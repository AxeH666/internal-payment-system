# Final Fix Summary

## Issue Identified

The test expects **409 CONFLICT** for duplicate approvals when status is APPROVED, but the code was returning success when ApprovalRecord exists.

## Fix Applied

Changed the logic so that:
1. **Status check happens FIRST**
2. If status is **APPROVED** → always return **409 CONFLICT** (duplicate approval)
3. If status is **PENDING_APPROVAL** → check ApprovalRecord existence
4. If ApprovalRecord exists → return success (idempotency for race conditions)

## Code Flow

```
1. Acquire lock on PaymentRequest
2. Check status:
   - If APPROVED → raise InvalidStateError (409 CONFLICT)
   - If not PENDING_APPROVAL → raise InvalidStateError
3. If PENDING_APPROVAL:
   - Check ApprovalRecord.exists()
   - If exists → return success (race condition handling)
   - If not exists → create ApprovalRecord
4. Update status to APPROVED
```

## Test Expectations

- **Concurrency test**: 5 concurrent approvals
  - 1st succeeds → creates ApprovalRecord, updates status to APPROVED
  - 2nd-5th see status APPROVED → return 409 CONFLICT ✅

## Files Modified

- `backend/apps/payments/services.py` - Fixed `approve_request` function

## Testing

Run:
```bash
export BASE_URL="http://localhost:8000"
export E2E_ADMIN_USER="admin"
export E2E_ADMIN_PASS="admin123"
python3 backend/scripts/system_e2e_hardening_test.py
```

Expected: All tests pass, including concurrency test with 1x 200 and 4x 409.
