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
import time

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
        print(f"   Please start the server: python manage.py runserver")
        print(f"   Expected URL: {BASE_URL.replace('/api/v1', '')}/api/health/")
        return False
    return False

ADMIN_TOKEN = "REPLACE_ADMIN_TOKEN"
CREATOR_TOKEN = "REPLACE_CREATOR_TOKEN"
APPROVER_TOKEN = "REPLACE_APPROVER_TOKEN"

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

    payload = {
        "name": f"TestVendor-{uuid.uuid4().hex[:6]}",
        "isActive": True,
    }

    try:
        r = requests.post(
            f"{BASE_URL}/ledger/vendors",
            headers=HEADERS_ADMIN,
            json=payload,
            timeout=5,
        )
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print(f"   URL attempted: {BASE_URL}/ledger/vendors")
        print("   Make sure backend server is running and ledger URLs are configured")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

    print("Status Code:", r.status_code)
    print("Response:", r.text)

    assert_true(
        r.status_code in [200, 201],
        f"Vendor creation failed: {r.status_code}"
    )

    vendor = r.json()

    print("Created Vendor ID:", vendor.get("id"))

    return vendor


def create_site():
    print("\nTEST 2 — Ledger Site Creation")

    payload = {
        "code": f"SITE-{uuid.uuid4().hex[:4]}",
        "name": "Test Site",
        "isActive": True,
    }

    r = requests.post(
        f"{BASE_URL}/ledger/sites",
        headers=HEADERS_ADMIN,
        json=payload,
    )

    assert_true(r.status_code in [200, 201], "Site created")

    return r.json()


# -----------------------------
# Batch
# -----------------------------

def create_batch():
    print("\nTEST 3 — Batch Creation")

    payload = {
        "name": f"Batch-{uuid.uuid4().hex[:6]}",
        "currency": "INR",
    }

    r = requests.post(
        f"{BASE_URL}/batches",
        headers=HEADERS_CREATOR,
        json=payload,
    )

    assert_true(r.status_code in [200, 201], "Batch created")

    return r.json()


# -----------------------------
# Payment creation
# -----------------------------

def create_payment_request(batch_id, vendor_id, site_id):

    print("\nTEST 4 — PaymentRequest Creation")

    headers = HEADERS_CREATOR.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 1000,
        "extraAmount": 200,
        "extraReason": "Transport",
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    assert_true(r.status_code in [200, 201], "PaymentRequest created")

    data = r.json()

    assert_true(
        data["totalAmount"] == 1200,
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

    assert_true(
        data.get("version") == 1,
        "Version initialized",
    )

    return data


# -----------------------------
# Idempotency tests
# -----------------------------

def test_idempotency(batch_id, vendor_id, site_id):

    print("\nTEST 5 — Idempotency Protection")

    key = str(uuid.uuid4())

    headers = HEADERS_CREATOR.copy()
    headers["Idempotency-Key"] = key

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 500,
        "extraAmount": 0,
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
        r1.json()["id"] == r2.json()["id"],
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
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=HEADERS_CREATOR,
        json=payload,
    )

    assert_true(
        r.status_code == 400,
        "Rejected without idempotency key",
    )


# -----------------------------
# Version locking
# -----------------------------

def approve_request(request_id):

    print("\nTEST 7 — Version Locking")

    headers = HEADERS_APPROVER.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    r1 = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve",
        headers=headers,
    )

    assert_true(r1.status_code == 200, "First approval succeeds")

    r2 = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve",
        headers=headers,
    )

    assert_true(
        r2.status_code != 200,
        "Second approval blocked",
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
        headers=HEADERS_CREATOR,
    )

    assert_true(
        r.json()["vendorSnapshotName"] is not None,
        "Snapshot preserved",
    )


# -----------------------------
# Immutability
# -----------------------------

def test_immutability(request_id):

    print("\nTEST 9 — Financial Immutability")

    r = requests.patch(
        f"{BASE_URL}/requests/{request_id}",
        headers=HEADERS_CREATOR,
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

    headers = HEADERS_CREATOR.copy()
    headers["Idempotency-Key"] = str(uuid.uuid4())

    payload = {
        "entityType": "VENDOR",
        "vendorId": vendor_id,
        "siteId": site_id,
        "baseAmount": 100,
        "extraAmount": 100,
        "totalAmount": 1,
    }

    r = requests.post(
        f"{BASE_URL}/batches/{batch_id}/requests",
        headers=headers,
        json=payload,
    )

    assert_true(
        r.json()["totalAmount"] == 200,
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

    assert_true(
        len(r.json()) > 0,
        "Audit logs exist",
    )


# -----------------------------
# Reconciliation
# -----------------------------

def test_reconciliation():

    print("\nTEST 12 — Reconciliation Command")

    result = subprocess.run(
        ["python", "manage.py", "reconcile_payments"],
        capture_output=True,
        text=True,
    )

    assert_true(
        result.returncode == 0,
        "Reconciliation successful",
    )


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

    approve_request(request["id"])

    test_snapshot_integrity(vendor["id"], request["id"])
    test_immutability(request["id"])

    test_total_tamper(batch["id"], vendor["id"], site["id"])

    test_audit_log()
    test_reconciliation()

    print("\nALL TESTS PASSED — SYSTEM SAFE\n")


if __name__ == "__main__":
    main()
