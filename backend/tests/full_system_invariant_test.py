"""
FULL SYSTEM INVARIANT TEST HARNESS
Production-grade financial invariant validation.

Run:
python backend/tests/full_system_invariant_test.py

Requirements:
- Backend running locally
- Admin, Creator, Approver tokens
"""

import requests
import uuid
import sys
import subprocess

BASE_URL = "http://127.0.0.1:8000/api/v1"


def check_server_connection():
    """Check if backend server is running."""
    try:
        r = requests.get(f"{BASE_URL.replace('/api/v1', '')}/api/health/", timeout=2)
        if r.status_code == 200:
            print("✅ Backend server is running")
            return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("\n❌ ERROR: Backend server is not running!")
        print("   Please start the server: python manage.py runserver")
        base = BASE_URL.replace("/api/v1", "")
        print(f"   Expected URL: {base}/api/health/")
        return False
    return False


ADMIN_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxNTA4Mjg4LCJpYXQiOjE3NzE0MjE4ODgs"
    "Imp0aSI6Ijg5ODRmOTdlNWZmMDRkYjFiNWMyMjNhZjZmZmI5YTZiIiwidXNlcl9pZCI6ImU0M2U1"
    "NDA1LWU5ZTAtNDE1MS1iMWM1LTBkMDJiMjdiYjAxNyJ9."
    "XOb437URyQNHo2BRqAb8xiuCQYU0WScZbFYLn5q2-Bc"
)
CREATOR_TOKEN = "NEW_TOKEN_HERE"
APPROVER_TOKEN = "NEW_TOKEN_HERE"

HEADERS_ADMIN = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json",
}

HEADERS_CREATOR = {
    "Authorization": f"Bearer {CREATOR_TOKEN}",
    "Content-Type": "application/json",
}

HEADERS_APPROVER = {
    "Authorization": f"Bearer {APPROVER_TOKEN}",
    "Content-Type": "application/json",
}


# -----------------------------
# Helper
# -----------------------------


def assert_true(condition, message):
    if not condition:
        print(f"\n❌ FAIL: {message}")
        sys.exit(1)
    else:
        print(f"✅ PASS: {message}")


# -----------------------------
# Ledger tests
# -----------------------------


def create_vendor():
    print("\nTEST 1 — Ledger Vendor Creation")

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {"name": f"TestVendor-{uuid.uuid4().hex[:6]}", "isActive": True}

    r = requests.post(
        f"{BASE_URL}/ledger/vendors",
        headers=headers,
        json=payload,
    )

    print("Status Code:", r.status_code)
    print("Response:", r.text)

    assert_true(r.status_code in [200, 201], f"Vendor creation failed: {r.status_code}")

    data = r.json()

    vendor = data.get("data", data)

    return vendor


def create_site():
    print("\nTEST 2 — Ledger Site Creation")

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "code": f"SITE-{uuid.uuid4().hex[:4]}",
        "name": "Test Site",
        "clientId": None,
        "isActive": True,
    }

    r = requests.post(
        f"{BASE_URL}/ledger/sites",
        headers=headers,
        json=payload,
    )

    print("Status Code:", r.status_code)
    print("Response:", r.text)

    assert_true(r.status_code in [200, 201], "Site created")

    response_data = r.json()
    site = response_data.get("data", response_data)

    # CRITICAL: validate required fields exist
    assert_true("id" in site, "Site has id")
    assert_true("code" in site, "Site has code")
    assert_true("name" in site, "Site has name")

    print("✅ PASS: Site creation successful")

    return site


# -----------------------------
# Batch
# -----------------------------


def create_batch():
    print("\nTEST 3 — Batch Creation")

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "name": f"Batch-{uuid.uuid4().hex[:6]}",
        "currency": "INR",
    }

    r = requests.post(
        f"{BASE_URL}/batches",
        headers=headers,
        json=payload,
    )

    print("Status Code:", r.status_code)
    print("Response:", r.text)

    assert_true(r.status_code in [200, 201], "Batch created")

    response_data = r.json()
    batch = response_data.get(
        "data", response_data
    )  # Handle both wrapped and unwrapped responses
    return batch


# -----------------------------
# Payment creation
# -----------------------------


def create_payment_request(batch_id, vendor_id, site_id):

    print("\nTEST 4 — PaymentRequest Creation")

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 1000,
        "extraAmount": 200,
        "extraReason": "Transport",
        "currency": "INR",
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    print("Status Code:", r.status_code)
    print("Response:", r.text)

    assert_true(r.status_code in [200, 201], "PaymentRequest created")

    response_data = r.json()
    data = response_data.get(
        "data", response_data
    )  # Handle both wrapped and unwrapped responses

    # totalAmount is serialized as string, compare accordingly
    total = (
        float(data["totalAmount"])
        if isinstance(data["totalAmount"], str)
        else data["totalAmount"]
    )
    assert_true(
        total == 1200,
        "Server computed total correctly",
    )

    assert_true(
        data.get("vendorSnapshotName") is not None,
        "Vendor snapshot populated",
    )

    assert_true(
        data.get("siteSnapshotCode") is not None,
        "Site snapshot populated",
    )

    # Version is an integer
    version = data.get("version")
    assert_true(
        version == 1,
        f"Version initialized (got {version})",
    )

    return data


# -----------------------------
# Idempotency tests
# -----------------------------


def test_idempotency(batch_id, vendor_id, site_id):

    print("\nTEST 5 — Idempotency Protection")

    key = str(uuid.uuid4())

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = key

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 500,
        "extraAmount": 0,
        "currency": "INR",
    }

    r1 = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    r2 = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    assert_true(
        r1.status_code in [200, 201],
        f"First idempotent request succeeded (got {r1.status_code})",
    )
    assert_true(
        r2.status_code in [200, 201],
        f"Second idempotent request succeeded (got {r2.status_code})",
    )
    r1_data = r1.json().get("data", r1.json())
    r2_data = r2.json().get("data", r2.json())
    assert_true(
        r1_data["id"] == r2_data["id"],
        "Duplicate prevented",
    )


def test_missing_idempotency(batch_id, vendor_id, site_id):

    print("\nTEST 6 — Missing Idempotency Key Rejection")

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 100,
        "extraAmount": 0,
        "currency": "INR",
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=HEADERS_ADMIN,
        json=payload,
    )

    assert_true(
        r.status_code == 400,
        "Rejected without idempotency key",
    )


# -----------------------------
# Version locking
# -----------------------------


def submit_batch(batch_id):
    """Submit batch to transition requests to PENDING_APPROVAL."""
    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())
    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/submit",
        headers=headers,
    )
    assert_true(
        r.status_code in [200, 201],
        f"Batch submit succeeded (got {r.status_code})",
    )


def approve_request(request_id):

    print("\nTEST 7 — Version Locking")

    headers1 = HEADERS_ADMIN.copy()
    headers1["Idempotency-Key"] = str(uuid.uuid4())
    r1 = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve",
        headers=headers1,
    )
    assert_true(r1.status_code == 200, "First approval succeeds")

    # Second approval with different idempotency key should be blocked
    headers2 = HEADERS_ADMIN.copy()
    headers2["Idempotency-Key"] = str(uuid.uuid4())
    r2 = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve",
        headers=headers2,
    )
    assert_true(
        r2.status_code != 200,
        f"Second approval blocked (got {r2.status_code})",
    )


# -----------------------------
# Snapshot integrity
# -----------------------------


def test_snapshot_integrity(vendor_id, request_id):

    print("\nTEST 8 — Snapshot Integrity")

    requests.patch(
        f"{BASE_URL}/ledger/vendors/{vendor_id}",
        headers=HEADERS_ADMIN,
        json={"isActive": False},
    )

    r = requests.get(
        f"{BASE_URL}/requests/{request_id}",
        headers=HEADERS_ADMIN,
    )

    response_data = r.json()
    data = response_data.get("data", response_data)

    assert_true(
        data["vendorSnapshotName"] is not None,
        "Snapshot preserved",
    )


# -----------------------------
# Immutability
# -----------------------------


def test_immutability(request_id):

    print("\nTEST 9 — Financial Immutability")

    r = requests.patch(
        f"{BASE_URL}/requests/{request_id}",
        headers=HEADERS_ADMIN,
        json={"baseAmount": 9999},
    )

    assert_true(
        r.status_code != 200,
        "Modification blocked",
    )


# -----------------------------
# total tamper protection
# -----------------------------


def test_total_tamper(batch_id, vendor_id, site_id):

    print("\nTEST 10 — totalAmount tamper protection")

    headers = HEADERS_ADMIN.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 100,
        "extraAmount": 100,
        "extraReason": "Test",
        "totalAmount": 1,  # Tampered - server should ignore and compute 200
        "currency": "INR",
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    assert_true(
        r.status_code in [200, 201],
        f"Tamper test request succeeded (got {r.status_code})",
    )
    response_data = r.json()
    data = response_data.get("data", response_data)
    total_val = data.get("totalAmount") or data.get("total_amount")
    total = float(total_val) if isinstance(total_val, str) else (total_val or 0)
    assert_true(
        total == 200,
        "Server ignored tampered total",
    )


# -----------------------------
# Audit log
# -----------------------------


def test_audit_log():

    print("\nTEST 11 — Audit Logs")

    r = requests.get(
        f"{BASE_URL}/audit/logs",
        headers=HEADERS_ADMIN,
    )

    response_data = r.json()
    # Audit logs endpoint returns paginated response with "results" or direct array
    audit_data = response_data.get("results", response_data.get("data", response_data))

    assert_true(
        len(audit_data) > 0,
        "Audit logs exist",
    )


# -----------------------------
# Reconciliation
# -----------------------------


def test_reconciliation():

    print("\nTEST 12 — Reconciliation Command")

    import os

    # Run inside Docker if available (has DB connection), else try local
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            os.path.join(project_root, "docker-compose.yml"),
            "exec",
            "-T",
            "backend",
            "python",
            "manage.py",
            "reconcile_payments",
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=30,
    )
    if result.returncode != 0 and "no such container" in (result.stderr or "").lower():
        # Fallback: try local (e.g. for CI without Docker)
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        result = subprocess.run(
            [sys.executable, "manage.py", "reconcile_payments"],
            capture_output=True,
            text=True,
            cwd=os.path.abspath(backend_dir),
            timeout=30,
        )

    stderr_preview = (result.stderr or "")[:200]
    msg = (
        "Reconciliation successful "
        f"(got {result.returncode}, stderr: {stderr_preview})"
    )
    assert_true(result.returncode == 0, msg)


# -----------------------------
# MAIN
# -----------------------------


def main():

    print("\nSTARTING FULL INVARIANT TEST SUITE\n")

    # Check server connection first
    if not check_server_connection():
        sys.exit(1)

    vendor = create_vendor()
    site = create_site()
    batch = create_batch()

    request = create_payment_request(
        batch["id"],
        vendor["id"],
        site["id"],
    )

    test_idempotency(batch["id"], vendor["id"], site["id"])
    test_missing_idempotency(batch["id"], vendor["id"], site["id"])

    test_total_tamper(batch["id"], vendor["id"], site["id"])

    submit_batch(batch["id"])
    approve_request(request["id"])

    test_snapshot_integrity(vendor["id"], request["id"])
    test_immutability(request["id"])

    test_audit_log()
    test_reconciliation()

    print("\nALL TESTS PASSED — SYSTEM SAFE\n")


if __name__ == "__main__":
    main()
