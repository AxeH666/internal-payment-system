import sys
import os
import uuid
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("E2E_USERNAME", "admin")
PASSWORD = os.getenv("E2E_PASSWORD", "admin")

BASE = f"{BASE_URL}/api/v1"
LOGIN = f"{BASE}/auth/login"


def safe_json(resp, label):
    print(f"\n[{label}] STATUS: {resp.status_code}")
    if "application/json" not in resp.headers.get("Content-Type", ""):
        print("❌ Non-JSON response:")
        print(resp.text)
        sys.exit(1)

    try:
        return resp.json()
    except Exception as e:
        print("❌ JSON parse failed:", e)
        print(resp.text)
        sys.exit(1)


def login():
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=5,
    )

    if r.status_code != 200:
        raise RuntimeError(f"[LOGIN FAILED] Status={r.status_code} Body={r.text}")

    try:
        data = r.json()
    except Exception as e:
        raise RuntimeError(f"[LOGIN FAILED] Invalid JSON response: {r.text}") from e

    if not isinstance(data, dict):
        raise RuntimeError(f"[LOGIN FAILED] Unexpected response type: {type(data)}")

    if "data" not in data or "token" not in data["data"]:
        raise RuntimeError(f"[LOGIN FAILED] Unexpected login response format: {data}")

    return data["data"]["token"]


def headers(token, idem=None):
    h = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if idem:
        h["Idempotency-Key"] = idem
    return h


def fail_if(cond, msg):
    if cond:
        print(f"\n❌ INVARIANT BROKEN: {msg}")
        sys.exit(1)
    else:
        print(f"✅ SAFE: {msg}")


def run():
    print("\n=== DEEP INVARIANT PROBE START ===")

    token = login()

    # Vendor (unique name per run to avoid unique constraint)
    r = requests.post(
        f"{BASE}/ledger/vendors",
        headers=headers(token, str(uuid.uuid4())),
        json={"name": f"ProbeVendor-{uuid.uuid4().hex[:8]}", "isActive": True},
    )
    j = safe_json(r, "CREATE VENDOR")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ CREATE VENDOR failed:", err.get("message"), err.get("details"))
        sys.exit(1)
    vendor = j["data"]

    # Site
    r = requests.post(
        f"{BASE}/ledger/sites",
        headers=headers(token, str(uuid.uuid4())),
        json={
            "code": f"P-{uuid.uuid4().hex[:4]}",
            "name": "Probe Site",
            "isActive": True,
        },
    )
    j = safe_json(r, "CREATE SITE")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ CREATE SITE failed:", err.get("message"), err.get("details"))
        sys.exit(1)
    site = j["data"]

    # Batch
    r = requests.post(
        f"{BASE}/batches",
        headers=headers(token, str(uuid.uuid4())),
        json={"title": "ProbeBatch"},
    )
    j = safe_json(r, "CREATE BATCH")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ CREATE BATCH failed:", err.get("message"), err.get("details"))
        sys.exit(1)
    batch = j["data"]

    # Request
    r = requests.post(
        f"{BASE}/batches/{batch['id']}/requests",
        headers=headers(token, str(uuid.uuid4())),
        json={
            "entityType": "VENDOR",
            "vendorId": vendor["id"],
            "siteId": site["id"],
            "baseAmount": "1000.00",
            "extraAmount": "500.00",
            "extraReason": "Probe",
            "currency": "INR",
        },
    )
    j = safe_json(r, "CREATE REQUEST")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ CREATE REQUEST failed:", err.get("message"), err.get("details"))
        sys.exit(1)
    req = j["data"]

    print("\n--- Attempt: Approve without submit ---")

    r = requests.post(
        f"{BASE}/requests/{req['id']}/approve",
        headers=headers(token, str(uuid.uuid4())),
    )
    safe_json(r, "APPROVE_WITHOUT_SUBMIT")
    fail_if(r.status_code == 200, "Approved without submit")

    print("\n--- Submit batch ---")

    r = requests.post(
        f"{BASE}/batches/{batch['id']}/submit",
        headers=headers(token, str(uuid.uuid4())),
    )
    safe_json(r, "SUBMIT BATCH")

    print("\n--- Approve correctly ---")

    r = requests.post(
        f"{BASE}/requests/{req['id']}/approve",
        headers=headers(token, str(uuid.uuid4())),
    )
    j = safe_json(r, "APPROVE")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ APPROVE failed:", err.get("message"), err.get("details"))
        sys.exit(1)

    print("\n--- Mark paid (full flow: create → submit → approve → mark_paid) ---")

    r = requests.post(
        f"{BASE}/requests/{req['id']}/mark-paid",
        headers=headers(token, str(uuid.uuid4())),
    )
    j = safe_json(r, "MARK_PAID")
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        print("❌ MARK_PAID failed:", err.get("message"), err.get("details"))
        sys.exit(1)

    print("\n--- Attempt modify after approval ---")

    r = requests.patch(
        f"{BASE}/batches/{batch['id']}/requests/{req['id']}",
        headers=headers(token, str(uuid.uuid4())),
        json={"baseAmount": "999999.00"},
    )
    safe_json(r, "PATCH_AFTER_APPROVE")
    fail_if(r.status_code in [200, 204], "Modified approved request")

    print("\n=== ALL CORE INVARIANTS HOLD ===")
    print("SYSTEM IS STRUCTURALLY SOUND\n")


if __name__ == "__main__":
    run()
