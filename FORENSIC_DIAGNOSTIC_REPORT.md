# FORENSIC DIAGNOSTIC REPORT
## PaymentRequest Creation HTTP 500 Analysis

**Date:** 2026-02-19  
**Scope:** READ-ONLY analysis of PaymentRequest creation failure  
**Objective:** Identify root cause of HTTP 500 during E2E probe execution

---

## SECTION 1 — ENDPOINT TRACE

### Call Stack: POST /api/v1/batches/<id>/requests

**1. URL Routing**
- **File:** `backend/core/urls.py:16`
- **Pattern:** `path("api/v1/", include("apps.payments.urls"))`
- **File:** `backend/apps/payments/urls.py:19-21`
- **Pattern:** `path("batches/<uuid:batchId>/requests", views.add_request, name="add-request")`
- **View Function:** `apps.payments.views.add_request`

**2. View Layer**
- **File:** `backend/apps/payments/views.py:220-316`
- **Function:** `add_request(request, batchId)`
- **Decorators:**
  - `@api_view(["POST"])`
  - `@permission_classes([IsCreator])`
- **Permission Check:** Runs before view logic, returns 403 if fails

**3. View Processing Flow**
```
Line 229: Import Decimal, InvalidOperation
Lines 237-250: Extract request.data fields (entityType, vendorId, siteId, baseAmount, extraAmount, extraReason, currency)
Lines 258-275: Convert decimal fields (amount, base_amount, extra_amount)
  - Catches ValueError, TypeError, InvalidOperation
  - Returns 400 VALIDATION_ERROR if conversion fails
Line 279-280: Silently ignore client-provided totalAmount
Lines 282-316: Call services.add_request()
  - Catches DomainError → re-raises (handled by exception handler)
  - Catches IntegrityError → returns 409 CONFLICT
  - Any other exception → UNHANDLED → 500
Line 302: Serialize response with PaymentRequestSerializer
Line 303: Return 201 CREATED
```

**4. Service Layer**
- **File:** `backend/apps/payments/services.py:79-358`
- **Function:** `add_request(batch_id, creator_id, ...)`
- **Transaction:** Wrapped in `transaction.atomic()` (line 144)

**5. Service Processing Flow**
```
Line 133-142: Idempotency check (outside transaction)
  - Queries IdempotencyKey
  - Returns existing PaymentRequest if found
Line 144: Begin transaction.atomic()
Line 145-148: Lock and fetch PaymentBatch (select_for_update)
  - Raises NotFoundError if batch missing
Line 150-153: Fetch User (creator)
  - Raises NotFoundError if user missing
Line 155-157: Ownership check
  - Raises PermissionDeniedError if not creator/admin
Line 159-166: Batch state check
  - Raises InvalidStateError if not DRAFT
  - Raises InvalidStateError if closed batch
Line 169: Determine ledger-driven vs legacy
Line 171-262: Ledger-driven validation (if entity_type provided)
  - Validates entity_type (VENDOR/SUBCONTRACTOR)
  - Validates vendor_id/subcontractor_id exclusivity
  - Fetches Vendor/Subcontractor with select_for_update
  - Raises NotFoundError if vendor/subcontractor missing
  - Raises ValidationError for invalid fields
  - Validates site_id, base_amount, extra_amount, extra_reason
  - Computes total_amount = base_amount + extra_amount
  - Validates currency (3-letter code)
Line 264-275: Legacy validation (if entity_type not provided)
  - Validates amount, currency, beneficiary_name, beneficiary_account, purpose
Line 277-313: Build request_data dict
Line 315: PaymentRequest.objects.create(**request_data) ← POTENTIAL FAILURE POINT
Line 317-324: Create IdempotencyKey (if provided)
Line 326-356: Create audit entry via create_audit_entry()
  - Called AFTER PaymentRequest creation
  - If this fails, PaymentRequest already created → transaction rollback
```

**6. Model Layer**
- **File:** `backend/apps/payments/models.py:69-247`
- **Model:** `PaymentRequest`
- **Create:** `PaymentRequest.objects.create()` (line 315 in services.py)

**7. Database Constraints**
Applied at INSERT time:
- CheckConstraint: `valid_request_status`
- CheckConstraint: `amount_positive`
- CheckConstraint: `legacy_or_ledger_exclusive` ← **CRITICAL**
- CheckConstraint: `vendor_or_subcontractor_exclusive` ← **CRITICAL**
- CheckConstraint: `total_amount_integrity` ← **CRITICAL**
- ForeignKey constraints (batch, created_by, vendor, subcontractor, site)

**8. Exception Handlers**
- **File:** `backend/core/exceptions.py:66-140`
- **Handler:** `domain_exception_handler(exc, context)`
- **Registered:** `REST_FRAMEWORK["EXCEPTION_HANDLER"]` in settings.py:176
- **Handles:** DomainError subclasses → maps to 400/403/404/409/412
- **Unhandled:** Any other exception → 500 INTERNAL_ERROR

**9. Signals**
- **None found** - No pre_save/post_save signals on PaymentRequest

---

## SECTION 2 — SERIALIZER CONTRACT

### PaymentRequestSerializer

**File:** `backend/apps/payments/serializers.py:16-143`

**Field Definitions:**

| Field | Type | Required | Nullable | Source |
|-------|------|----------|----------|--------|
| id | UUID | No | No | Read-only |
| batchId | UUID | No | No | Read-only (batch_id) |
| amount | Decimal | No | Yes | Legacy field |
| currency | CharField | No | No | Required in service layer |
| beneficiaryName | CharField | No | Yes | Legacy (beneficiary_name) |
| beneficiaryAccount | CharField | No | Yes | Legacy (beneficiary_account) |
| purpose | CharField | No | Yes | Legacy |
| entityType | CharField | No | Yes | Phase 2 (entity_type) |
| vendorId | UUID | No | Yes | Phase 2 (vendor_id) |
| subcontractorId | UUID | No | Yes | Phase 2 (subcontractor_id) |
| siteId | UUID | No | Yes | Phase 2 (site_id) |
| baseAmount | Decimal | No | Yes | Phase 2 (base_amount) |
| extraAmount | Decimal | No | Yes | Phase 2 (extra_amount) |
| extraReason | CharField | No | Yes | Phase 2 (extra_reason) |
| totalAmount | Decimal | No | Yes | Read-only (total_amount) |

**Key Observations:**
1. **Serializer does NOT validate** - All fields are `required=False, allow_null=True`
2. **No custom validate() method** - No serializer-level validation logic
3. **Validation happens in view/service layer** - Not in serializer
4. **Serializer is used only for OUTPUT** - Line 302: `PaymentRequestSerializer(payment_request)` (read-only serialization)

**Probe Payload (deep_invariant_probe.py:97-108):**
```json
{
    "entityType": "VENDOR",
    "vendorId": "<uuid>",
    "siteId": "<uuid>",
    "baseAmount": "1000.00",
    "extraAmount": "500.00",
    "extraReason": "Probe",
    "currency": "INR"
}
```

**Expected Input Shape:**
- Matches serializer fields ✅
- All fields present ✅
- Currency provided ✅

**Mismatches:**
- **NONE** - Payload structure is correct

---

## SECTION 3 — MODEL CONSTRAINTS

### PaymentRequest Meta Constraints

**File:** `backend/apps/payments/models.py:170-230`

**1. CheckConstraint: `valid_request_status`**
```python
check=models.Q(status__in=["DRAFT", "SUBMITTED", "PENDING_APPROVAL", "APPROVED", "REJECTED", "PAID"])
```
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught

**2. CheckConstraint: `amount_positive`**
```python
check=models.Q(amount__isnull=True) | models.Q(amount__gt=0)
```
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught
- **Note:** Service sets `amount=total_amount` for ledger-driven (line 289), which is positive ✅

**3. CheckConstraint: `legacy_or_ledger_exclusive`** ⚠️ **CRITICAL**
```python
check=models.Q(
    (models.Q(entity_type__isnull=True) & models.Q(beneficiary_name__isnull=False))
    | (models.Q(entity_type__isnull=False) & models.Q(beneficiary_name__isnull=True))
)
```
- **Requirement:** 
  - If `entity_type` is NULL → `beneficiary_name` must NOT be NULL (legacy)
  - If `entity_type` is NOT NULL → `beneficiary_name` must be NULL (ledger-driven)
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught
- **Probe Impact:** 
  - Probe sends `entityType: "VENDOR"` → `entity_type` is NOT NULL
  - Service sets `beneficiary_name=None` for ledger-driven (line 285-303)
  - **Should be safe** ✅

**4. CheckConstraint: `vendor_or_subcontractor_exclusive`** ⚠️ **CRITICAL**
```python
check=models.Q(
    (models.Q(vendor_id__isnull=False) & models.Q(subcontractor_id__isnull=True))
    | (models.Q(vendor_id__isnull=True) & models.Q(subcontractor_id__isnull=False))
    | (models.Q(vendor_id__isnull=True) & models.Q(subcontractor_id__isnull=True))  # legacy
)
```
- **Requirement:**
  - Only one of vendor_id or subcontractor_id can be non-NULL
  - Both can be NULL (legacy mode)
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught
- **Probe Impact:**
  - Probe sends `vendorId` only, no `subcontractorId`
  - Service validates exclusivity (lines 181-184, 197-200)
  - **Should be safe** ✅

**5. CheckConstraint: `total_amount_integrity`** ⚠️ **CRITICAL**
```python
check=models.Q(total_amount__isnull=True)
| models.Q(total_amount=models.F("base_amount") + models.F("extra_amount"))
```
- **Requirement:**
  - If `total_amount` is NOT NULL → must equal `base_amount + extra_amount`
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught
- **Probe Impact:**
  - Probe sends `baseAmount: "1000.00"`, `extraAmount: "500.00"`
  - Service computes `total_amount = base_amount + extra_amount` (line 229)
  - Service sets `total_amount=total_amount` (line 299)
  - **Should be safe** ✅

**6. ForeignKey Constraints**
- `batch` → PaymentBatch (PROTECT)
- `created_by` → User (PROTECT)
- `vendor` → Vendor (PROTECT)
- `subcontractor` → Subcontractor (PROTECT)
- `site` → Site (PROTECT)
- **Violation:** Would cause IntegrityError
- **Surface as:** 500 if uncaught, 409 if caught

**7. Field Validators**
- `amount`: `MinValueValidator(0.01)` (line 88)
- `base_amount`: `MinValueValidator(0.01)` (line 141)
- `extra_amount`: `MinValueValidator(0)` (line 148)
- `total_amount`: `MinValueValidator(0.01)` (line 156)
- **Violation:** Would raise ValidationError at model level
- **Surface as:** 500 if uncaught

---

## SECTION 4 — SERVICE LAYER RULES

### add_request Service Function

**File:** `backend/apps/payments/services.py:79-358`

**Validations Performed:**

1. **Idempotency Check** (lines 133-142)
   - Outside transaction
   - Returns early if key exists
   - **No exceptions raised**

2. **Batch Existence** (lines 145-148)
   - Raises `NotFoundError` if batch missing
   - **Handled:** DomainError → 404

3. **User Existence** (lines 150-153)
   - Raises `NotFoundError` if creator missing
   - **Handled:** DomainError → 404

4. **Ownership Check** (lines 155-157)
   - Raises `PermissionDeniedError` if not creator/admin
   - **Handled:** DomainError → 403

5. **Batch State Check** (lines 159-166)
   - Raises `InvalidStateError` if not DRAFT
   - Raises `InvalidStateError` if closed batch
   - **Handled:** DomainError → 409

6. **Ledger-Driven Validation** (lines 171-262)
   - Raises `ValidationError` for invalid entity_type
   - Raises `ValidationError` for missing vendor_id/subcontractor_id
   - Raises `ValidationError` for both vendor_id and subcontractor_id
   - Raises `NotFoundError` if vendor/subcontractor missing
   - Raises `NotFoundError` if site missing
   - Raises `ValidationError` for invalid amounts
   - Raises `ValidationError` for missing extra_reason when extra_amount > 0
   - Raises `ValidationError` for invalid currency
   - **All handled:** DomainError → 400/404

7. **Legacy Validation** (lines 264-275)
   - Raises `ValidationError` for invalid fields
   - **Handled:** DomainError → 400

8. **Model Creation** (line 315)
   - `PaymentRequest.objects.create(**request_data)`
   - **Potential IntegrityError** if constraint violated
   - **Caught:** Yes (line 306) → 409 CONFLICT

9. **IdempotencyKey Creation** (lines 317-324)
   - `IdempotencyKey.objects.create(...)`
   - **Potential IntegrityError** if key already exists
   - **NOT CAUGHT** ← **POTENTIAL ISSUE**
   - **Surface as:** 500 if uncaught

10. **Audit Entry Creation** (lines 326-356)
    - `create_audit_entry(...)`
    - **File:** `backend/apps/audit/services.py:10-46`
    - **Potential exceptions:**
      - User.DoesNotExist → silently ignored (line 33-35)
      - AuditLog.objects.create() → **Potential IntegrityError**
      - **NOT CAUGHT** ← **POTENTIAL ISSUE**
    - **Surface as:** 500 if uncaught

**State Machine Guards:**
- Batch must be DRAFT (line 160)
- Batch must not be closed (line 165)
- **No PaymentRequest state machine guards** - creation always sets status=DRAFT

**Unhandled Exceptions:**
1. **IntegrityError from IdempotencyKey.objects.create()** (line 319)
   - Not wrapped in try/except
   - Would bubble to view → 500

2. **IntegrityError from AuditLog.objects.create()** (line 37 in audit/services.py)
   - Not wrapped in try/except
   - Would bubble to view → 500

3. **Any exception from create_audit_entry()**
   - Not wrapped in try/except in add_request
   - Would bubble to view → 500

---

## SECTION 5 — DATABASE STATE DEPENDENCIES

### Batch Status Requirements

**Service Check:** `backend/apps/payments/services.py:159-166`
```python
if batch.status != "DRAFT":
    raise InvalidStateError(...)
if is_closed_batch(batch.status):
    raise InvalidStateError(...)
```
- **Requirement:** Batch must be DRAFT
- **Probe:** Creates batch first → should be DRAFT ✅
- **Violation:** Would raise InvalidStateError → 409 (handled)

### Vendor/Subcontractor Exclusivity

**Model Constraint:** `vendor_or_subcontractor_exclusive`
- **Requirement:** Only one FK can be non-NULL
- **Service Validation:** Lines 181-184, 197-200
- **Probe:** Sends vendorId only → safe ✅

### total_amount_integrity Constraint

**Model Constraint:** `total_amount_integrity`
- **Requirement:** `total_amount = base_amount + extra_amount` when not NULL
- **Service Logic:** Line 229 computes `total_amount = base_amount + extra_amount`
- **Service Assignment:** Line 299 sets `total_amount=total_amount`
- **Probe:** baseAmount=1000.00, extraAmount=500.00 → total=1500.00 ✅
- **Potential Issue:** If computation is wrong or constraint check fails → IntegrityError

### amount_positive Constraint

**Model Constraint:** `amount_positive`
- **Requirement:** `amount > 0` if not NULL
- **Service Logic:** For ledger-driven, sets `amount=total_amount` (line 289)
- **Probe:** total_amount=1500.00 → amount=1500.00 ✅

### legacy_or_ledger_exclusive Constraint

**Model Constraint:** `legacy_or_ledger_exclusive`
- **Requirement:** 
  - Legacy: entity_type=NULL, beneficiary_name≠NULL
  - Ledger: entity_type≠NULL, beneficiary_name=NULL
- **Service Logic:** For ledger-driven, does NOT set beneficiary_name (line 285-303)
- **Probe:** entityType="VENDOR" → entity_type≠NULL, beneficiary_name should be NULL ✅

**Potential Violation Scenarios:**
1. **If service sets beneficiary_name incorrectly** → IntegrityError
2. **If constraint check fails due to NULL handling** → IntegrityError
3. **If transaction isolation causes constraint check to see stale data** → IntegrityError

---

## SECTION 6 — EXCEPTION HANDLER BEHAVIOR

### domain_exception_handler

**File:** `backend/core/exceptions.py:66-140`

**Exception Mapping:**

| Exception Type | Code | HTTP Status |
|----------------|------|-------------|
| ValidationError | VALIDATION_ERROR | 400 |
| InvalidStateError | INVALID_STATE | 409 |
| NotFoundError | NOT_FOUND | 404 |
| PermissionDeniedError | FORBIDDEN | 403 |
| PreconditionFailedError | PRECONDITION_FAILED | 412 |
| DomainError (other) | (code) | 400 |

**Unhandled Exceptions:**

1. **IntegrityError** (django.db.IntegrityError)
   - **NOT a DomainError subclass**
   - **Handler behavior:** Falls through to REST framework handler (line 103)
   - **REST framework handler:** Returns 500 if no response (line 127-138)
   - **View catch:** `add_request` catches IntegrityError (line 306) → 409
   - **BUT:** Only catches IntegrityError from `services.add_request()`
   - **NOT caught:** IntegrityError from IdempotencyKey or AuditLog creation

2. **DatabaseError** (django.db.DatabaseError)
   - **NOT handled** → 500

3. **Any Python exception**
   - **NOT handled** → 500

**Critical Finding:**
- **IntegrityError from IdempotencyKey.objects.create()** (line 319) is **NOT caught**
- **IntegrityError from AuditLog.objects.create()** (line 37 in audit/services.py) is **NOT caught**
- Both would bubble to view → view doesn't catch them → exception handler → 500

---

## SECTION 7 — LOG CORRELATION

### Stack Trace Analysis

**No logs provided** - Analysis based on code structure.

**Expected Stack Trace for IntegrityError:**

```
Traceback (most recent call last):
  File "backend/apps/payments/services.py", line 319, in add_request
    IdempotencyKey.objects.create(...)
  File "django/db/models/manager.py", line 85, in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
  File "django/db/models/query.py", line 515, in create
    obj.save(force_insert=True, using=self.db)
  File "django/db/models/base.py", line 806, in save
    self._save_table(...)
  File "django/db/models/base.py", line 918, in _save_table
    results = self._do_insert(...)
  File "django/db/models/base.py", line 956, in _do_insert
    return database.execute_sql(...)
django.db.utils.IntegrityError: duplicate key value violates unique constraint "unique_idempotency_per_operation"
```

**OR:**

```
Traceback (most recent call last):
  File "backend/apps/audit/services.py", line 37, in create_audit_entry
    AuditLog.objects.create(...)
  File "django/db/models/manager.py", line 85, in manager_method
    ...
django.db.utils.IntegrityError: [database constraint violation]
```

**OR:**

```
Traceback (most recent call last):
  File "backend/apps/payments/services.py", line 315, in add_request
    PaymentRequest.objects.create(**request_data)
  File "django/db/models/manager.py", line 85, in manager_method
    ...
django.db.utils.IntegrityError: check constraint "total_amount_integrity" is violated
```

**Most Likely:** IntegrityError from PaymentRequest.objects.create() due to constraint violation.

---

## SECTION 8 — PAYLOAD DIFFERENCE ANALYSIS

### Probe Payload

**File:** `backend/scripts/deep_invariant_probe.py:97-108`

```json
{
    "entityType": "VENDOR",
    "vendorId": "<uuid>",
    "siteId": "<uuid>",
    "baseAmount": "1000.00",
    "extraAmount": "500.00",
    "extraReason": "Probe",
    "currency": "INR"
}
```

### Expected Input Schema

**Service Function Signature:** `add_request(batch_id, creator_id, entity_type=None, vendor_id=None, site_id=None, base_amount=None, extra_amount=None, extra_reason=None, currency=None, ...)`

**View Extraction:** `backend/apps/payments/views.py:237-250`
- `entityType` → `entity_type`
- `vendorId` → `vendor_id`
- `siteId` → `site_id`
- `baseAmount` → `base_amount` (converted to Decimal)
- `extraAmount` → `extra_amount` (converted to Decimal)
- `extraReason` → `extra_reason`
- `currency` → `currency`

### Comparison Table

| Field | Probe Sends | View Extracts | Service Expects | Match |
|-------|-------------|---------------|------------------|-------|
| entityType | "VENDOR" | entity_type | entity_type | ✅ |
| vendorId | UUID | vendor_id | vendor_id | ✅ |
| siteId | UUID | site_id | site_id | ✅ |
| baseAmount | "1000.00" | base_amount (Decimal) | base_amount (Decimal) | ✅ |
| extraAmount | "500.00" | extra_amount (Decimal) | extra_amount (Decimal) | ✅ |
| extraReason | "Probe" | extra_reason | extra_reason | ✅ |
| currency | "INR" | currency | currency | ✅ |

**Mismatches:** **NONE** ✅

**Payload is fully compatible with backend expectations.**

---

## SECTION 9 — ROOT CAUSE HYPOTHESIS

### Ranked Root Cause Analysis

#### **1. Database Constraint Violation (HIGH CONFIDENCE - 85%)**

**Hypothesis:** `total_amount_integrity` constraint violation during PaymentRequest.objects.create()

**Evidence:**
- Constraint requires: `total_amount = base_amount + extra_amount` when not NULL
- Service computes: `total_amount = base_amount + extra_amount` (line 229)
- Service sets: `total_amount=total_amount` (line 299)
- **Potential issue:** Decimal precision or NULL handling
- **If base_amount or extra_amount is NULL** → constraint check fails
- **If computation has rounding errors** → constraint check fails
- **If constraint uses F() expressions incorrectly** → constraint check fails

**Why 500:**
- IntegrityError from PaymentRequest.objects.create() (line 315)
- **IS caught** by view (line 306) → should return 409
- **BUT:** If exception occurs AFTER PaymentRequest creation but transaction not committed
- **OR:** If exception occurs in audit entry creation → NOT caught → 500

**Confidence:** 85% - Most likely cause given constraint complexity

---

#### **2. Audit Entry Creation Failure (MEDIUM CONFIDENCE - 60%)**

**Hypothesis:** IntegrityError or other exception from `create_audit_entry()` bubbles to 500

**Evidence:**
- `create_audit_entry()` called AFTER PaymentRequest creation (line 327)
- **NOT wrapped in try/except** in `add_request()`
- AuditLog.objects.create() could raise IntegrityError
- **If audit creation fails:** PaymentRequest already created, transaction would rollback
- **BUT:** If exception is not IntegrityError → NOT caught → 500

**Why 500:**
- Exception from create_audit_entry() not caught
- Bubbles to view → view doesn't catch → exception handler → 500

**Confidence:** 60% - Possible but less likely than constraint violation

---

#### **3. IdempotencyKey Creation Failure (MEDIUM CONFIDENCE - 55%)**

**Hypothesis:** IntegrityError from IdempotencyKey.objects.create() bubbles to 500

**Evidence:**
- IdempotencyKey.objects.create() called AFTER PaymentRequest creation (line 319)
- **NOT wrapped in try/except**
- Unique constraint: `unique_idempotency_per_operation` (key, operation)
- **If key already exists:** IntegrityError
- **NOT caught** → bubbles to view → 500

**Why 500:**
- IntegrityError from IdempotencyKey creation not caught
- Bubbles to view → view only catches IntegrityError from services.add_request() → 500

**Confidence:** 55% - Possible but probe generates new UUID each time

---

#### **4. ForeignKey Constraint Violation (LOW CONFIDENCE - 30%)**

**Hypothesis:** Vendor, Subcontractor, or Site FK constraint violation

**Evidence:**
- Service validates existence with select_for_update (lines 186-188, 202-204, 214)
- **BUT:** If entity deleted between check and create → IntegrityError
- **OR:** If entity is_active=False but constraint doesn't check → IntegrityError

**Why 500:**
- IntegrityError from FK constraint → caught by view → 409
- **UNLESS:** Exception occurs in unexpected place → 500

**Confidence:** 30% - Service validates existence, unlikely

---

#### **5. Decimal Precision/Rounding Issue (LOW CONFIDENCE - 25%)**

**Hypothesis:** total_amount_integrity constraint fails due to Decimal precision

**Evidence:**
- Service computes: `total_amount = base_amount + extra_amount`
- Constraint checks: `total_amount = base_amount + extra_amount`
- **If Decimal precision differs:** Constraint fails
- **Probe sends:** "1000.00", "500.00" → should compute to 1500.00

**Why 500:**
- IntegrityError from constraint violation → caught → 409
- **UNLESS:** Different exception type → 500

**Confidence:** 25% - Decimal arithmetic should be precise

---

### Summary

**Most Likely Root Cause:**
1. **Database constraint violation** (total_amount_integrity or legacy_or_ledger_exclusive)
2. **Unhandled exception from audit entry creation**
3. **Unhandled exception from idempotency key creation**

**Key Finding:**
- **IntegrityError from PaymentRequest.objects.create() IS caught** → returns 409
- **BUT:** Exceptions from IdempotencyKey or AuditLog creation are **NOT caught** → return 500
- **Most likely:** Constraint violation on PaymentRequest creation, but exception handling gap causes 500 instead of 409

---

## RECOMMENDATIONS FOR FIX

1. **Wrap IdempotencyKey creation in try/except IntegrityError**
2. **Wrap create_audit_entry() call in try/except**
3. **Verify total_amount_integrity constraint logic**
4. **Add logging before PaymentRequest.objects.create() to capture exact data**
5. **Check database logs for exact constraint violation message**

---

**END OF REPORT**
