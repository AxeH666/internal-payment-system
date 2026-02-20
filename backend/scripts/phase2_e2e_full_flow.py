#!/usr/bin/env python3
"""
FULL END-TO-END VALIDATION SCRIPT — Phase 2

Runs a complete flow: ADMIN creates CREATOR/APPROVER, CREATOR creates batch + request,
submit → APPROVER approves → ADMIN marks paid. Validates final state is PAID.

Requires: backend running (e.g. python manage.py runserver), admin user exists
  (e.g. created via shell:
  User.objects.create_superuser(username="admin", password="admin123")).
Usage: BASE_URL=http://localhost:8000 python backend/scripts/phase2_e2e_full_flow.py
"""

import os
import requests
import uuid
import sys

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"


def log(msg):
    print(f"\n=== {msg} ===")


def assert_status(resp, expected):
    if resp.status_code != expected:
        print("FAILED:", resp.status_code, resp.text)
        sys.exit(1)


def idempotency():
    return {"Idempotency-Key": str(uuid.uuid4())}


# -----------------------------
# STEP 0 — LOGIN AS ADMIN
# -----------------------------
log("Login as ADMIN")

admin_login = requests.post(
    f"{API}/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10,
)
assert_status(admin_login, 200)
data = admin_login.json()
token = data.get("data", data).get("token") or data.get("access")
if not token:
    print("FAILED: No token in login response:", data)
    sys.exit(1)
admin_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# -----------------------------
# STEP 1 — CREATE CREATOR
# -----------------------------
log("Create CREATOR user")

creator_resp = requests.post(
    f"{API}/users/",
    headers={**admin_headers, **idempotency()},
    json={
        "username": "creator1",
        "password": "creator123",
        "display_name": "Creator One",
        "role": "CREATOR",
    },
    timeout=10,
)
assert_status(creator_resp, 201)

# -----------------------------
# STEP 2 — CREATE APPROVER
# -----------------------------
log("Create APPROVER user")

approver_resp = requests.post(
    f"{API}/users/",
    headers={**admin_headers, **idempotency()},
    json={
        "username": "approver1",
        "password": "approver123",
        "display_name": "Approver One",
        "role": "APPROVER",
    },
    timeout=10,
)
assert_status(approver_resp, 201)

# -----------------------------
# STEP 3 — LOGIN AS CREATOR
# -----------------------------
log("Login as CREATOR")

creator_login = requests.post(
    f"{API}/auth/login",
    json={"username": "creator1", "password": "creator123"},
    timeout=10,
)
assert_status(creator_login, 200)
data = creator_login.json()
token = data.get("data", data).get("token") or data.get("access")
if not token:
    print("FAILED: No token in creator login response:", data)
    sys.exit(1)
creator_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    **idempotency(),
}

# -----------------------------
# STEP 4 — CREATE BATCH
# -----------------------------
log("Create batch")

batch_resp = requests.post(
    f"{API}/batches",
    headers=creator_headers,
    json={"title": "E2E Batch"},
    timeout=10,
)
assert_status(batch_resp, 201)
batch_data = batch_resp.json().get("data", batch_resp.json())
batch_id = batch_data.get("id")

# -----------------------------
# STEP 5 — ADD REQUEST (legacy payload)
# -----------------------------
log("Add payment request")

request_resp = requests.post(
    f"{API}/batches/{batch_id}/requests",
    headers={**creator_headers, **idempotency()},
    json={
        "amount": "1000.00",
        "currency": "USD",
        "beneficiaryName": "Test Payee",
        "beneficiaryAccount": "ACC123",
        "purpose": "E2E test payment",
    },
    timeout=10,
)
assert_status(request_resp, 201)
request_data = request_resp.json().get("data", request_resp.json())
request_id = request_data.get("id")

# -----------------------------
# STEP 6 — SUBMIT BATCH
# -----------------------------
log("Submit batch")

submit_resp = requests.post(
    f"{API}/batches/{batch_id}/submit",
    headers={**creator_headers, **idempotency()},
    timeout=10,
)
assert_status(submit_resp, 200)

# -----------------------------
# STEP 7 — LOGIN AS APPROVER
# -----------------------------
log("Login as APPROVER")

approver_login = requests.post(
    f"{API}/auth/login",
    json={"username": "approver1", "password": "approver123"},
    timeout=10,
)
assert_status(approver_login, 200)
data = approver_login.json()
token = data.get("data", data).get("token") or data.get("access")
if not token:
    print("FAILED: No token in approver login response:", data)
    sys.exit(1)
approver_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    **idempotency(),
}

# -----------------------------
# STEP 8 — APPROVE REQUEST
# -----------------------------
log("Approve payment request")

approve_resp = requests.post(
    f"{API}/requests/{request_id}/approve",
    headers={**approver_headers, **idempotency()},
    json={},
    timeout=10,
)
assert_status(approve_resp, 200)

# -----------------------------
# STEP 9 — MARK PAID (ADMIN TEST)
# -----------------------------
log("Mark paid as ADMIN")

mark_paid_resp = requests.post(
    f"{API}/requests/{request_id}/mark-paid",
    headers={**admin_headers, **idempotency()},
    timeout=10,
)
assert_status(mark_paid_resp, 200)

# -----------------------------
# FINAL VALIDATION
# -----------------------------
log("Fetch final request state")

final_resp = requests.get(
    f"{API}/batches/{batch_id}/requests/{request_id}",
    headers=admin_headers,
    timeout=10,
)
assert_status(final_resp, 200)

final_data = final_resp.json().get("data", final_resp.json())
status = final_data.get("status")

if status != "PAID":
    print("FAILED: Final state not PAID, got:", status)
    sys.exit(1)

log("PHASE 2 E2E VALIDATION PASSED")
