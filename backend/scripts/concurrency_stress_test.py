"""
CRITICAL WARNING:
Do NOT run against production database.
These scripts intentionally trigger conflict scenarios.
Use only in local or CI test environments.
"""

import sys
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "http://127.0.0.1:8000/api/v1"
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
    r = requests.post(LOGIN_URL, json={"username": "admin", "password": "admin123"})
    data = safe_json(r, "LOGIN")
    if not data or "data" not in data or "token" not in data["data"]:
        print("LOGIN failed:", getattr(r, "status_code", None), data)
        sys.exit(1)
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
    print("=== Concurrency stress test (10 parallel approves, expect 1x200, 9x409) ===")
    token = login()

    r = requests.post(
        f"{BASE}/ledger/vendors",
        headers=headers(token, str(uuid.uuid4())),
        json={"name": f"StressVendor-{uuid.uuid4().hex[:8]}", "isActive": True},
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
            "code": f"S-{uuid.uuid4().hex[:4]}",
            "name": "Stress Site",
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
        json={"title": "StressBatch"},
    )
    j = safe_json(r, "BATCH")
    if r.status_code >= 400 or not j or "data" not in j:
        print("CREATE BATCH failed:", r.status_code, j)
        sys.exit(1)
    batch = j["data"]

    r = requests.post(
        f"{BASE}/batches/{batch['id']}/requests",
        headers=headers(token, str(uuid.uuid4())),
        json={
            "entityType": "VENDOR",
            "vendorId": vendor["id"],
            "siteId": site["id"],
            "baseAmount": "1000.00",
            "extraAmount": "0",
            "currency": "INR",
        },
    )
    j = safe_json(r, "REQUEST")
    if r.status_code >= 400 or not j or "data" not in j:
        print("CREATE REQUEST failed:", r.status_code, j)
        sys.exit(1)
    req = j["data"]

    r = requests.post(
        f"{BASE}/batches/{batch['id']}/submit",
        headers=headers(token, str(uuid.uuid4())),
    )
    j = safe_json(r, "SUBMIT")
    if r.status_code >= 400 or not j:
        print("SUBMIT BATCH failed:", r.status_code, j)
        sys.exit(1)

    request_id = req["id"]

    def approve_once(_):
        resp = requests.post(
            f"{BASE}/requests/{request_id}/approve",
            headers=headers(token, str(uuid.uuid4())),
        )
        return resp.status_code

    codes = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(approve_once, i) for i in range(10)]
        for f in as_completed(futures):
            codes.append(f.result())

    ok = sum(1 for c in codes if c == 200)
    conflict = sum(1 for c in codes if c == 409)
    if ok != 1 or conflict != 9:
        print(f"INVARIANT BROKEN: expected 1x200, 9x409; got {ok}x200, {conflict}x409")
        print("Status codes:", sorted(codes))
        sys.exit(1)
    print("OK: 1x200, 9x409 as expected.")


if __name__ == "__main__":
    run()
