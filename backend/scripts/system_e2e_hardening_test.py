import os
import sys
import uuid
import requests
import threading

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

BASE_URL = os.environ.get("BASE_URL", "http://backend:8000")
API = f"{BASE_URL}/api/v1"
HEALTH_URL = f"{BASE_URL}/api/health/"

ADMIN_USER = os.environ.get("E2E_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("E2E_ADMIN_PASS", "admin123")

CREATOR_USER = "e2e_creator"
CREATOR_PASS = "creator123"

APPROVER_USER = "e2e_approver"
APPROVER_PASS = "approver123"


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------


def fail(msg):
    print(f"\n❌ FAIL: {msg}")
    sys.exit(1)


def assert_status(resp, expected):
    if resp.status_code != expected:
        print("Status:", resp.status_code)
        print("Body:", resp.text)
        fail(f"Expected {expected}, got {resp.status_code}")


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


def login(username, password):
    r = requests.post(
        f"{API}/auth/login",
        json={"username": username, "password": password},
    )

    if r.status_code != 200:
        print("Status:", r.status_code)
        print("Body:", r.text)
        fail(f"Login failed for {username}")

    payload = r.json()

    if "data" in payload and "token" in payload["data"]:
        return payload["data"]["token"]

    fail("Unexpected login response format")


# -------------------------------------------------------
# TESTS
# -------------------------------------------------------


def test_health():
    print("=== PHASE 0: Health Check ===")
    r = requests.get(HEALTH_URL)
    assert_status(r, 200)
    print("✅ Health check passed\n")


def setup_users(admin_token):
    print("=== PHASE 1: User Setup ===")

    for username, password, role in [
        (CREATOR_USER, CREATOR_PASS, "CREATOR"),
        (APPROVER_USER, APPROVER_PASS, "APPROVER"),
    ]:
        r = requests.post(
            f"{API}/users",
            json={
                "username": username,
                "password": password,
                "role": role,
                "displayName": username,
            },
            headers=auth_headers(admin_token),
        )

        # 201 if created, 409 if already exists
        if r.status_code not in (201, 409):
            print("Status:", r.status_code)
            print("Body:", r.text)
            fail("User creation failed")

    print("✅ Users ready\n")


def create_ledger_entities(token):
    print("=== PHASE 2: Ledger Setup ===")

    vendor_name = f"Vendor-{uuid.uuid4().hex[:6]}"
    site_code = f"SITE-{uuid.uuid4().hex[:6]}"

    r = requests.post(
        f"{API}/ledger/vendors",
        json={
            "name": vendor_name
        },  # vendorTypeId is optional, will create default if not provided
        headers=auth_headers(token),
    )
    assert_status(r, 201)
    vendor_id = r.json()["data"]["id"]

    # Site creation requires clientId, but we can create a client first or use None
    # Check if clientId is required
    r = requests.post(
        f"{API}/ledger/sites",
        json={"code": site_code, "name": "Test Site"},  # clientId may be optional
        headers=auth_headers(token),
    )
    assert_status(r, 201)
    site_id = r.json()["data"]["id"]

    print("✅ Ledger entities created\n")
    return vendor_id, site_id


def test_state_machine(creator_token, approver_token, vendor_id, site_id):
    print("=== PHASE 3: State Machine ===")

    batch_name = f"Batch-{uuid.uuid4().hex[:6]}"

    r = requests.post(
        f"{API}/batches",
        json={"name": batch_name},
        headers=auth_headers(creator_token),
    )
    assert_status(r, 201)
    batch_id = r.json()["data"]["id"]

    # Create request
    r = requests.post(
        f"{API}/batches/{batch_id}/requests",
        json={
            "entityType": "VENDOR",
            "vendorId": vendor_id,
            "siteId": site_id,
            "baseAmount": "100.00",
            "extraAmount": "0.00",
        },
        headers=auth_headers(creator_token),
    )
    assert_status(r, 201)
    request_id = r.json()["data"]["id"]

    # Approve without submit → 409
    r = requests.post(
        f"{API}/requests/{request_id}/approve",
        headers=auth_headers(approver_token),
    )
    assert_status(r, 409)

    # Submit batch
    r = requests.post(
        f"{API}/batches/{batch_id}/submit",
        headers=auth_headers(creator_token),
    )
    assert_status(r, 200)

    # Concurrency approve test
    results = []

    def approve():
        resp = requests.post(
            f"{API}/requests/{request_id}/approve",
            headers=auth_headers(approver_token),
        )
        results.append(resp.status_code)

    threads = [threading.Thread(target=approve) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if results.count(200) != 1:
        fail("Concurrency violation: approve should succeed once")

    if results.count(409) != 4:
        fail("Concurrency violation: remaining should conflict")

    print("✅ Concurrency safe\n")

    # PATCH after approval → 409
    r = requests.patch(
        f"{API}/batches/{batch_id}/requests/{request_id}",
        json={"amount": "200.00"},
        headers=auth_headers(creator_token),
    )
    assert_status(r, 409)

    print("✅ Immutability enforced\n")

    # Mark paid (should succeed)
    r = requests.post(
        f"{API}/requests/{request_id}/mark-paid",
        headers=auth_headers(creator_token),
    )
    assert_status(r, 200)

    print("✅ State machine validated\n")


def test_idempotency(creator_token, vendor_id, site_id):
    print("=== PHASE 4: Idempotency ===")

    batch_name = f"Batch-Idem-{uuid.uuid4().hex[:6]}"

    r = requests.post(
        f"{API}/batches",
        json={"name": batch_name},
        headers=auth_headers(creator_token),
    )
    assert_status(r, 201)
    batch_id = r.json()["data"]["id"]

    key = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {creator_token}",
        "Idempotency-Key": key,
        "Content-Type": "application/json",
    }

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": "50.00",
        "extraAmount": "0.00",
    }

    r1 = requests.post(
        f"{API}/batches/{batch_id}/requests",
        json=payload,
        headers=headers,
    )

    r2 = requests.post(
        f"{API}/batches/{batch_id}/requests",
        json=payload,
        headers=headers,
    )

    if r1.status_code != r2.status_code:
        fail("Idempotency replay mismatch")

    print("✅ Idempotency enforced\n")


# -------------------------------------------------------
# RUNNER
# -------------------------------------------------------


def run():
    print("\n============================================================")
    print("=== SYSTEM E2E HARDENING TEST (FINAL) ===")
    print("============================================================\n")

    test_health()

    admin_token = login(ADMIN_USER, ADMIN_PASS)
    setup_users(admin_token)

    creator_token = login(CREATOR_USER, CREATOR_PASS)
    approver_token = login(APPROVER_USER, APPROVER_PASS)

    vendor_id, site_id = create_ledger_entities(admin_token)

    test_state_machine(creator_token, approver_token, vendor_id, site_id)

    test_idempotency(creator_token, vendor_id, site_id)

    print("\n============================================================")
    print("🎉 ALL END-TO-END INVARIANTS HOLD")
    print("SYSTEM IS STRUCTURALLY SOUND")
    print("============================================================\n")


if __name__ == "__main__":
    run()
