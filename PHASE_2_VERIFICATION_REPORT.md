# Phase 2 Critical Safeguards Verification Report

**Date:** 2026-02-18  
**Branch:** phase-2-ledger  
**Architecture Version:** v0.2.0

---

## Executive Summary

This report verifies the implementation of 5 critical safeguards required for Phase 2 financial system integrity. **3 out of 5 safeguards are FULLY IMPLEMENTED**, **1 is PARTIALLY IMPLEMENTED** (requires database migration execution), and **1 has a CRITICAL GAP** (idempotency key not passed from view to service).

---

## 1. DB CHECK Constraints ✅ PARTIALLY IMPLEMENTED

### Status: **MIGRATION EXISTS BUT NOT VERIFIED IN DATABASE**

### Verification Steps Performed:
1. ✅ Migration file exists: `backend/apps/payments/migrations/0005_add_phase2_constraints.py`
2. ✅ All three constraints defined:
   - `legacy_or_ledger_exclusive` - Ensures mutual exclusivity between legacy and ledger-driven requests
   - `vendor_or_subcontractor_exclusive` - Ensures only one FK is set (vendor OR subcontractor OR neither for legacy)
   - `total_amount_integrity` - Ensures `total_amount = base_amount + extra_amount` when not null

### Migration Code Review:
```python
# Migration 0005_add_phase2_constraints.py contains:
- CheckConstraint for legacy_or_ledger_exclusive ✅
- CheckConstraint for vendor_or_subcontractor_exclusive ✅
- CheckConstraint for total_amount_integrity ✅
```

### Database Verification Required:
**CRITICAL:** Cannot verify constraints are actually in PostgreSQL without database access.

**Required Action:**
```bash
# Run this command when database is available:
python manage.py dbshell

# Then execute:
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'payment_requests'::regclass
AND conname IN ('legacy_or_ledger_exclusive', 'vendor_or_subcontractor_exclusive', 'total_amount_integrity');
```

**Expected Result:** Should return 3 rows, one for each constraint.

**Risk Level:** 🟡 **MEDIUM** - Migration exists but not verified in database. If migration hasn't been run, constraints are NOT protecting data.

---

## 2. Idempotency Enforcement in Endpoints ❌ CRITICAL GAP

### Status: **SERVICE IMPLEMENTED BUT VIEW DOES NOT PASS KEY**

### Service Layer Implementation: ✅ CORRECT
**File:** `backend/apps/payments/services.py` (lines 133-142)

```python
# Idempotency check
if idempotency_key:
    existing_key = IdempotencyKey.objects.filter(
        key=idempotency_key, operation="CREATE_PAYMENT_REQUEST"
    ).first()
    if existing_key and existing_key.target_object_id:
        try:
            return PaymentRequest.objects.get(id=existing_key.target_object_id)
        except PaymentRequest.DoesNotExist:
            pass  # Key exists but object missing, proceed with creation
```

**Analysis:** Service correctly checks for existing idempotency key and returns original object if found.

### View Layer Implementation: ❌ MISSING
**File:** `backend/apps/payments/views.py` (lines 218-273)

```python
@api_view(["POST"])
@permission_classes([IsCreator])
def add_request(request, batchId):
    # ... validation code ...
    try:
        payment_request = services.add_request(
            batchId,
            request.user.id,
            amount,
            currency,
            beneficiary_name,
            beneficiary_account,
            purpose,
            # ❌ MISSING: idempotency_key parameter
        )
```

**Problem:** View does NOT extract `idempotency_key` from `request.idempotency_key` (set by middleware) and pass it to service.

### Middleware Implementation: ✅ CORRECT
**File:** `backend/core/middleware.py` (lines 55-86)

```python
class IdempotencyKeyMiddleware:
    def __call__(self, request):
        if request.method in self.MUTATION_METHODS:
            # ... checks ...
            idempotency_key = request.headers.get("Idempotency-Key")
            if not idempotency_key:
                return Response(...)  # Returns 400 if missing
            request.idempotency_key = idempotency_key  # ✅ Sets on request
```

**Analysis:** Middleware correctly extracts header and sets `request.idempotency_key`.

### Required Fix:
```python
# In views.py add_request function, change:
payment_request = services.add_request(
    batchId,
    request.user.id,
    amount,
    currency,
    beneficiary_name,
    beneficiary_account,
    purpose,
    idempotency_key=getattr(request, 'idempotency_key', None),  # ADD THIS
)
```

**Risk Level:** 🔴 **CRITICAL** - Without this fix, idempotency protection is completely bypassed. Duplicate requests can be created on retries.

---

## 3. Version Locking ✅ FULLY IMPLEMENTED

### Status: **CORRECTLY IMPLEMENTED**

### Verification Results:

#### approve_request() - ✅ CORRECT
**File:** `backend/apps/payments/services.py` (lines 745-752)

```python
current_version = request.version
updated_count = version_locked_update(
    PaymentRequest.objects.filter(
        id=request_id, status="PENDING_APPROVAL", version=current_version  # ✅ Includes version
    ),
    current_version=current_version,
    status="APPROVED",
    updated_by=approver,
)
```

**Analysis:** Filter includes `version=current_version` ✅

#### reject_request() - ✅ CORRECT
**File:** `backend/apps/payments/services.py` (lines 834-841)

```python
current_version = request.version
updated_count = version_locked_update(
    PaymentRequest.objects.filter(
        id=request_id, status="PENDING_APPROVAL", version=current_version  # ✅ Includes version
    ),
    current_version=current_version,
    status="REJECTED",
    updated_by=approver,
)
```

**Analysis:** Filter includes `version=current_version` ✅

#### mark_paid() - ✅ CORRECT
**File:** `backend/apps/payments/services.py` (lines 912-919)

```python
current_version = request.version
updated_count = version_locked_update(
    PaymentRequest.objects.filter(
        id=request_id, status="APPROVED", version=current_version  # ✅ Includes version
    ),
    current_version=current_version,
    status="PAID",
    updated_by=actor,
)
```

**Analysis:** Filter includes `version=current_version` ✅

#### version_locked_update() Helper - ✅ CORRECT
**File:** `backend/apps/payments/versioning.py` (lines 24-27)

```python
updated_count = queryset.filter(version=current_version).update(
    **updates,
    version=F("version") + 1,  # ✅ Atomically increments version
)
```

**Analysis:** Helper correctly filters by version and atomically increments.

**Risk Level:** 🟢 **LOW** - Version locking is correctly implemented. Concurrent modifications will be detected and rejected.

---

## 4. Snapshot Population Enforcement ✅ FULLY IMPLEMENTED

### Status: **AUTOMATICALLY POPULATED IN SERVICE LAYER**

### Verification Results:

**File:** `backend/apps/payments/services.py` (lines 256-259, 298-300)

```python
# Populate snapshots (mandatory for ledger-driven)
vendor_snapshot_name = vendor.name if entity_type == "VENDOR" else None
subcontractor_snapshot_name = (
    subcontractor.name if entity_type == "SUBCONTRACTOR" else None
)
site_snapshot_code = site.code

# ... later in request creation ...
request_data.update({
    # ...
    "vendor_snapshot_name": vendor_snapshot_name,
    "subcontractor_snapshot_name": subcontractor_snapshot_name,
    "site_snapshot_code": site_snapshot_code,
})
```

**Analysis:**
- ✅ Snapshots are populated **server-side** in service layer
- ✅ No reliance on frontend
- ✅ Snapshots are mandatory for ledger-driven requests (set before creation)
- ✅ Vendor snapshot only set when entity_type=VENDOR
- ✅ Subcontractor snapshot only set when entity_type=SUBCONTRACTOR
- ✅ Site snapshot always set for ledger-driven requests

**Risk Level:** 🟢 **LOW** - Snapshots are correctly populated automatically. Historical data integrity is preserved.

---

## 5. Immutability Enforcement ⚠️ PARTIALLY IMPLEMENTED

### Status: **CHECK EXISTS BUT HAS LOGIC ISSUE**

### Verification Results:

**File:** `backend/apps/payments/services.py` (lines 400-408)

```python
# Check request state
if request.status != "DRAFT":
    raise InvalidStateError(f"Cannot update request with status {request.status}")

# Phase 2: Immutable financial lock - block modifications when APPROVED/PAID
if request.status in ("APPROVED", "PAID"):
    raise InvalidStateError(
        "Financial fields are locked when request is APPROVED or PAID"
    )
```

### Problem Identified:
**Logic Issue:** The second check is **unreachable** because the first check already raises an error if status != "DRAFT". If status is APPROVED or PAID, the first check will catch it.

**However:** The check is still **functionally correct** because:
- If status = APPROVED → First check raises "Cannot update request with status APPROVED" ✅
- If status = PAID → First check raises "Cannot update request with status PAID" ✅

The second check is redundant but doesn't cause harm.

### Required Test:
To verify immutability works, test:
```python
# Test case:
request.status = "APPROVED"
# Attempt update_request()
# Expected: InvalidStateError("Cannot update request with status APPROVED")
```

**Risk Level:** 🟡 **LOW-MEDIUM** - Functionally correct but redundant code. Should be cleaned up for clarity.

---

## Summary Table

| Safeguard | Status | Risk Level | Action Required |
|-----------|--------|------------|-----------------|
| 1. DB CHECK Constraints | ⚠️ Migration exists, DB not verified | 🟡 MEDIUM | Run migration and verify in database |
| 2. Idempotency Enforcement | ❌ View doesn't pass key | 🔴 CRITICAL | Fix view to pass `idempotency_key` parameter |
| 3. Version Locking | ✅ Fully implemented | 🟢 LOW | None - working correctly |
| 4. Snapshot Population | ✅ Fully implemented | 🟢 LOW | None - working correctly |
| 5. Immutability Enforcement | ⚠️ Redundant but functional | 🟡 LOW-MEDIUM | Clean up redundant check (optional) |

---

## Critical Actions Required

### 🔴 IMMEDIATE (Before Production):
1. **Fix idempotency key passing in views.py** - Add `idempotency_key=getattr(request, 'idempotency_key', None)` to `add_request()` call
2. **Verify database constraints** - Run migration and confirm constraints exist in PostgreSQL

### 🟡 HIGH PRIORITY (Before Phase 2 Completion):
3. **Test immutability enforcement** - Verify APPROVED/PAID requests cannot be updated
4. **Clean up redundant immutability check** - Remove second check or combine logic

### 🟢 OPTIONAL (Code Quality):
5. **Add integration tests** for all 5 safeguards
6. **Document idempotency key usage** in API documentation

---

## Test Recommendations

### Test 1: Idempotency Key Enforcement
```python
# Test that duplicate requests with same idempotency key return same object
key = "test-key-123"
req1 = add_request(..., idempotency_key=key)
req2 = add_request(..., idempotency_key=key)
assert req1.id == req2.id  # Should return same object
```

### Test 2: Version Locking
```python
# Test concurrent approval rejection
request = create_request(status="PENDING_APPROVAL", version=1)
# Thread 1: approve_request() with version=1
# Thread 2: approve_request() with version=1
# Expected: Only one succeeds, other gets InvalidStateError
```

### Test 3: Immutability
```python
# Test that APPROVED requests cannot be updated
request = create_request(status="APPROVED")
try:
    update_request(request.id, amount=999)
    assert False, "Should have raised InvalidStateError"
except InvalidStateError:
    pass  # Expected
```

### Test 4: Snapshot Population
```python
# Test that snapshots are populated automatically
vendor = Vendor.objects.create(name="Test Vendor", ...)
request = add_request(..., entity_type="VENDOR", vendor_id=vendor.id, ...)
assert request.vendor_snapshot_name == "Test Vendor"  # Should be set automatically
```

### Test 5: Database Constraints
```sql
-- Test that constraint prevents invalid data
-- This should fail:
INSERT INTO payment_requests (entity_type, beneficiary_name, ...) 
VALUES ('VENDOR', 'Legacy Name', ...);  -- Should violate legacy_or_ledger_exclusive
```

---

## Conclusion

**Overall Status:** ⚠️ **PARTIALLY SAFE**

- **3 safeguards fully implemented** ✅
- **1 safeguard has critical gap** ❌ (idempotency key not passed)
- **1 safeguard needs database verification** ⚠️

**Recommendation:** **DO NOT DEPLOY** until idempotency key fix is applied and database constraints are verified. The system is vulnerable to duplicate request creation on retries without the idempotency fix.

---

**Report Generated:** 2026-02-18  
**Next Review:** After fixes are applied
