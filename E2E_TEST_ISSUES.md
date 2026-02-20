# E2E Hardening Test Issues Analysis

## Test Overview
The `system_e2e_hardening_test.py` tests:
1. Health check
2. User setup
3. Ledger entity creation
4. State machine transitions (including concurrency test)
5. Idempotency enforcement

## Critical Issues Found

### Issue 1: Missing ApprovalRecord Existence Check in `approve_request`

**Location**: `backend/apps/payments/services.py:689-798`

**Problem**: 
The `approve_request` function does not check if an `ApprovalRecord` already exists before attempting to create one. According to the API contract (docs/04_API_CONTRACT.md:837):
> "If ApprovalRecord already exists for this request (regardless of decision), return success with current request state."

**Current Code Flow**:
1. Idempotency key check (outside transaction) - lines 712-720
2. Lock PaymentRequest - line 724
3. Check request status - lines 740-752
4. **Directly create ApprovalRecord** - lines 754-760 (NO CHECK FOR EXISTING RECORD)
5. Update request status

**Expected Behavior**:
Before creating an ApprovalRecord, the code should check if one already exists. If it exists, return the request immediately with success.

**Impact**: 
- Violates API contract idempotency rules
- Concurrent approval attempts may cause IntegrityError instead of graceful 409 CONFLICT
- Test expects 409 for duplicate approvals, but may get IntegrityError

---

### Issue 2: Idempotency Check Outside Transaction

**Location**: `backend/apps/payments/services.py:712-720`

**Problem**:
The idempotency key check happens BEFORE the transaction starts. This means:
- Multiple concurrent requests with DIFFERENT idempotency keys will all pass the check
- They will all enter the transaction and try to create ApprovalRecords
- Only one will succeed, others will hit IntegrityError

**Current Flow**:
```python
# OUTSIDE transaction
if idempotency_key:
    existing_key = IdempotencyKey.objects.filter(...).first()
    if existing_key:
        return request  # Early return

# INSIDE transaction
with transaction.atomic():
    request = PaymentRequest.objects.select_for_update().get(...)
    # ... checks ...
    ApprovalRecord.objects.create(...)  # May fail with IntegrityError
```

**Expected Behavior**:
The idempotency check should happen INSIDE the transaction, or the ApprovalRecord existence check should be the primary guard.

**Impact**:
- Concurrency test expects exactly 1 success (200) and 4 conflicts (409)
- Current implementation may return IntegrityError (500) instead of 409 CONFLICT
- Different idempotency keys bypass the idempotency check

---

### Issue 3: Missing ApprovalRecord Existence Check Before Creation

**Location**: `backend/apps/payments/services.py:754-760`

**Problem**:
The code directly creates an ApprovalRecord without checking if one already exists:

```python
# Create ApprovalRecord
ApprovalRecord.objects.create(
    payment_request=request,
    approver=approver,
    decision="APPROVED",
    comment=comment.strip() if comment else None,
)
```

**Model Constraint**:
`ApprovalRecord` has a `OneToOneField` relationship with `PaymentRequest` (models.py:259-260), meaning only ONE ApprovalRecord can exist per PaymentRequest.

**Expected Behavior**:
```python
# Check if ApprovalRecord already exists
if hasattr(request, 'approval') or ApprovalRecord.objects.filter(payment_request=request).exists():
    # Return success with current state (idempotency)
    return request

# Only create if it doesn't exist
ApprovalRecord.objects.create(...)
```

**Impact**:
- Violates API contract requirement for idempotency
- Concurrent requests will hit IntegrityError
- Test expects graceful 409 CONFLICT, not IntegrityError

---

### Issue 4: Error Handling for IntegrityError

**Location**: `backend/apps/payments/views.py:543-555`

**Problem**:
The view catches `IntegrityError` and returns 409 CONFLICT, but this may not be the right approach if we properly check for existing ApprovalRecords first.

**Current Code**:
```python
except IntegrityError:
    return Response(
        {
            "error": {
                "code": "CONFLICT",
                "message": "Approval conflict (duplicate approval or idempotency)",
                "details": {},
            }
        },
        status=status.HTTP_409_CONFLICT,
    )
```

**Expected Behavior**:
If we properly check for existing ApprovalRecords before creation, IntegrityError should be rare. When it occurs, it should be treated as a concurrency conflict.

**Impact**:
- May mask other IntegrityError issues
- Should be a last-resort fallback, not primary error handling

---

### Issue 5: Concurrency Test Expectations

**Location**: `backend/scripts/system_e2e_hardening_test.py:185-207`

**Test Expectation**:
```python
# Concurrency approve test
results = []
def approve():
    resp = requests.post(...)
    results.append(resp.status_code)

threads = [threading.Thread(target=approve) for _ in range(5)]
# ... start and join ...

if results.count(200) != 1:
    fail("Concurrency violation: approve should succeed once")

if results.count(409) != 4:
    fail("Concurrency violation: remaining should conflict")
```

**Problem**:
The test expects:
- Exactly 1 success (200)
- Exactly 4 conflicts (409)

But current implementation may:
- Return IntegrityError (500) instead of 409
- Not properly handle concurrent requests with different idempotency keys
- Not check for existing ApprovalRecord before creation

---

## Root Cause Summary

The primary issue is that `approve_request` does not check if an `ApprovalRecord` already exists before attempting to create one. This violates the API contract's idempotency requirements and causes concurrency issues.

**Key Fix Required**:
1. Check for existing ApprovalRecord INSIDE the transaction (after acquiring lock)
2. If ApprovalRecord exists, return success immediately (idempotency)
3. Only create ApprovalRecord if it doesn't exist
4. Handle IntegrityError as a fallback for race conditions

---

## Recommended Fixes

### Fix 1: Add ApprovalRecord Existence Check
```python
# Inside transaction, after acquiring lock
with transaction.atomic():
    request = PaymentRequest.objects.select_for_update().get(id=request_id)
    
    # ... existing checks ...
    
    # Check if ApprovalRecord already exists (idempotency)
    if hasattr(request, 'approval') or ApprovalRecord.objects.filter(payment_request=request).exists():
        # Refresh to get latest state
        request.refresh_from_db()
        return request
    
    # Only create if it doesn't exist
    ApprovalRecord.objects.create(...)
```

### Fix 2: Move Idempotency Check Inside Transaction
Or rely on ApprovalRecord existence check as the primary idempotency mechanism.

### Fix 3: Ensure Proper Error Mapping
Ensure IntegrityError is caught and mapped to 409 CONFLICT with appropriate message.

---

## Additional Observations

1. **reject_request** has inconsistent implementation (line 864-867) - it DOES check `hasattr(request, "approval")` but `approve_request` does NOT. This inconsistency suggests the check was added to reject_request but forgotten in approve_request.

2. **hasattr() limitation**: Using `hasattr(request, "approval")` may not be reliable in concurrent scenarios:
   - Django's OneToOneField reverse accessor may trigger a database query
   - In concurrent scenarios, another transaction might create ApprovalRecord between check and create
   - Better approach: Use `ApprovalRecord.objects.filter(payment_request=request).exists()` or try/except around create

3. **IdempotencyKey model** exists but may not be the primary mechanism for preventing duplicate approvals - the OneToOneField constraint is the real guard. The idempotency key check happens outside the transaction, making it ineffective for concurrent requests with different keys.

4. **Test environment**: Test cannot run without backend service running (`backend` hostname not resolvable), but code analysis reveals these issues.

5. **Domain Model Discrepancy**: The domain model docs (02_DOMAIN_MODEL.md:222) says "One PaymentRequest may have zero or more ApprovalRecords" but the actual model uses OneToOneField, meaning only ONE ApprovalRecord per PaymentRequest. This is correct per the API contract, but the domain model doc is misleading.

## Summary of Required Fixes

### Critical Fix for `approve_request`:
1. Add ApprovalRecord existence check INSIDE transaction (after lock)
2. Use `ApprovalRecord.objects.filter(payment_request=request).exists()` instead of `hasattr()`
3. Return success immediately if ApprovalRecord exists (idempotency)
4. Wrap ApprovalRecord.create() in try/except to handle race conditions
5. Map IntegrityError to 409 CONFLICT with appropriate message

### Recommended Pattern:
```python
with transaction.atomic():
    request = PaymentRequest.objects.select_for_update().get(id=request_id)
    
    # ... existing validation checks ...
    
    # Check if ApprovalRecord already exists (idempotency)
    if ApprovalRecord.objects.filter(payment_request=request).exists():
        request.refresh_from_db()  # Get latest state
        return request
    
    # Try to create ApprovalRecord (may fail in race condition)
    try:
        ApprovalRecord.objects.create(
            payment_request=request,
            approver=approver,
            decision="APPROVED",
            comment=comment.strip() if comment else None,
        )
    except IntegrityError:
        # Race condition: another transaction created it
        request.refresh_from_db()
        return request  # Return success (idempotency)
    
    # ... rest of approval logic ...
```
