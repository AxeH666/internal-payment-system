# Implementation Plan Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Implementation Plan Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |

---

## Implementation Philosophy

1. **Bottom-up:** Backend before frontend. Models before services. Services before views. No skipping layers.

2. **Document alignment:** Every implementation step corresponds to a frozen specification. No entity without domain model. No endpoint without API contract. No state without state machine.

3. **Verification per phase:** Each phase completes before the next begins. Integration tests run before hardening. Hardening completes before deployment.

4. **No speculative phases:** Only MVP v1 scope. No Phase 2, Phase 3, or future roadmap in this document.

---

## Branch Strategy Introduction Point

The develop branch is introduced at the start of Phase 2 (Backend Implementation Sequence). Phase 1 (project initialization) may occur on main or a single initialization branch. From Phase 2 onward, all work occurs on feature branches merging into develop. develop merges to main only at release milestones.

---

## Backend Implementation Sequence

### Phase 2.1: Project Initialization

1. Initialize Django project (django-admin startproject).
2. Create config/ structure. Configure settings.py for PostgreSQL.
3. Create apps/ directory. Create apps/users, apps/payments, apps/audit, apps/auth, core.
4. Add apps to INSTALLED_APPS. Configure database connection from environment.

### Phase 2.2: User Model and Authentication

1. Create custom User model in apps.users.models. Fields: id (UUID), username, display_name, role, password, created_at, updated_at. Username unique. Role choices CREATOR, APPROVER, VIEWER.
2. Configure AUTH_USER_MODEL.
3. Implement authentication: install djangorestframework-simplejwt. Configure JWT settings (access 15 min, refresh 7 days). Implement login view (POST /api/v1/auth/login). Implement logout view (POST /api/v1/auth/logout).
4. Implement users/me view (GET /api/v1/users/me). Implement users list view (GET /api/v1/users).

### Phase 2.3: Models

1. Implement PaymentBatch model. Fields: id, title, status, created_at, created_by, submitted_at, completed_at. ForeignKey created_by -> User. Status choices DRAFT, SUBMITTED, PROCESSING, COMPLETED, CANCELLED.
2. Implement PaymentRequest model. Fields: id, batch, amount, currency, beneficiary_name, beneficiary_account, purpose, status, created_at, created_by, updated_at, updated_by. ForeignKeys batch, created_by, updated_by. Status choices DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, PAID.
3. Implement ApprovalRecord model. Fields: id, payment_request, approver, decision, comment, created_at. UniqueConstraint payment_request.
4. Implement SOAVersion model. Fields: id, payment_request, version_number, document_reference, uploaded_at, uploaded_by. UniqueConstraint (payment_request, version_number).
5. Implement AuditLog model. Fields: id, event_type, actor, entity_type, entity_id, previous_state, new_state, occurred_at.
6. Add database constraints: CheckConstraint for status fields, amount > 0, version_number >= 1.
7. Run makemigrations. Run migrate.

### Phase 2.4: State Machine Enforcement Integration

1. Implement apps.payments.state_machine. Define validate_transition(entity_type, current_status, target_status). Implement allowed transition maps for PaymentRequest and PaymentBatch.
2. Raise InvalidStateError for disallowed transitions. Enforce: no mutation in CLOSED batch, no mutation after PAID, no mutation after REJECTED.
3. Integrate validate_transition into all service layer calls that change status.

### Phase 2.5: Permission Layer

1. Implement core.permissions. Create IsCreator, IsApprover, IsCreatorOrApprover, IsAuthenticatedReadOnly permission classes.
2. Role is read from request.user (authenticated via JWT). Never from request body or headers.
3. Apply permission_classes to each view per API contract.

### Phase 2.6: Service Layer

1. Implement apps.payments.services: create_batch, add_request, update_request, submit_batch, cancel_batch, approve_request, reject_request, mark_paid, upload_soa.
2. Implement apps.audit.services: create_audit_entry.
3. All mutations flow through service layer. Views never call Model.save() or Model.objects.create() directly for domain entities.

### Phase 2.7: Audit Integration

1. Add create_audit_entry calls at each mutation point per Audit Integration Points in backend structure.
2. Event types: BATCH_CREATED, REQUEST_CREATED, REQUEST_UPDATED, BATCH_SUBMITTED, REQUEST_SUBMITTED, BATCH_CANCELLED, APPROVAL_RECORDED, REQUEST_PAID, SOA_UPLOADED.

### Phase 2.8: Transaction Boundaries

1. Wrap submit_batch, cancel_batch, add_request, update_request, approve_request, reject_request, mark_paid, upload_soa in transaction.atomic.
2. Add select_for_update for PaymentBatch and PaymentRequest where specified in Transaction Boundary Mapping.
3. Lock ordering: batch before requests, by identifier.

### Phase 2.9: Idempotency Handling

1. Implement idempotent behavior for submit_batch: if batch already SUBMITTED, return success without re-submitting.
2. Implement idempotent behavior for approve/reject: if ApprovalRecord exists, return success without duplicate.
3. Implement idempotent behavior for mark_paid: if request already PAID, return success.

### Phase 2.10: API Views and URL Routing

1. Implement all endpoints per API contract. Wire views to service layer. Apply serializers. Apply permissions.
2. Implement standard error format. Implement exception handler for DomainError subclasses.

### Phase 2.11: Integration Tests

1. Add pytest-django. Write integration tests for each API endpoint.
2. Test success paths. Test permission denial (403). Test invalid state (409). Test not found (404).

---

## State Machine Enforcement Integration Phase

This phase is embedded in Phase 2.4 above. The state machine module (apps.payments.state_machine) is implemented before any service that performs status transitions. All services that change status call validate_transition before performing the update.

---

## Security Integration Phase

This phase is distributed across Phase 2.2 (authentication), Phase 2.5 (permissions), and Phase 2.9 (idempotency). No separate security phase. JWT configuration, permission checks, and role enforcement are implemented as part of the backend sequence.

---

## Frontend Implementation Sequence

### Phase 3.1: Project Setup

1. Initialize React project with Vite. Configure for React 18.2.0.
2. Install react-router-dom, axios. Configure base URL for API.
3. Create route structure: /login, /, /batches, /batches/new, /batches/:batchId, /batches/:batchId/requests/:requestId, /requests, /requests/:requestId, /audit.

### Phase 3.2: Auth Flow

1. Implement login screen. POST /api/v1/auth/login. Store token. Redirect to / on success.
2. Implement logout. POST /api/v1/auth/logout. Clear token. Redirect to /login.
3. Implement token storage. Attach token to axios Authorization header.

### Phase 3.3: Route Protection

1. Implement protected route wrapper. Check token. Redirect to /login if missing.
2. Implement role-based redirect. GET /api/v1/users/me. Redirect CREATOR/VIEWER to /batches. Redirect APPROVER to /requests.
3. Hide routes for unauthorized roles. Redirect to / if user navigates to forbidden route.

### Phase 3.4: Batch Screens

1. Implement /batches list. GET /api/v1/batches. Display table. Link to /batches/:batchId. Link to /batches/new (CREATOR only).
2. Implement /batches/new. POST /api/v1/batches. Redirect to /batches/:batchId on success.
3. Implement /batches/:batchId. GET /api/v1/batches/:batchId. Display batch and requests. Submit, Cancel, Add Request buttons per State-Based UI Visibility Rules.

### Phase 3.5: Payment Actions

1. Implement add request form. POST /api/v1/batches/:batchId/requests.
2. Implement update request form. PATCH /api/v1/batches/:batchId/requests/:requestId. Only when DRAFT.
3. Implement submit batch. POST /api/v1/batches/:batchId/submit.
4. Implement cancel batch. POST /api/v1/batches/:batchId/cancel.
5. Implement approve, reject, mark paid. POST /api/v1/requests/:requestId/approve, reject, mark-paid. Visibility per State-Based UI Visibility Rules.

### Phase 3.6: SOA Screens

1. Implement SOA upload. POST /api/v1/batches/:batchId/requests/:requestId/soa (multipart). Only when request DRAFT.
2. Implement SOA list. GET /api/v1/batches/:batchId/requests/:requestId/soa.
3. Implement SOA download. GET /api/v1/batches/:batchId/requests/:requestId/soa/:versionId. Fetch downloadUrl.

### Phase 3.7: Approval Queue Screens

1. Implement /requests list. GET /api/v1/requests?status=PENDING_APPROVAL.
2. Implement /requests/:requestId. Display request. Approve, Reject, Mark Paid per visibility rules.

### Phase 3.8: Audit Screen

1. Implement /audit. GET /api/v1/audit with optional filters. Display results. Paginate.

### Phase 3.9: Error Handling

1. Implement standardized error parsing. Parse {"error": {"code": "...", "message": "...", "details": {}}}.
2. Display error.message. Handle 401: clear token, redirect to /login. Handle 403: display message. Handle 404: display message, offer back navigation. Handle 409: trigger reload behavior.

### Phase 3.10: Concurrency Reload Logic

1. On 409 CONFLICT or INVALID_STATE: discard local state, re-fetch entity (GET batch or GET request), refresh screen, display conflict message.
2. No automatic retry. User must re-initiate action.

---

## Integration Testing Phase

1. Run backend integration tests. Verify all endpoints.
2. Run frontend manually against backend. Verify full flow: login, create batch, add request, submit, approve, mark paid.
3. Verify permission denial for VIEWER on mutation endpoints.
4. Verify CLOSED batch disables actions. Verify PAID disables actions.

---

## Hardening Phase

### Phase 5.1: Concurrency Simulation Tests

1. Write test: two concurrent approve requests for same PaymentRequest. Verify only one succeeds. Verify no duplicate ApprovalRecord.
2. Write test: concurrent submit and cancel. Verify one succeeds, one fails with 409.

### Phase 5.2: Duplicate Submission Tests

1. Write test: submit batch twice. Verify second returns success without duplicate transition. Verify no duplicate AuditLog.
2. Write test: approve request twice. Verify second returns success without duplicate ApprovalRecord.

### Phase 5.3: Permission Abuse Tests

1. Write test: VIEWER attempts POST /api/v1/batches. Verify 403.
2. Write test: APPROVER attempts submit batch (CREATOR only). Verify 403.
3. Write test: CREATOR attempts approve (APPROVER only). Verify 403.

### Phase 5.4: Closed Batch Mutation Tests

1. Write test: attempt add request to COMPLETED batch. Verify 409 or 412.
2. Write test: attempt submit CANCELLED batch. Verify 409.

### Phase 5.5: Paid Mutation Tests

1. Write test: attempt mark paid on already PAID request. Verify idempotent success.
2. Write test: attempt approve on PAID request. Verify 403 or 409.

### Phase 5.6: SOA Version Increment Tests

1. Write test: upload two SOAs to same request. Verify version_number 1 and 2. Verify UniqueConstraint.
2. Write test: attempt SOA upload when request not DRAFT. Verify 409.

---

## Deployment Preparation Phase

1. Create Dockerfile for Django backend. Single container. Install requirements. Collect static. Run gunicorn or uwsgi.
2. Build frontend. npm run build. Serve static from Django or nginx.
3. Configure environment variables. No secrets in image.
4. Configure HTTPS. TLS termination at reverse proxy.
5. Verify DEBUG=False in production settings.

---

## Merge & Release Strategy

1. **Branch workflow:** Feature branches merge to develop. No direct commits to main.
2. **Main protected:** main accepts merges only from develop. No force push.
3. **Tag architecture freeze:** Tag v0.1.0-arch-freeze when documents 01-09 are finalized.
4. **Tag MVP release:** Tag v1.0.0-mvp when all phases complete, hardening passes, deployment succeeds.

---

## Implementation Guardrails

1. **No new entity without domain update:** Do not add a model that is not in 02_DOMAIN_MODEL.md. Document change required first.

2. **No new endpoint without API contract update:** Do not add an API endpoint that is not in 04_API_CONTRACT.md. Document change required first.

3. **No new state without state machine update:** Do not add a status value that is not in 03_STATE_MACHINE.md. Document change required first.

4. **No permission bypass:** Every mutation endpoint must enforce permission. No endpoint may skip permission check.

5. **No model mutation outside service layer:** Views must not call Model.save(), Model.objects.create(), or Model.objects.update() for PaymentBatch, PaymentRequest, ApprovalRecord, SOAVersion, AuditLog. All mutations through service layer.

6. **No direct DB edits:** All schema changes via Django migrations. No manual ALTER TABLE, CREATE INDEX, or raw SQL in production.

---

## Implementation Freeze Declaration

This implementation plan specification is frozen for MVP v1. No phase, step, or guardrail may be added, removed, or altered without a formal change control process and document revision.
