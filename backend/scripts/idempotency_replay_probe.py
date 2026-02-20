"""
CRITICAL WARNING:
Do NOT run against production database.
These scripts intentionally trigger conflict scenarios.
Use only in local or CI test environments.
"""

import sys
import os
import uuid
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("E2E_USERNAME", "admin")
PASSWORD = os.getenv("E2E_PASSWORD", "admin")

BASE = f"{BASE_URL}/api/v1"
LOGIN_URL = f"{BASE}/auth/login"


def safe_json(resp, label):
    if "application/json" not in resp.headers.get("Content-Type", ""):
        print(f"[{label}] Non-JSON: {resp.text[:200]}")
        return None
    try:
        return resp.json()
    except Exception:
        return None


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


def run():
    print("=== Idempotency replay probe ===")
    token = login()

    r = requests.post(
        f"{BASE}/ledger/vendors",
        headers=headers(token, str(uuid.uuid4())),
        json={"name": f"IdemVendor-{uuid.uuid4().hex[:8]}", "isActive": True},
    )
    j = safe_json(r, "VENDOR")
    if r.status_code >= 400 or not j or "data" not in j:
        print("CREATE VENDOR failed:", r.status_code, j)
        sys.exit(1)
    vendor = j["data"]

    r = requests.post(
        f"{BASE}/ledger/sites",
        headers=headers(token, str(uuid.uuid4())),
        json={
            "code": f"I-{uuid.uuid4().hex[:4]}",
            "name": "Idem Site",
            "isActive": True,
        },
    )
    j = safe_json(r, "SITE")
    if r.status_code >= 400 or not j or "data" not in j:
        print("CREATE SITE failed:", r.status_code, j)
        sys.exit(1)
    site = j["data"]

    r = requests.post(
        f"{BASE}/batches",
        headers=headers(token, str(uuid.uuid4())),
        json={"title": "IdemBatch"},
    )
    j = safe_json(r, "BATCH")
    if r.status_code >= 400 or not j or "data" not in j:
        print("CREATE BATCH failed:", r.status_code, j)
        sys.exit(1)
    batch = j["data"]
    batch_id = batch["id"]

    same_key = str(uuid.uuid4())
    body_a = {
        "entityType": "VENDOR",
        "vendorId": vendor["id"],
        "siteId": site["id"],
        "baseAmount": "100.00",
        "extraAmount": "0",
        "currency": "INR",
    }
    body_b = {
        "entityType": "VENDOR",
        "vendorId": vendor["id"],
        "siteId": site["id"],
        "baseAmount": "200.00",
        "extraAmount": "0",
        "currency": "INR",
    }

    r1 = requests.post(
        f"{BASE}/batches/{batch_id}/requests",
        headers=headers(token, same_key),
        json=body_a,
    )
    j1 = safe_json(r1, "REQUEST_1")
    if r1.status_code not in (200, 201) or not j1 or "data" not in j1:
        print("First create request failed:", r1.status_code, j1)
        sys.exit(1)
    id1 = j1["data"].get("id")

    r2 = requests.post(
        f"{BASE}/batches/{batch_id}/requests",
        headers=headers(token, same_key),
        json=body_a,
    )
    j2 = safe_json(r2, "REQUEST_2_REPLAY")
    if r2.status_code not in (200, 201):
        print("Same key + same body should return success:", r2.status_code, j2)
        sys.exit(1)
    id2 = j2["data"].get("id") if j2 and "data" in j2 else None
    if id1 != id2:
        print("Same key + same body must return same response/record:", id1, id2)
        sys.exit(1)
    print("OK: Same Idempotency-Key + same body → same response")

    r3 = requests.post(
        f"{BASE}/batches/{batch_id}/requests",
        headers=headers(token, same_key),
        json=body_b,
    )
    if r3.status_code != 409:
        print("Same key + different body must return 409:", r3.status_code)
        sys.exit(1)
    print("OK: Same Idempotency-Key + different body → 409")

    r4 = requests.post(
        f"{BASE}/batches/{batch_id}/requests",
        headers=headers(token, str(uuid.uuid4())),
        json=body_a,
    )
    j4 = safe_json(r4, "REQUEST_4_NEW_KEY")
    if r4.status_code not in (200, 201) or not j4 or "data" not in j4:
        print("Different key + same body should create new record:", r4.status_code, j4)
        sys.exit(1)
    id4 = j4["data"].get("id")
    if id4 == id1:
        print("Different key + same body must create new record (different id)")
        sys.exit(1)
    print("OK: Different Idempotency-Key + same body → new record")

    print("All idempotency invariants held.")


if __name__ == "__main__":
    run()
