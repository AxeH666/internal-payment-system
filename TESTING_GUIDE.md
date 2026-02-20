# Testing Guide for E2E Hardening Test Fixes

This guide provides exact commands to test the fixes for the `approve_request` concurrency issues.

## Prerequisites

1. Backend service must be running and accessible
2. Database must be initialized with migrations
3. Test users must exist (or be created by the test)

## Fix Summary

The following issues were fixed:

1. **Added ApprovalRecord existence check** in `approve_request` before creating
2. **Added IntegrityError handling** for race conditions
3. **Improved reject_request** to use consistent pattern with `exists()` check
4. **Ensured idempotency** - if ApprovalRecord exists, return success immediately

## Test Commands (Run One After Another)

### Step 1: Verify Backend is Running

```bash
# Check if backend service is accessible
curl -f http://localhost:8000/api/health/ || echo "Backend not running - start it first"
```

**Expected**: HTTP 200 response with health check data

**If backend is not running**, start it:
```bash
# From project root
cd backend
python manage.py runserver 0.0.0.0:8000
# Or if using Docker:
docker-compose up backend
```

---

### Step 2: Set Environment Variables

```bash
# Set BASE_URL (adjust if your backend runs on different host/port)
export BASE_URL="http://localhost:8000"

# Set admin credentials (adjust if different)
export E2E_ADMIN_USER="admin"
export E2E_ADMIN_PASS="admin123"
```

---

### Step 3: Run the Full E2E Test

```bash
# Navigate to project root
cd /home/axehe/internal-payment-system

# Run the test script
python3 backend/scripts/system_e2e_hardening_test.py
```

**Expected Output**:
```
============================================================
=== SYSTEM E2E HARDENING TEST (FINAL) ===
============================================================

=== PHASE 0: Health Check ===
✅ Health check passed

=== PHASE 1: User Setup ===
✅ Users ready

=== PHASE 2: Ledger Setup ===
✅ Ledger entities created

=== PHASE 3: State Machine ===
✅ Concurrency safe
✅ Immutability enforced
✅ State machine validated

=== PHASE 4: Idempotency ===
✅ Idempotency enforced

============================================================
🎉 ALL END-TO-END INVARIANTS HOLD
SYSTEM IS STRUCTURALLY SOUND
============================================================
```

**If test fails**, check the error message and proceed to Step 4 for detailed debugging.

---

### Step 4: Test Concurrency Fix Specifically

Create a test script to verify the concurrency fix:

```bash
# Create a test script
cat > /tmp/test_concurrency_fix.py << 'EOF'
import os
import uuid
import requests
import threading
import time

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"

ADMIN_USER = os.environ.get("E2E_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("E2E_ADMIN_PASS", "admin123")
CREATOR_USER = "e2e_creator"
CREATOR_PASS = "creator123"
APPROVER_USER = "e2e_approver"
APPROVER_PASS = "approver123"

def login(username, password):
    r = requests.post(f"{API}/auth/login", json={"username": username, "password": password})
    if r.status_code != 200:
        raise Exception(f"Login failed: {r.status_code} - {r.text}")
    return r.json()["data"]["token"]

def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

print("=== Testing Concurrency Fix ===")

# Login
admin_token = login(ADMIN_USER, ADMIN_PASS)
creator_token = login(CREATOR_USER, CREATOR_PASS)
approver_token = login(APPROVER_USER, APPROVER_PASS)

# Create batch
batch_name = f"ConcurrencyTest-{uuid.uuid4().hex[:6]}"
r = requests.post(f"{API}/batches", json={"name": batch_name}, headers=auth_headers(creator_token))
assert r.status_code == 201, f"Batch creation failed: {r.status_code}"
batch_id = r.json()["data"]["id"]

# Create vendor and site (simplified - adjust if needed)
vendor_r = requests.post(f"{API}/ledger/vendors", json={"name": f"Vendor-{uuid.uuid4().hex[:6]}"}, headers=auth_headers(admin_token))
vendor_id = vendor_r.json()["data"]["id"] if vendor_r.status_code == 201 else None

site_r = requests.post(f"{API}/ledger/sites", json={"code": f"SITE-{uuid.uuid4().hex[:6]}", "name": "Test Site"}, headers=auth_headers(admin_token))
site_id = site_r.json()["data"]["id"] if site_r.status_code == 201 else None

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
assert r.status_code == 201, f"Request creation failed: {r.status_code}"
request_id = r.json()["data"]["id"]

# Submit batch
r = requests.post(f"{API}/batches/{batch_id}/submit", headers=auth_headers(creator_token))
assert r.status_code == 200, f"Batch submit failed: {r.status_code}"

# Test concurrent approval
results = []
def approve():
    resp = requests.post(
        f"{API}/requests/{request_id}/approve",
        json={},
        headers=auth_headers(approver_token),
    )
    results.append(resp.status_code)
    print(f"  Thread result: {resp.status_code}")

print(f"\nSending 5 concurrent approval requests for request {request_id}...")
threads = [threading.Thread(target=approve) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"\nResults: {results}")
print(f"Success (200): {results.count(200)}")
print(f"Conflict (409): {results.count(409)}")
print(f"Other codes: {[c for c in results if c not in (200, 409)]}")

# Verify exactly 1 success and 4 conflicts
assert results.count(200) == 1, f"Expected 1 success (200), got {results.count(200)}"
assert results.count(409) == 4, f"Expected 4 conflicts (409), got {results.count(409)}"

print("\n✅ Concurrency test passed!")
EOF

# Run the concurrency test
python3 /tmp/test_concurrency_fix.py
```

**Expected Output**:
```
=== Testing Concurrency Fix ===
Sending 5 concurrent approval requests for request <uuid>...

Results: [200, 409, 409, 409, 409]
Success (200): 1
Conflict (409): 4
Other codes: []

✅ Concurrency test passed!
```

---

### Step 5: Test Idempotency Fix

```bash
# Create idempotency test script
cat > /tmp/test_idempotency_fix.py << 'EOF'
import os
import uuid
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"

ADMIN_USER = os.environ.get("E2E_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("E2E_ADMIN_PASS", "admin123")
CREATOR_USER = "e2e_creator"
CREATOR_PASS = "creator123"
APPROVER_USER = "e2e_approver"
APPROVER_PASS = "approver123"

def login(username, password):
    r = requests.post(f"{API}/auth/login", json={"username": username, "password": password})
    if r.status_code != 200:
        raise Exception(f"Login failed: {r.status_code}")
    return r.json()["data"]["token"]

print("=== Testing Idempotency Fix ===")

admin_token = login(ADMIN_USER, ADMIN_PASS)
creator_token = login(CREATOR_USER, CREATOR_PASS)
approver_token = login(APPROVER_USER, APPROVER_PASS)

# Create batch
batch_name = f"IdempotencyTest-{uuid.uuid4().hex[:6]}"
r = requests.post(
    f"{API}/batches",
    json={"name": batch_name},
    headers={
        "Authorization": f"Bearer {creator_token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    },
)
batch_id = r.json()["data"]["id"]

# Create vendor and site
vendor_r = requests.post(
    f"{API}/ledger/vendors",
    json={"name": f"Vendor-{uuid.uuid4().hex[:6]}"},
    headers={
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    },
)
vendor_id = vendor_r.json()["data"]["id"]

site_r = requests.post(
    f"{API}/ledger/sites",
    json={"code": f"SITE-{uuid.uuid4().hex[:6]}", "name": "Test Site"},
    headers={
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    },
)
site_id = site_r.json()["data"]["id"]

# Create request
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

r1 = requests.post(f"{API}/batches/{batch_id}/requests", json=payload, headers=headers)
r2 = requests.post(f"{API}/batches/{batch_id}/requests", json=payload, headers=headers)

print(f"First request: {r1.status_code}")
print(f"Second request (same idempotency key): {r2.status_code}")

assert r1.status_code == r2.status_code, f"Idempotency violation: {r1.status_code} != {r2.status_code}"
assert r1.status_code in (201, 409), f"Unexpected status: {r1.status_code}"

print("✅ Idempotency test passed!")
EOF

python3 /tmp/test_idempotency_fix.py
```

**Expected Output**:
```
=== Testing Idempotency Fix ===
First request: 201
Second request (same idempotency key): 201
✅ Idempotency test passed!
```

---

### Step 6: Verify Code Changes

```bash
# Verify the fixes are in place
grep -A 5 "Check if ApprovalRecord already exists" backend/apps/payments/services.py
```

**Expected**: Should show the new existence check code

```bash
# Verify IntegrityError import
grep "from django.db import.*IntegrityError" backend/apps/payments/services.py
```

**Expected**: Should show `from django.db import transaction, IntegrityError`

---

### Step 7: Run Unit Tests (if available)

```bash
# Run Django tests if they exist
cd backend
python manage.py test apps.payments.tests 2>&1 | head -50
```

---

## Troubleshooting

### Issue: "Failed to resolve 'backend'"

**Solution**: Set BASE_URL to the correct host:
```bash
export BASE_URL="http://localhost:8000"  # For local development
# OR
export BASE_URL="http://127.0.0.1:8000"  # Alternative
```

### Issue: "Login failed"

**Solution**: Ensure test users exist. The test should create them, but if not:
```bash
cd backend
python manage.py shell
```

Then in Python shell:
```python
from apps.users.models import User
User.objects.create_user(username="e2e_creator", password="creator123", role="CREATOR", display_name="Creator")
User.objects.create_user(username="e2e_approver", password="approver123", role="APPROVER", display_name="Approver")
```

### Issue: "Concurrency test shows wrong status codes"

**Check**:
1. Ensure database supports transactions properly
2. Check that `select_for_update()` is working
3. Verify ApprovalRecord model has OneToOneField constraint

### Issue: Test hangs or times out

**Solution**: Check database connection and ensure transactions are committing properly.

---

## Success Criteria

✅ All tests pass without errors
✅ Concurrency test shows exactly 1 success (200) and 4 conflicts (409)
✅ Idempotency test shows same status code for duplicate requests
✅ No IntegrityError exceptions (should be caught and handled)
✅ No 500 Internal Server Error responses

---

## Summary of Fixes Applied

1. **approve_request**: Added `ApprovalRecord.objects.filter(payment_request=request).exists()` check before creating
2. **approve_request**: Added try/except IntegrityError handling for race conditions
3. **reject_request**: Replaced `hasattr()` with `exists()` check for reliability
4. **reject_request**: Added try/except IntegrityError handling
5. **Both functions**: Return success immediately if ApprovalRecord exists (idempotency)

All fixes ensure proper concurrency handling and idempotency as required by the API contract.
