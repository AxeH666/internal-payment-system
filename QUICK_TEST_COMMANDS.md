# Quick Test Commands - Copy & Paste Ready

## Prerequisites Check
```bash
# 1. Check backend is running
curl -f http://localhost:8000/api/health/ || echo "❌ Backend not running - start it first"
```

## Set Environment Variables
```bash
# 2. Set environment variables
export BASE_URL="http://localhost:8000"
export E2E_ADMIN_USER="admin"
export E2E_ADMIN_PASS="admin123"
```

## Run Full E2E Test
```bash
# 3. Run the complete test suite
cd /home/axehe/internal-payment-system
python3 backend/scripts/system_e2e_hardening_test.py
```

## Expected Success Output
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

## Verify Fixes Are Applied
```bash
# 4. Verify the fixes are in the code
grep -A 3 "Check if ApprovalRecord already exists" backend/apps/payments/services.py
grep "from django.db import.*IntegrityError" backend/apps/payments/services.py
```

## If Backend Not Running
```bash
# Start backend (choose one method):

# Method 1: Django development server
cd backend
python manage.py runserver 0.0.0.0:8000

# Method 2: Docker Compose
docker-compose up backend
```

---

**All fixes have been applied. Run the commands above to test.**
