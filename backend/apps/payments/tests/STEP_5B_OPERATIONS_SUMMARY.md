# STEP 5B — Payments Services Edge Coverage — Operations Summary

## File Created

- **`backend/apps/payments/tests/test_payments_services_edge_coverage.py`**

## Test Classes and Operations (Execution Order)

---

### 1. Version Lock Conflicts (`VersionLockConflictTests`)

Simulates **version_locked_update** returning `0` (concurrent modification) so that the service raises `InvalidStateError` instead of updating.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_approve_version_lock_conflict_raises_invalid_state` | Patch `version_locked_update` → return 0; call `services.approve_request(...)` with idempotency key | `if updated_count == 0: raise InvalidStateError(...)` in `approve_request` |
| `test_reject_version_lock_conflict_raises_invalid_state` | Patch `version_locked_update` → return 0; call `services.reject_request(...)` | Same conflict branch in `reject_request` |
| `test_mark_paid_version_lock_conflict_raises_invalid_state` | Approve request, then patch `version_locked_update` → return 0; call `services.mark_paid(...)` | Same conflict branch in `mark_paid` |

**Setup:** Creator, approver, admin; one DRAFT batch with one request; batch submitted so request is PENDING_APPROVAL (or APPROVED for mark_paid).

---

### 2. Batch Completion Logic (`BatchCompletionLogicTests`)

Covers **batch status PROCESSING → COMPLETED** and **SOA generation** trigger when all requests are terminal; idempotent skip when SOA already generated; not-found batch.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_mark_paid_when_not_all_terminal_batch_stays_processing` | Approve only `req1`; `mark_paid(req1)`. `req2` stays PENDING_APPROVAL. | `all_terminal = all(...)` is False → batch remains PROCESSING |
| `test_mark_paid_when_all_terminal_batch_completes_and_soa_generated` | Approve both req1, req2; `mark_paid(req1)` then `mark_paid(req2)`. | `batch.status == "PROCESSING"`, `all_terminal` True → batch COMPLETED, `generate_soa_for_batch(batch.id)` called |
| `test_generate_soa_for_batch_already_generated_returns_empty` | Complete batch (two mark_paids) so SOA already generated; then `generate_soa_for_batch(batch.id)`. | `has_generated` True → return `[]` |
| `test_generate_soa_for_batch_not_found_returns_empty` | `generate_soa_for_batch(uuid.uuid4())`. | `PaymentBatch.DoesNotExist` → return `[]` |

**Setup:** Batch with two requests; submit; use approver and admin.

---

### 3. Invalid State Transitions (`InvalidStateTransitionTests`)

Forces **invalid state** paths so the service raises `InvalidStateError` or `PreconditionFailedError`.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_approve_draft_request_raises_invalid_state` | `approve_request(req.id, ...)` while request still DRAFT (no submit). | `request.status != "PENDING_APPROVAL"` → raise |
| `test_approve_already_approved_raises_invalid_state` | Submit, approve once, then approve again with new idempotency key. | `request.status == "APPROVED"` → "Request has already been approved" |
| `test_reject_paid_request_raises_invalid_state` | Submit, approve, mark_paid, then `reject_request(...)`. | `request.status != "PENDING_APPROVAL"` and not REJECTED → raise |
| `test_mark_paid_rejected_request_raises_invalid_state` | Submit, reject, then `mark_paid(...)`. | `request.status != "APPROVED"` (REJECTED) → raise |
| `test_mark_paid_draft_request_raises_invalid_state` | `mark_paid(...)` on DRAFT request. | Same invalid-state branch |
| `test_submit_cancelled_batch_raises_invalid_state` | Set batch to CANCELLED (via update with submitted_at/completed_at); `submit_batch(...)`. | `batch.status != "DRAFT"` and not SUBMITTED → raise |
| `test_cancel_submitted_batch_raises_invalid_state` | Submit batch, then `cancel_batch(...)`. | `batch.status != "DRAFT"` and not CANCELLED → raise |
| `test_update_request_non_draft_raises_invalid_state` | Submit batch, then `update_request(req.id, batch.id, creator.id, amount=...)`. | `request.status != "DRAFT"` → "Cannot update request with status ..." |
| `test_submit_empty_batch_raises_precondition_failed` | Create empty batch (no requests); `submit_batch(empty.id, ...)`. | `if not requests: raise PreconditionFailedError(...)` |

---

### 4. Idempotency Replay at Service Layer (`IdempotencyReplayServiceTests`)

Same idempotency key used twice; no duplicate side effects; replay list and idempotent returns.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_approve_replay_same_key_no_duplicate_approval_record` | `approve_request(..., idempotency_key=key)` twice. | Second call: `IdempotencyKey` exists with `target_object_id` → return existing `PaymentRequest`; single `ApprovalRecord` |
| `test_approve_replay_same_key_replay_flag_set` | First approve with key; second with same key and `_idempotency_replay=[]`. | Second call appends `True` to list |
| `test_reject_replay_same_key_no_duplicate_approval_record` | `reject_request(..., idempotency_key=key)` twice. | Replay path; one `ApprovalRecord` |
| `test_mark_paid_replay_same_key_no_duplicate_paid_audit` | Approve, then `mark_paid(..., idempotency_key=key)` twice. | Replay returns existing request; one `REQUEST_PAID` audit |
| `test_submit_already_submitted_batch_raises_invalid_state` | SetUp submits batch; test calls `submit_batch(...)` again. | `batch.status == "PROCESSING"` → raise InvalidStateError |
| `test_cancel_already_cancelled_batch_returns_same_batch` | Create batch, set to CANCELLED via update; `cancel_batch(...)`. | `batch.status == "CANCELLED"` → return batch (idempotent) |

---

### 5. Permission Violations at Service Layer (`PermissionViolationServiceTests`)

Wrong role calls mutation → **PermissionDeniedError**.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_add_request_non_creator_raises_permission_denied` | `add_request(batch.id, approver.id, ...)`. | Creator check → "Only the batch creator can add requests" |
| `test_approve_request_creator_raises_permission_denied` | Submit, then `approve_request(req.id, creator.id, ...)`. | Role not APPROVER/ADMIN → raise |
| `test_reject_request_creator_raises_permission_denied` | Submit, then `reject_request(req.id, creator.id, ...)`. | Same role check in reject |
| `test_mark_paid_viewer_raises_permission_denied` | Submit, approve, then `mark_paid(req.id, viewer.id, ...)`. | Role not in CREATOR/APPROVER/ADMIN → raise |
| `test_submit_batch_non_creator_raises_permission_denied` | `submit_batch(batch.id, approver.id)`. | "Only the batch creator can submit the batch" |
| `test_cancel_batch_non_creator_raises_permission_denied` | `cancel_batch(batch.id, approver.id)`. | "Only the batch creator can cancel the batch" |
| `test_update_request_non_creator_raises_permission_denied` | `update_request(req.id, batch.id, approver.id, ...)`. | "Only the batch creator can update requests" |

---

### 6. Conflict / Validation / Not Found (`ServiceConflictAndValidationTests`)

**ValidationError**, **NotFoundError**, and **InvalidStateError** from service validations and lookups.

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_create_batch_empty_title_raises_validation_error` | `create_batch(creator.id, "")`. | `ValidationError("Title must be non-empty")` |
| `test_create_batch_whitespace_title_raises_validation_error` | `create_batch(creator.id, "   ")`. | Same validation |
| `test_create_batch_nonexistent_creator_raises_not_found` | `create_batch(uuid.uuid4(), "Title")`. | `User.DoesNotExist` → NotFoundError |
| `test_add_request_batch_not_found_raises_not_found` | `add_request(uuid.uuid4(), creator.id, ...)`. | `PaymentBatch.DoesNotExist` → NotFoundError |
| `test_add_request_negative_amount_raises_validation_error` | `add_request(..., amount=Decimal("0"), ...)`. | "Amount must be positive" (legacy path) |
| `test_update_request_not_found_raises_not_found` | `update_request(uuid.uuid4(), batch.id, creator.id, ...)`. | `PaymentRequest.DoesNotExist` → NotFoundError |
| `test_update_request_wrong_batch_raises_not_found` | `update_request(req.id, other_batch.id, creator.id, ...)`. | "does not belong to batch" → NotFoundError |
| `test_approve_request_not_found_raises_not_found` | `approve_request(uuid.uuid4(), approver.id, ...)`. | `PaymentRequest.DoesNotExist` → NotFoundError |
| `test_reject_request_not_found_raises_not_found` | `reject_request(uuid.uuid4(), approver.id, ...)`. | NotFoundError (after role check) |
| `test_mark_paid_request_not_found_raises_not_found` | `mark_paid(uuid.uuid4(), creator.id, ...)`. | `PaymentRequest.DoesNotExist` → NotFoundError |
| `test_upload_soa_no_file_raises_validation_error` | `upload_soa(batch.id, req.id, creator.id, None)`. | `ValidationError("File is required")` |
| `test_upload_soa_request_not_draft_raises_invalid_state` | Submit batch, then `upload_soa(..., ContentFile(b"fake"))`. | "Cannot upload SOA for request with status ..." |

---

### 7. Reject Idempotent When Already Rejected (`RejectIdempotentWhenAlreadyRejectedTests`)

| Test | Operation | Branch Hit |
|------|-----------|------------|
| `test_reject_already_rejected_returns_same_request` | Submit, reject once; then `reject_request(..., idempotency_key="rej-second")`. | `request.status == "REJECTED"` → update reservation, return request |

---

## Summary Counts

- **Test classes:** 8  
- **Test methods:** 42  
- **Services exercised:** `create_batch`, `add_request`, `update_request`, `submit_batch`, `cancel_batch`, `approve_request`, `reject_request`, `mark_paid`, `upload_soa`, `generate_soa_for_batch`  
- **Branches targeted:**  
  - Version lock conflict (`updated_count == 0`) in approve, reject, mark_paid  
  - Batch completion (all terminal → COMPLETED + SOA; not all terminal; already generated → `[]`)  
  - Invalid states (DRAFT/APPROVED/REJECTED/PAID/CANCELLED/PROCESSING) for approve, reject, mark_paid, submit, cancel, update, upload_soa  
  - Idempotency replay (same key → return existing, replay list, single ApprovalRecord/audit)  
  - Permission (creator vs approver vs viewer vs admin)  
  - Validation (empty title, bad amount, no file)  
  - Not found (batch, request, user)  

## Running Tests and Coverage

```bash
cd backend
POSTGRES_PORT=5433 .venv/bin/python manage.py test apps.payments.tests.test_payments_services_edge_coverage -v 2
POSTGRES_PORT=5433 .venv/bin/coverage run --branch manage.py test
POSTGRES_PORT=5433 .venv/bin/coverage report
```

Expected: all 42 tests pass; `apps/payments/services.py` branch coverage increases (target ~76–82% total project with Step 5A+5B).
