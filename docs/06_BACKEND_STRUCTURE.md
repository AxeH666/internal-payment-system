# Backend Structure Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Backend Structure Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |
| Framework | Django |

---

## Backend Architecture Overview

1. **Monolithic Django application:** Single Django project. No microservices. No service-to-service calls.

2. **Request flow:** HTTP Request -> Django middleware (auth, logging) -> URL routing -> View (permission check) -> Service layer -> Model layer -> Response.

3. **Layers:** View layer (HTTP handling), Service layer (business logic, state transitions, transactions), Model layer (persistence). No direct model save from views. All mutations flow through the service layer.

4. **State enforcement:** State machine validation occurs in the service layer before any model update. Status transitions are never performed by direct model save from views or management commands.

5. **Immutability:** No partial writes. No silent state mutation. No direct model save bypassing service layer. No state transition without validation.

---

## Project Structure (Folder Layout)

```
internal_payment_system/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── payments/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── state_machine.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── services.py
│   │   └── views.py
│   └── auth/
│       ├── __init__.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── core/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── permissions.py
│   ├── middleware.py
│   └── logging_config.py
└── requirements.txt
```

---

## Application Modules Definition

| App | Responsibility |
|-----|----------------|
| users | User model, user list, current user. No mutation of payment entities. |
| payments | PaymentBatch, PaymentRequest, ApprovalRecord, SOAVersion models. All payment mutations. State machine enforcement. |
| audit | AuditLog model. Audit log creation (append-only). Audit log query. |
| auth | Login, logout, token issuance. No domain logic. |
| core | Exceptions, permissions, middleware, logging. Shared utilities. |

---

## Model Definitions (Conceptual to Field Level)

### User (apps.users.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| username | CharField(150) | no | unique=True | Login identifier. |
| display_name | CharField(255) | no | | Human-readable name. |
| role | CharField(20) | no | choices=CREATOR, APPROVER, VIEWER | Role classification. |
| password | CharField(128) | no | | Hashed password. |
| created_at | DateTimeField | no | auto_now_add=True | Creation timestamp. |
| updated_at | DateTimeField | no | auto_now=True | Last update timestamp. |

**Unique constraints:** username (model-level unique=True).

**Check constraints:** role IN ('CREATOR', 'APPROVER', 'VIEWER').

---

### PaymentBatch (apps.payments.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| title | CharField(255) | no | | Batch label. |
| status | CharField(20) | no | choices | DRAFT, SUBMITTED, PROCESSING, COMPLETED, CANCELLED. |
| created_at | DateTimeField | no | auto_now_add=True | Creation timestamp. |
| created_by | ForeignKey(User) | no | on_delete=PROTECT | Creator. |
| submitted_at | DateTimeField | yes | | Set on submission. |
| completed_at | DateTimeField | yes | | Set on COMPLETED or CANCELLED. |

**Foreign keys:** created_by -> User.

**Unique constraints:** None.

**Check constraints:** status IN ('DRAFT', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'CANCELLED'); submitted_at NOT NULL when status != 'DRAFT'; completed_at NOT NULL when status IN ('COMPLETED', 'CANCELLED').

---

### PaymentRequest (apps.payments.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| batch | ForeignKey(PaymentBatch) | no | on_delete=PROTECT | Parent batch. |
| amount | DecimalField(15,2) | no | | Positive amount. |
| currency | CharField(3) | no | | Three-letter currency code. |
| beneficiary_name | CharField(255) | no | | Recipient name. |
| beneficiary_account | CharField(255) | no | | Account identifier. |
| purpose | TextField | no | | Payment purpose. |
| status | CharField(20) | no | choices | DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, PAID. |
| created_at | DateTimeField | no | auto_now_add=True | Creation timestamp. |
| created_by | ForeignKey(User) | no | on_delete=PROTECT | Creator. |
| updated_at | DateTimeField | no | auto_now=True | Last update timestamp. |
| updated_by | ForeignKey(User) | yes | on_delete=SET_NULL, null=True | Last updater. |

**Foreign keys:** batch -> PaymentBatch; created_by -> User; updated_by -> User.

**Unique constraints:** None.

**Check constraints:** status IN ('DRAFT', 'SUBMITTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PAID'); amount > 0.

---

### ApprovalRecord (apps.payments.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| payment_request | ForeignKey(PaymentRequest) | no | on_delete=PROTECT | Associated request. |
| approver | ForeignKey(User) | no | on_delete=PROTECT | Approver. |
| decision | CharField(20) | no | choices | APPROVED, REJECTED. |
| comment | TextField | yes | | Optional comment. |
| created_at | DateTimeField | no | auto_now_add=True | Decision timestamp. |

**Foreign keys:** payment_request -> PaymentRequest; approver -> User.

**Unique constraints:** One ApprovalRecord per PaymentRequest (unique constraint on payment_request).

**Check constraints:** decision IN ('APPROVED', 'REJECTED').

---

### SOAVersion (apps.payments.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| payment_request | ForeignKey(PaymentRequest) | no | on_delete=PROTECT | Associated request. |
| version_number | PositiveIntegerField | no | | Monotonically increasing per request. |
| document_reference | CharField(512) | no | | Storage path or identifier. |
| uploaded_at | DateTimeField | no | auto_now_add=True | Upload timestamp. |
| uploaded_by | ForeignKey(User) | no | on_delete=PROTECT | Uploader. |

**Foreign keys:** payment_request -> PaymentRequest; uploaded_by -> User.

**Unique constraints:** (payment_request, version_number) unique together.

**Check constraints:** version_number >= 1.

---

### AuditLog (apps.audit.models)

| Field | Type | Nullable | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | UUID | no | primary_key, default=uuid4 | Identifier. |
| event_type | CharField(50) | no | | Event classification. |
| actor | ForeignKey(User) | yes | on_delete=SET_NULL, null=True | Actor (null for system). |
| entity_type | CharField(50) | no | | Affected entity type. |
| entity_id | UUIDField | no | | Affected entity identifier. |
| previous_state | JSONField | yes | | State before change. |
| new_state | JSONField | yes | | State after change. |
| occurred_at | DateTimeField | no | auto_now_add=True | Event timestamp. |

**Foreign keys:** actor -> User.

**Unique constraints:** None.

**Check constraints:** No update or delete. Model must not expose update/delete methods in service layer.

---

## Database Constraints

1. **ForeignKey on_delete:** PROTECT for all domain FKs (User, PaymentBatch, PaymentRequest). Prevents accidental cascade delete. SET_NULL for optional updated_by. SET_NULL for optional audit actor.

2. **PaymentRequest status:** Check constraint status IN ('DRAFT', 'SUBMITTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PAID').

3. **PaymentBatch status:** Check constraint status IN ('DRAFT', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'CANCELLED').

4. **ApprovalRecord decision:** Check constraint decision IN ('APPROVED', 'REJECTED').

5. **ApprovalRecord uniqueness:** UniqueConstraint(fields=['payment_request']).

6. **SOAVersion uniqueness:** UniqueConstraint(fields=['payment_request', 'version_number']).

7. **PaymentRequest amount:** Check constraint amount > 0.

8. **User username:** UniqueConstraint(fields=['username']).

---

## Indexing Strategy

| Model | Index | Columns | Purpose |
|-------|-------|---------|---------|
| PaymentBatch | idx_batch_status | status | Filter by status. |
| PaymentBatch | idx_batch_created_by | created_by | Filter by creator. |
| PaymentRequest | idx_request_batch | batch_id | Batch lookup. |
| PaymentRequest | idx_request_status | status | Filter pending approvals. |
| PaymentRequest | idx_request_batch_status | batch_id, status | Combined filter. |
| ApprovalRecord | idx_approval_request | payment_request_id | Request lookup (unique). |
| SOAVersion | idx_soa_request | payment_request_id | Request lookup. |
| AuditLog | idx_audit_entity | entity_type, entity_id | Entity lookup. |
| AuditLog | idx_audit_occurred | occurred_at | Chronological query. |
| AuditLog | idx_audit_actor | actor_id | Actor filter. |

---

## State Machine Enforcement Layer

1. **Location:** apps.payments.state_machine.py.

2. **Allowed transitions (PaymentRequest):**
   - DRAFT -> SUBMITTED
   - SUBMITTED -> PENDING_APPROVAL
   - PENDING_APPROVAL -> APPROVED
   - PENDING_APPROVAL -> REJECTED
   - APPROVED -> PAID

3. **Allowed transitions (PaymentBatch):**
   - DRAFT -> SUBMITTED
   - SUBMITTED -> PROCESSING
   - PROCESSING -> COMPLETED
   - DRAFT -> CANCELLED

4. **Validation function:** validate_transition(entity_type, current_status, target_status) -> bool. Raises InvalidStateError if transition is disallowed.

5. **Integration:** Service layer calls validate_transition before any status change. No status change without validation.

6. **Enforcement rules:**
   - No mutation in CLOSED batch: PaymentBatch with status COMPLETED or CANCELLED rejects all mutations.
   - No mutation after PAID: PaymentRequest with status PAID rejects all mutations.
   - No mutation after REJECTED: PaymentRequest with status REJECTED rejects all mutations.

7. **Service layer:** Every mutation that changes status must: (a) call validate_transition; (b) use select_for_update; (c) perform update within transaction.atomic.

---

## Service Layer Structure

1. **Location:** apps.payments.services.py, apps.audit.services.py.

2. **Payment services:**
   - create_batch(creator_id, title) -> PaymentBatch
   - add_request(batch_id, creator_id, amount, currency, beneficiary_name, beneficiary_account, purpose) -> PaymentRequest
   - update_request(request_id, batch_id, creator_id, **fields) -> PaymentRequest
   - submit_batch(batch_id, creator_id) -> PaymentBatch
   - cancel_batch(batch_id, creator_id) -> PaymentBatch
   - approve_request(request_id, approver_id, comment=None) -> PaymentRequest
   - reject_request(request_id, approver_id, comment=None) -> PaymentRequest
   - mark_paid(request_id, actor_id) -> PaymentRequest
   - upload_soa(batch_id, request_id, creator_id, file) -> SOAVersion

3. **Audit service:** create_audit_entry(event_type, actor_id, entity_type, entity_id, previous_state, new_state) -> AuditLog.

4. **Rule:** Views never call Model.save() or Model.objects.create() directly for PaymentBatch, PaymentRequest, ApprovalRecord, SOAVersion, AuditLog. All mutations go through service functions.

---

## Transaction Boundary Mapping

| Operation | transaction.atomic | select_for_update |
|-----------|--------------------|-------------------|
| create_batch | yes | no |
| add_request | yes | PaymentBatch |
| update_request | yes | PaymentRequest |
| submit_batch | yes | PaymentBatch, all PaymentRequests (batch then requests, by id) |
| cancel_batch | yes | PaymentBatch |
| approve_request | yes | PaymentRequest |
| reject_request | yes | PaymentRequest |
| mark_paid | yes | PaymentRequest |
| upload_soa | yes | PaymentRequest |
| create_audit_entry | no (append-only, single insert) | no |

---

## Audit Integration Points

| Operation | Event Type | Entity Type | Entity ID | When |
|-----------|------------|-------------|-----------|------|
| create_batch | BATCH_CREATED | PaymentBatch | batch.id | After batch insert |
| add_request | REQUEST_CREATED | PaymentRequest | request.id | After request insert |
| update_request | REQUEST_UPDATED | PaymentRequest | request.id | After update (DRAFT only) |
| submit_batch | BATCH_SUBMITTED | PaymentBatch | batch.id | After batch status change |
| submit_batch | REQUEST_SUBMITTED | PaymentRequest | request.id | For each request in batch |
| cancel_batch | BATCH_CANCELLED | PaymentBatch | batch.id | After batch status change |
| approve_request | APPROVAL_RECORDED | PaymentRequest | request.id | After ApprovalRecord create |
| reject_request | APPROVAL_RECORDED | PaymentRequest | request.id | After ApprovalRecord create |
| mark_paid | REQUEST_PAID | PaymentRequest | request.id | After status change |
| upload_soa | SOA_UPLOADED | SOAVersion | soa.id | After SOAVersion insert |

---

## Permission Enforcement Layer

1. **Location:** core.permissions.py.

2. **Structure:** Permission classes that check request.user.role against required roles. Role is read from request.user (authenticated user from token). Role is never read from request body, query params, or headers.

3. **Permission classes:**
   - IsCreator: Allow CREATOR only.
   - IsApprover: Allow APPROVER only.
   - IsCreatorOrApprover: Allow CREATOR or APPROVER.
   - IsAuthenticatedReadOnly: Allow CREATOR, APPROVER, VIEWER for GET.

4. **Per-endpoint mapping:** Each view specifies permission_classes. Permission check runs before view logic. If check fails, return 403 Forbidden. Do not execute service layer.

5. **Ownership check:** For batch operations (submit, cancel, add_request, update_request, upload_soa), service layer validates request.user.id == batch.created_by_id or request.created_by_id. If not, raise PermissionDenied.

---

## Error Handling Layer

1. **Location:** core.exceptions.py.

2. **Exception hierarchy:**
   - DomainError (base): code, message, details.
   - ValidationError: extends DomainError, code='VALIDATION_ERROR'.
   - InvalidStateError: extends DomainError, code='INVALID_STATE'.
   - NotFoundError: extends DomainError, code='NOT_FOUND'.
   - PermissionDeniedError: extends DomainError, code='FORBIDDEN'.
   - PreconditionFailedError: extends DomainError, code='PRECONDITION_FAILED'.

3. **Standard response structure:** All domain exceptions serialize to {"error": {"code": "...", "message": "...", "details": {}}}.

4. **Exception handler middleware:** Catches DomainError subclasses. Returns 400/403/404/409/412 with standard format. Never returns stack trace.

5. **Unhandled exceptions:** Return 500 with generic message. Log full error server-side. Never expose stack trace to client.

---

## Logging Structure

1. **Format:** Structured JSON. One log line per event. Keys: timestamp, level, message, request_id, endpoint, status_code, duration_ms, user_id (optional), error_code (optional).

2. **Example:**
```json
{"timestamp": "2025-02-11T14:30:00Z", "level": "INFO", "message": "Request completed", "request_id": "abc-123", "endpoint": "/api/v1/batches", "status_code": 201, "duration_ms": 45}
```

3. **Sensitive data:** Never log passwords, tokens, full beneficiary account numbers. Redact if necessary.

4. **Separation:** Audit log (business events) stored in AuditLog table. System log (technical) written to stdout/file. Do not mix.

---

## Database Migration Discipline

1. **Rule:** All schema changes via Django migrations. No manual SQL edits to production.

2. **Process:** (a) Change models.py; (b) Run makemigrations; (c) Review generated migration; (d) Run migrate in dev; (e) Commit migration file; (f) Deploy; (g) Run migrate in production.

3. **No manual edits:** No direct ALTER TABLE, CREATE INDEX, or DROP executed outside migrations.

4. **Reversibility:** Migrations should be reversible when possible. Avoid destructive operations without explicit migration.

---

## Backend Freeze Declaration

This backend structure specification is frozen for MVP v1. No module, model, field, constraint, index, service, or transaction boundary may be added, removed, or altered without a formal change control process and document revision.

**Explicit enforcement:**

1. No partial writes.
2. No silent state mutation.
3. No direct model save bypassing service layer.
4. No state transition without validation.
5. No mutation in CLOSED batch (COMPLETED or CANCELLED).
6. No mutation after PAID (PaymentRequest).
