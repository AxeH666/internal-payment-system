# Phase 2 — Robust System Forensic Report

**Read-only structural audit. No files were modified.**

---

## SECTION 1 — REPOSITORY STRUCTURE

### Full directory tree (relevant paths; excludes .git, .venv, node_modules)

```
.
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── ci.yml
├── .pre-commit-config.yaml
├── backend/
│   ├── .dockerignore
│   ├── .env
│   ├── .flake8
│   ├── Dockerfile
│   ├── docker-compose.override.yml.example
│   ├── gunicorn.conf.py
│   ├── manage.py
│   ├── wait-for-postgres.sh
│   ├── core/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── exceptions.py
│   │   ├── health.py
│   │   ├── middleware.py
│   │   ├── permissions.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── audit/
│   │   │   ├── __init__.py, apps.py, models.py, serializers.py, services.py, urls.py, views.py
│   │   ├── auth/
│   │   │   ├── __init__.py, apps.py, serializers.py, urls.py, views.py
│   │   ├── ledger/
│   │   │   ├── __init__.py, apps.py, migrations/, models.py, serializers.py, services.py, urls.py, views.py
│   │   ├── payments/
│   │   │   ├── __init__.py, admin.py, apps.py, migrations/, models.py, serializers.py, services.py, soa_export.py, state_machine.py, urls.py, versioning.py, views.py
│   │   │   ├── management/commands/
│   │   │   │   └── reconcile_payments.py
│   │   │   └── tests/
│   │   │       ├── __init__.py, test_invariants.py
│   │   ├── users/
│   │   │   ├── __init__.py, apps.py, migrations/, models.py, serializers.py, services.py, urls.py, views.py
│   │   └── (legacy) payments/  # duplicate app name under backend/payments/ - models, admin, views, tests
│   ├── payments/   # legacy duplicate - NOT FOUND in INSTALLED_APPS as "payments"; apps.payments is used
│   ├── scripts/
│   │   ├── concurrency_stress_test.py
│   │   ├── debug_auth.py
│   │   ├── deep_invariant_probe.py
│   │   ├── enforce_service_layer.py
│   │   ├── idempotency_replay_probe.py
│   │   └── system_introspection.py
│   └── tests/
│       └── full_system_invariant_test.py
├── docs/
│   ├── 01_PRD.md, 02_DOMAIN_MODEL.md, 03_STATE_MACHINE.md, 04_API_CONTRACT.md
│   ├── 05_SECURITY_MODEL.md, 06_BACKEND_STRUCTURE.md, 07_APP_FLOW.md, 08_FRONTEND_GUIDELINES.md
│   ├── 09_TECH_STACK.md, 10_IMPLEMENTATION_PLAN.md
│   ├── ARCHITECTURE_FREEZE.md, BRANCH_PROTECTION_POLICY.md, DOCKER_RUN.md, INFRASTRUCTURE.md
├── scripts/
│   └── git-hooks/
│       └── commit-msg
├── docker-compose.yml
├── pyproject.toml
├── discipline_layer_check.py, docs_check.py, engineering_audit.py, governance_audit.py
├── phase1_certification.py, phase1_full_system_certification.py, phase_1_12_smoke_test.py
├── project_integrity_check.py
├── frontend/   (Vite/React; out of scope for this backend audit)
└── Root .md files: README.md, QUICKSTART.md, AGENT_RULEBOOK.md, ARCHITECTURE_FREEZE.md,
    TEST_FAILURE_REPORT.md, ISSUES_REPORT.md, PROJECT_REVIEW_REPORT.md, etc.
```

### Django apps and purpose

| App | Purpose |
|-----|--------|
| **apps.payments** | Payment batches, payment requests, approvals, SOA versions, idempotency keys. Core domain. |
| **apps.ledger** | Master data: Client, Site, VendorType, SubcontractorScope, Vendor, Subcontractor. |
| **apps.users** | Custom User model (UUID, role), user CRUD and auth-related helpers. |
| **apps.audit** | AuditLog model and read-only audit query API. |
| **apps.auth** | Login/logout (JWT), no domain models. |
| **core** | Settings, URLs, middleware, permissions, exceptions, health. |

**Note:** `backend/payments/` exists as a legacy duplicate (models, admin, views, tests); `INSTALLED_APPS` uses `apps.payments`, not `payments`.

### Management commands

| Command | Path | Purpose |
|---------|------|--------|
| **reconcile_payments** | `backend/apps/payments/management/commands/reconcile_payments.py` | Verifies total_amount integrity, audit log presence, FK integrity; reports errors/warnings. |

No other custom management commands under `apps.*.management.commands`. Django built-ins (e.g. `createsuperuser`) unchanged.

### Middleware

| Order | Class | Path | Purpose |
|-------|--------|------|--------|
| 1 | RequestIDMiddleware | `backend/core/middleware.py` | Injects/generates X-Request-ID on request, sets response header, sets context var for logging. |
| 2 | IdempotencyKeyMiddleware | `backend/core/middleware.py` | For POST/PATCH/PUT (excluding `/api/v1/auth/login`, `/api/health/`), requires `Idempotency-Key` header; returns 400 with VALIDATION_ERROR if missing. Sets `request.idempotency_key`. |
| 3–8 | SecurityMiddleware, SessionMiddleware, CommonMiddleware, CsrfViewMiddleware, AuthenticationMiddleware, MessageMiddleware, XFrameOptionsMiddleware | Django built-in | Standard Django stack. |

### Custom exception handlers

| Handler | Path | Behavior |
|---------|------|----------|
| **domain_exception_handler** | `backend/core/exceptions.py` | Registered as `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Handles `DomainError` subclasses → standard `{"error": {"code", "message", "details"}}` and status map (VALIDATION_ERROR→400, INVALID_STATE→409, NOT_FOUND→404, FORBIDDEN→403, PRECONDITION_FAILED→412). For other exceptions: uses DRF `exception_handler`; if still no response, logs and returns 500 INTERNAL_ERROR. Does **not** handle `IntegrityError` (views catch it and return 409). |

### Signal handlers

**NOT FOUND.** No `django.db.models.signals` or `django.dispatch` receivers in `apps/` or `core/`.

### Scripts

| Script | Path | Purpose |
|--------|------|--------|
| **deep_invariant_probe** | `backend/scripts/deep_invariant_probe.py` | HTTP probe: login, create vendor/site/batch/request (ledger-driven), then e.g. approve-without-submit (expect 409), submit, approve, mark-paid; checks invariants. |
| **concurrency_stress_test** | `backend/scripts/concurrency_stress_test.py` | 10 parallel approve calls on same request; expects 1×200, 9×409. |
| **idempotency_replay_probe** | `backend/scripts/idempotency_replay_probe.py` | Same Idempotency-Key with same body → 201 once; same key + different body → 409. |
| **debug_auth** | `backend/scripts/debug_auth.py` | Auth debugging (login/token checks). |
| **system_introspection** | `backend/scripts/system_introspection.py` | System introspection. |
| **enforce_service_layer** | `backend/scripts/enforce_service_layer.py` | Enforces service-layer usage (no direct model saves from views). |

### GitHub workflow files

| File | Triggers | Jobs |
|------|----------|------|
| **.github/workflows/ci.yml** | PR/push to `develop` | governance: build backend image, Python 3.12, install deps, `makemigrations --check --dry-run`, docs_check.py, engineering_audit.py; runtime-smoke-test: Postgres + backend container, health check, create user, login smoke test. |
| **.github/workflows/backend-ci.yml** | PR/push to `main`, `phase-2-ledger`; push to `main` | build-and-test: Postgres service, Black check, Flake8, `manage.py test`, `scripts/deep_invariant_probe.py`. |

### Config files

| File | Purpose |
|------|--------|
| **backend/.flake8** | max-line-length=88; extend-ignore E203, W503; exclude .git, pycache, build, dist, migrations, venv, .venv; backend/tests/* S101. |
| **.pre-commit-config.yaml** | black (rev 24.3.0), flake8 (rev 7.0.0), mypy (rev v1.8.0). No `args` or `files`; runs on whole repo. |
| **pyproject.toml** | [tool.black] line-length=88, target py312, exclude .venv, build, dist. |
| **backend/Dockerfile** | Backend image build. |
| **backend/docker-compose.override.yml.example** | Example override. |
| **docker-compose.yml** | Root compose. |

**mypy.ini / [tool.mypy]:** NOT FOUND. Pre-commit runs mypy without project config.

### Documentation files (project root and docs/)

Root: `README.md`, `QUICKSTART.md`, `AGENT_RULEBOOK.md`, `ARCHITECTURE_FREEZE.md`, `10_IMPLEMENTATION_PLAN.md`, `TEST_FAILURE_REPORT.md`, `ISSUES_REPORT.md`, `PROJECT_REVIEW_REPORT.md`, `FINAL_VERIFICATION_REPORT.md`, `IDEMPOTENCY_FIX_REPORT.md`, `MIGRATION_FIX_VERIFICATION.md`, `PHASE_2_VERIFICATION_REPORT.md`, `MIGRATION_FIX_VERIFICATION.md`.

docs/: `01_PRD.md`, `02_DOMAIN_MODEL.md`, `03_STATE_MACHINE.md`, `04_API_CONTRACT.md`, `05_SECURITY_MODEL.md`, `06_BACKEND_STRUCTURE.md`, `07_APP_FLOW.md`, `08_FRONTEND_GUIDELINES.md`, `09_TECH_STACK.md`, `10_IMPLEMENTATION_PLAN.md`, `ARCHITECTURE_FREEZE.md`, `BRANCH_PROTECTION_POLICY.md`, `DOCKER_RUN.md`, `INFRASTRUCTURE.md`.

---

## SECTION 2 — DOMAIN MODEL

### apps.payments

**PaymentBatch** (`backend/apps/payments/models.py`)

- **Fields:** id (UUID, PK), title (CharField 255), status (CharField 20, choices DRAFT/SUBMITTED/PROCESSING/COMPLETED/CANCELLED), created_at (auto_now_add), created_by (FK → users.User, PROTECT), submitted_at (nullable), completed_at (nullable).
- **Constraints:** CheckConstraint `valid_batch_status` (status in allowed set), `submitted_at_set_when_not_draft` (submitted_at NOT NULL when status != DRAFT), `completed_at_set_when_closed` (completed_at NOT NULL when status in COMPLETED, CANCELLED).
- **Indexes:** idx_batch_status (status), idx_batch_created_by (created_by).
- **Meta:** db_table `payment_batches`.
- **Custom save:** None.

**PaymentRequest** (`backend/apps/payments/models.py`)

- **Fields:** id (UUID, PK), batch (FK → PaymentBatch, PROTECT), amount (Decimal 15,2, nullable, MinValueValidator 0.01), currency (Char 3), beneficiary_name/account, purpose (nullable), status (choices), created_at, created_by (FK PROTECT), updated_at, updated_by (FK users.User SET_NULL, null=True), entity_type (VENDOR/SUBCONTRACTOR, null), vendor (FK ledger.Vendor PROTECT, null), subcontractor (FK ledger.Subcontractor PROTECT, null), site (FK ledger.Site PROTECT, null), base_amount, extra_amount, extra_reason, total_amount (nullable), vendor_snapshot_name, site_snapshot_code, subcontractor_snapshot_name, version (default 1), execution_id (UUID, null, db_index).
- **Constraints:** `valid_request_status` (status in set); `amount_positive` (in **model**: `amount__gt=0`; in **migration 0006**: replaced by `(amount__isnull=True) | (amount__gt=0)` — DB matches migration; model file is out of sync); `legacy_or_ledger_exclusive` (legacy vs ledger mutual exclusivity on beneficiary_name/entity_type); `vendor_or_subcontractor_exclusive` (vendor XOR subcontractor XOR both null); `total_amount_integrity` (when total_amount not null, total_amount = base_amount + extra_amount).
- **Indexes:** idx_request_batch, idx_request_status, idx_request_batch_status, idx_request_status_batch, idx_request_execution_id.
- **Meta:** db_table `payment_requests`.
- **Custom save:** None.

**ApprovalRecord** (`backend/apps/payments/models.py`)

- **Fields:** id (UUID, PK), payment_request (OneToOne PaymentRequest, PROTECT), approver (FK users.User, PROTECT), decision (APPROVED/REJECTED), comment (Text, null), created_at.
- **Constraints:** CheckConstraint `valid_decision` (decision in APPROVED, REJECTED).
- **Indexes:** idx_approval_request.
- **Custom save:** None.

**SOAVersion** (`backend/apps/payments/models.py`)

- **Fields:** id (UUID, PK), payment_request (FK PaymentRequest, PROTECT), version_number (PositiveInteger), document_reference (Char 512), source (UPLOAD/GENERATED), uploaded_at, uploaded_by (FK users.User PROTECT, null).
- **Constraints:** version_number >= 1; UniqueConstraint (payment_request, version_number) `unique_request_version`.
- **Indexes:** idx_soa_request.
- **Custom save:** None.

**IdempotencyKey** (`backend/apps/payments/models.py`)

- **Fields:** id (UUID, PK), key (Char 255, db_index), operation (Char 100), target_object_id (UUID, null), response_code (Integer, null), created_at.
- **Constraints:** UniqueConstraint (key, operation) `unique_idempotency_per_operation`.
- **Indexes:** idx_idempotency_key.
- **Custom save:** None.

### apps.ledger

**Client, Site, VendorType, SubcontractorScope, Vendor, Subcontractor** (`backend/apps/ledger/models.py`)

- All use UUID PK, is_active, effective_from, deactivated_at, created_at, updated_at where applicable.
- FKs use **on_delete=PROTECT**.
- **Client:** name unique. **Site:** code unique, client FK. **VendorType:** name unique. **SubcontractorScope:** name unique. **Vendor:** UniqueConstraint (name, vendor_type). **Subcontractor:** UniqueConstraint (name, scope); assigned_site FK nullable.
- Indexes on is_active and FKs as listed in Meta.
- No custom save/delete.

### apps.users

**User** (`backend/apps/users/models.py`)

- **Fields:** id (UUID, PK), username (Char 150, unique, RegexValidator), display_name, role (CREATOR/APPROVER/VIEWER/ADMIN), password, created_at, updated_at.
- **Constraints:** CheckConstraint `valid_role` (role in set).
- **Meta:** db_table `users`.
- **Custom:** is_staff, is_superuser, has_perm, has_module_perms delegate to `apps.users.services`.

### apps.audit

**AuditLog** (`backend/apps/audit/models.py`)

- **Fields:** id (UUID, PK), event_type (Char 50), actor (FK users.User SET_NULL, null), entity_type (Char 50), entity_id (UUID), previous_state, new_state (JSONField, null), occurred_at (auto_now_add).
- **Indexes:** idx_audit_entity (entity_type, entity_id), idx_audit_occurred (occurred_at), idx_audit_actor.
- **Custom save:** Override prevents update (if pk exists and row exists, raises ValueError). **Custom delete:** Override raises ValueError (append-only).

### Invariants: DB vs service layer

- **DB-enforced:** Batch/request status in allowed set; submitted_at/completed_at consistency (batch); amount_positive (nullable-aware in DB via migration 0006); legacy vs ledger exclusivity; vendor/subcontractor exclusivity; total_amount = base_amount + extra_amount when total_amount not null; approval decision; SOA version uniqueness; idempotency (key, operation) unique; audit log no update/delete.
- **Service-layer enforced:** State transitions (state_machine.validate_transition); batch must be DRAFT to add/cancel, SUBMITTED idempotency on submit; all requests DRAFT to submit; PENDING_APPROVAL for approve/reject; APPROVED for mark_paid; double approval prevented by ApprovalRecord + version_locked_update; creator/approver/admin role checks; ledger entity active checks; total_amount computed server-side for ledger-driven; immutability after approval (update_request only for DRAFT).

---

## SECTION 3 — SERVICE LAYER

### backend/apps/payments/services.py

| Function | transaction.atomic() | select_for_update() | DomainError subclasses | State transitions | Idempotency | Version lock |
|----------|------------------------|----------------------|------------------------|------------------|------------|-------------|
| create_batch | Yes | No | ValidationError, NotFoundError | No | No | No |
| add_request | Yes | Batch, Vendor/Subcontractor/Site (ledger) | ValidationError, NotFoundError, InvalidStateError, PermissionDeniedError | is_closed_batch, batch DRAFT | CREATE_PAYMENT_REQUEST (key→target_object_id, 201) | No |
| update_request | Yes (two blocks: one for lock+fetch, one for save) | PaymentRequest | InvalidStateError, NotFoundError, PermissionDeniedError, ValidationError | DRAFT only, is_closed_batch | No | No (DRAFT only) |
| submit_batch | Yes | Batch, then all requests in batch | NotFoundError, PermissionDeniedError, InvalidStateError, PreconditionFailedError | validate_transition for each request and batch | Idempotent: if batch SUBMITTED return batch | No |
| cancel_batch | Yes (only around save) | Batch (called **outside** atomic — see Section 7) | NotFoundError, PermissionDeniedError, InvalidStateError | DRAFT only; idempotent if CANCELLED | No | No |
| approve_request | Yes | PaymentRequest | NotFoundError, PermissionDeniedError, InvalidStateError | PENDING_APPROVAL→APPROVED | APPROVE_PAYMENT_REQUEST | version_locked_update |
| reject_request | Yes (around create+update) | PaymentRequest (called **outside** atomic — see Section 7) | Same | PENDING_APPROVAL→REJECTED | REJECT_PAYMENT_REQUEST | version_locked_update |
| mark_paid | Yes (around update) | PaymentRequest (called **outside** atomic — see Section 7) | Same | APPROVED→PAID | MARK_PAYMENT_PAID | version_locked_update |
| upload_soa | Yes (around create) | PaymentRequest (called **outside** atomic) | Same | DRAFT only | No | No |
| generate_soa_for_batch | Yes (per-request SOA create + audit) | No | No | No (idempotent skip if SOA exists) | No | No |

**Immutability after approval:** update_request checks `request.status != "DRAFT"` and raises InvalidStateError before any update; no other service updates APPROVED/PAID/REJECTED request fields.

**Financial totals:** total_amount computed in add_request as base_amount + extra_amount; DB constraint `total_amount_integrity` enforces equality when total_amount is not null. Reconcile command checks total_amount vs base_amount + extra_amount.

**Concurrency:** version_locked_update used for approve, reject, mark_paid (optimistic lock on PaymentRequest.version). select_for_update used in add_request (batch, ledger entities), submit_batch (batch + requests), and in update_request, but in cancel_batch, reject_request, mark_paid, upload_soa the select_for_update().get() is **outside** the transaction.atomic() that performs the write (see Section 7).

### backend/apps/ledger/services.py

All mutations use transaction.atomic(). select_for_update used in update_client, update_site, update_vendor, update_subcontractor (fetch inside atomic then save). create_* do not use select_for_update. DomainErrors: ValidationError, NotFoundError, PermissionDeniedError (ADMIN-only). No state machine; no idempotency keys; no version locking.

### backend/apps/users/services.py

create_user, create_superuser: no transaction.atomic() (single save). user_is_staff, user_is_superuser, user_has_perm, user_has_module_perms: read-only. No select_for_update, no DomainError, no state machine, no idempotency, no version locking.

### backend/apps/audit/services.py

create_audit_entry: no transaction.atomic() (single create). No select_for_update; no DomainError; append-only, no state/version/idempotency.

---

## SECTION 4 — STATE MACHINE

**Source:** `backend/apps/payments/state_machine.py` and docs `03_STATE_MACHINE.md`.

### PaymentRequest statuses

DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, PAID.

**Allowed transitions:**

- DRAFT → SUBMITTED, DRAFT (edit).
- SUBMITTED → PENDING_APPROVAL.
- PENDING_APPROVAL → APPROVED, REJECTED.
- APPROVED → PAID.
- REJECTED, PAID: terminal (no transitions).

**Forbidden:** Any transition not in the map (e.g. APPROVED→REJECTED, PAID→APPROVED). Validated in state_machine.validate_transition(); used in services before status change. Invalid transition raises **InvalidStateError** (code INVALID_STATE) → mapped to **409 Conflict** by domain_exception_handler.

### PaymentBatch statuses

DRAFT, SUBMITTED, PROCESSING, COMPLETED, CANCELLED.

**Allowed transitions:**

- DRAFT → SUBMITTED, CANCELLED.
- SUBMITTED → PROCESSING.
- PROCESSING → COMPLETED.
- COMPLETED, CANCELLED: terminal.

**Forbidden:** Same rule; validate_transition in services. Invalid transition → InvalidStateError → 409.

### Where transitions are validated

- submit_batch: validate_transition("PaymentRequest", ...) for each request (DRAFT→SUBMITTED, SUBMITTED→PENDING_APPROVAL); validate_transition("PaymentBatch", batch.status, "PROCESSING").
- approve_request: validate_transition("PaymentRequest", request.status, "APPROVED").
- reject_request: validate_transition("PaymentRequest", request.status, "REJECTED").
- mark_paid: validate_transition("PaymentRequest", request.status, "PAID"); and validate_transition("PaymentBatch", batch.status, "COMPLETED") when closing batch.

---

## SECTION 5 — API CONTRACT

Base path: `/api/v1`. Auth: JWT Bearer (except login/health). Idempotency: required for mutation methods (POST/PATCH/PUT) by IdempotencyKeyMiddleware, except `/api/v1/auth/login` and `/api/health/`.

| Method | URL | Headers | Idempotency | Auth | Permission | Service / behavior | Responses | Error shape |
|--------|-----|--------|-------------|------|------------|-------------------|-----------|-------------|
| POST | /api/v1/auth/login | Content-Type | No | No (AllowAny) | — | authenticate, JWT | 200, 401 | `{"error": {"code","message","details"}}` |
| POST | /api/v1/auth/logout | — | No | Yes | — | blacklist refresh | 200 | same |
| GET | /api/health/ | — | No | No | — | health_check (DB ping) | 200, 503 | JSON status/database |
| GET | /api/v1/users/me | Bearer | N/A | Yes | IsAuthenticatedReadOnly | get_current_user | 200 | data |
| GET | /api/v1/users | Bearer | N/A | Yes | IsAuthenticatedReadOnly | list_users | 200 | paginated |
| POST | /api/v1/batches | Bearer, Idempotency-Key | Required | Yes | IsCreator (manual check) | create_batch | 201, 400, 403, 409 | error |
| GET | /api/v1/batches | Bearer | N/A | Yes | IsAuthenticatedReadOnly (manual) | list batches | 200 | paginated |
| GET | /api/v1/batches/{batchId} | Bearer | N/A | Yes | IsAuthenticatedReadOnly | get_batch | 200, 404 | error |
| POST | /api/v1/batches/{batchId}/submit | Bearer, Idempotency-Key | Required | Yes | IsCreator | submit_batch | 200, 409, 403, 404, 412 | error |
| POST | /api/v1/batches/{batchId}/cancel | Bearer, Idempotency-Key | Required | Yes | IsCreator | cancel_batch | 200, 409, 403, 404 | error |
| POST | /api/v1/batches/{batchId}/requests | Bearer, Idempotency-Key | Required | Yes | IsCreator | add_request | 201, 400, 403, 404, 409 | error |
| GET | /api/v1/batches/{batchId}/requests/{requestId} | Bearer | N/A | Yes | IsAuthenticatedReadOnly / IsCreator | get_or_update_request (GET) | 200, 404 | error |
| PATCH | /api/v1/batches/{batchId}/requests/{requestId} | Bearer, Idempotency-Key | Required | Yes | IsCreator | update_request | 200, 400, 403, 404, 409 | error |
| GET | /api/v1/requests | Bearer | N/A | Yes | IsApprover | list_pending_requests | 200, 400 | error |
| GET | /api/v1/requests/{requestId} | Bearer | N/A | Yes | IsAuthenticatedReadOnly | get_request | 200, 404 | error |
| POST | /api/v1/requests/{requestId}/approve | Bearer, Idempotency-Key | Required | Yes | IsApprover | approve_request | 200, 403, 404, 409 | error |
| POST | /api/v1/requests/{requestId}/reject | Bearer, Idempotency-Key | Required | Yes | IsApprover | reject_request | 200, 403, 404, 409 | error |
| POST | /api/v1/requests/{requestId}/mark-paid | Bearer, Idempotency-Key | Required | Yes | IsCreatorOrApprover | mark_paid | 200, 403, 404, 409 | error |
| POST | /api/v1/batches/{batchId}/requests/{requestId}/soa | Bearer, Idempotency-Key | Required | Yes | IsCreator (manual) | upload_soa | 201, 400, 403, 404, 409 | error |
| GET | /api/v1/batches/{batchId}/requests/{requestId}/soa | Bearer | N/A | Yes | IsAuthenticatedReadOnly (manual) | list SOA | 200, 404 | error |
| GET | /api/v1/batches/.../soa/{versionId} | Bearer | N/A | Yes | IsAuthenticatedReadOnly | get_soa_document | 200, 404 | error |
| GET | .../soa/{versionId}/download | Bearer | N/A | Yes | IsAuthenticatedReadOnly | download_soa_document | 200, 404 | FileResponse / Http404 |
| GET | /api/v1/batches/{batchId}/soa-export | Bearer | N/A | Yes | IsAuthenticatedReadOnly | export_batch_soa_pdf/excel | 200, 400, 404 | error |
| GET/POST | /api/v1/ledger/clients | Bearer (GET/POST) | POST required | Yes | IsAuthenticatedReadOnly / IsAdmin | list_or_create_clients | 200, 201, 400, 403, 409 | error |
| PATCH | /api/v1/ledger/clients/{clientId} | Bearer, Idempotency-Key | Required | Yes | IsAdmin | update_client | 200, 400, 403, 404 | error |
| GET/POST | /api/v1/ledger/sites | Bearer | POST required | Yes | IsAuthenticatedReadOnly / IsAdmin | list_or_create_sites | 200, 201, 400, 403, 409 | error |
| PATCH | /api/v1/ledger/sites/{siteId} | Bearer, Idempotency-Key | Required | Yes | IsAdmin | update_site | 200, 400, 403, 404 | error |
| GET/POST | /api/v1/ledger/vendors | Bearer | POST required | Yes | IsAuthenticatedReadOnly / IsAdmin | list_or_create_vendors | 200, 201, 400, 403, 409 | error |
| PATCH | /api/v1/ledger/vendors/{vendorId} | Bearer, Idempotency-Key | Required | Yes | IsAdmin | update_vendor | 200, 400, 403, 404 | error |
| GET/POST | /api/v1/ledger/subcontractors | Bearer | POST required | Yes | IsAuthenticatedReadOnly / IsAdmin | list_or_create_subcontractors | 200, 201, 400, 403, 409 | error |
| PATCH | /api/v1/ledger/subcontractors/{subcontractorId} | Bearer, Idempotency-Key | Required | Yes | IsAdmin | update_subcontractor | 200, 400, 403, 404 | error |
| GET | /api/v1/ledger/vendor-types | Bearer | N/A | Yes | IsAuthenticatedReadOnly | list_vendor_types | 200 | data |
| GET | /api/v1/ledger/scopes | Bearer | N/A | Yes | IsAuthenticatedReadOnly | list_subcontractor_scopes | 200 | data |
| GET | /api/v1/audit, /api/v1/audit/logs | Bearer | N/A | Yes | IsAuthenticatedReadOnly | query_audit_log | 200, 400 | error |

**Error shape:** `{"error": {"code": "CODE", "message": "...", "details": {}}}`. Codes: VALIDATION_ERROR, INVALID_STATE, NOT_FOUND, FORBIDDEN, PRECONDITION_FAILED, CONFLICT (view-caught IntegrityError), UNAUTHORIZED (auth), INTERNAL_ERROR (unhandled).

**Tracebacks:** Unhandled exceptions go to domain_exception_handler which returns 500 with "An internal error occurred" and logs the exception; no traceback in response.

**Broad Exception in views:** get_or_update_request (PATCH) catches DomainError and maps e.code to status (INVALID_STATE→409, NOT_FOUND→404, FORBIDDEN→403, else 400); then returns Response with e.code/e.message/e.details. No bare `except Exception` in payment/ledger/audit/auth views. Scripts (debug_auth, deep_invariant_probe, concurrency_stress_test, idempotency_replay_probe, enforce_service_layer) use `except Exception` for JSON parse or control flow; health_check uses `except Exception` to return 503 — all localized and intentional.

---

## SECTION 6 — SECURITY MODEL

**Authentication:** JWT (rest_framework_simplejwt). Access token in `Authorization: Bearer <token>`. SIMPLE_JWT: ACCESS_TOKEN_LIFETIME 24h, REFRESH 7d, ROTATE_REFRESH_TOKENS, BLACKLIST_AFTER_ROTATION, AUTH_HEADER_TYPES ("Bearer"), USER_ID_FIELD id, USER_ID_CLAIM user_id. Token type from token only; role from request.user.role (from DB via JWT user_id).

**Role enum:** CREATOR, APPROVER, VIEWER, ADMIN (users.models.Role). Enforced in permission classes and in services (e.g. batch creator, APPROVER/ADMIN for approve/reject).

**Permission classes** (`backend/core/permissions.py`): IsAdmin (ADMIN only), IsCreator (CREATOR or ADMIN), IsApprover (APPROVER or ADMIN), IsCreatorOrApprover, IsAuthenticatedReadOnly (all roles for GET). Role is read only from request.user, never from body/query/headers.

**Idempotency middleware:** Requires Idempotency-Key for POST/PATCH/PUT on non-excluded paths; 400 VALIDATION_ERROR if missing; sets request.idempotency_key (passed to services where implemented).

**Global exception handler:** domain_exception_handler; unhandled exceptions logged with logger.exception, response 500 INTERNAL_ERROR; no traceback in body.

**Logging:** JSON formatter, request_id filter (RequestIDMiddleware + RequestIDFilter), LOG_LEVEL from env; django, apps, gunicorn loggers configured.

**Potential weaknesses:** Ledger update_client/update_site/update_vendor/update_subcontractor do not catch IntegrityError (Section 11). Audit API entityType filter only allows PaymentBatch, PaymentRequest — query by Client/Site/Vendor etc. returns 400 Invalid entityType. No rate limiting or CORS config visible in settings excerpt.

**Silent swallowing:** auth/views logout: `except (TokenError, ValueError): pass` for blacklist — documented as idempotent. No other broad silent swallow in views.

**Logic in views:** Views do not bypass service layer for mutations; they parse input, call services, serialize output, and catch DomainError/IntegrityError.

---

## SECTION 7 — TRANSACTIONAL SAFETY

**transaction.atomic() usage:** create_batch, add_request, submit_batch, update_request (two blocks), cancel_batch (one block around save only), approve_request, reject_request, mark_paid, upload_soa, generate_soa_for_batch; all ledger create/update functions use atomic.

**select_for_update() usage (payments):** add_request: batch, vendor/subcontractor, site. submit_batch: batch, then requests. update_request: request (inside first atomic). cancel_batch: batch **outside** atomic (lock released before atomic block). approve_request: request inside atomic. reject_request: request **outside** atomic. mark_paid: request **outside** atomic. upload_soa: request **outside** atomic. So: cancel_batch, reject_request, mark_paid, upload_soa acquire a row lock in an implicit/short transaction, then release it; the actual write happens in a later transaction.atomic() — **race window** between read and write.

**Isolation level:** reject_request and mark_paid set `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` inside the atomic block (connection.cursor().execute). Default Django/Postgres is READ COMMITTED.

**Deadlock risk:** submit_batch locks batch then requests in order (order_by id); add_request locks batch then ledger entities. Possible circular wait if other code locks in different order. No other explicit lock ordering documented.

**Version locking:** version_locked_update in approve_request, reject_request, mark_paid (PaymentRequest: filter by id, status, version; update status, updated_by, version=F("version")+1). Prevents double approval / concurrent state change when used inside the same atomic as the ApprovalRecord create and update.

**Double approval protection:** One ApprovalRecord per request (OneToOne); creation in approve/reject inside atomic with version_locked_update; idempotency key returns existing result on replay.

**Idempotency replay:** Same key + same operation returns stored response (e.g. 201/200) and existing resource; same key + different body → IntegrityError or business rule → 409 CONFLICT in views.

---

## SECTION 8 — TESTING COVERAGE

| Test file | Path | What it verifies |
|-----------|------|------------------|
| **InvariantTests** | backend/apps/payments/tests/test_invariants.py | Placeholder tests: total_amount_integrity, idempotency_prevents_duplicates, version_lock_prevents_double_approval, snapshots_required_for_ledger_driven — all `pass`. |
| **Django test suite** | backend (manage.py test) | Default Django discovery; runs InvariantTests and any other tests in apps. |
| **full_system_invariant_test** | backend/tests/full_system_invariant_test.py | Standalone script: server health, ledger (vendor, site), batch, request (ledger-driven), submit, approve, mark-paid, SOA export; uses hardcoded ADMIN token and placeholders for CREATOR/APPROVER; asserts status codes and response shape. |
| **deep_invariant_probe** | backend/scripts/deep_invariant_probe.py | HTTP probe: login, create vendor/site/batch/request, approve-without-submit (expect 409), submit, approve, mark-paid; checks invariants. Run in backend-ci after unit tests. |
| **concurrency_stress_test** | backend/scripts/concurrency_stress_test.py | 10 parallel approves; expects 1×200, 9×409. Not wired in CI (only backend-ci runs tests + deep_invariant_probe). |
| **idempotency_replay_probe** | backend/scripts/idempotency_replay_probe.py | Same key + same body → 201 once; same key + different body → 409. Not wired in CI. |

**deep_invariant_probe:** Covers create batch/request (ledger), invalid approve-before-submit, submit, approve, mark-paid. Does not cover cancel_batch, update_request, reject_request, upload_soa, or ledger CRUD in depth.

**concurrency_stress_test:** Covers concurrent approve (version lock / conflict behavior). Not in CI.

**idempotency_replay_probe:** Covers idempotency for create and (by script logic) approve. Not in CI.

**Missing/partial:** Unit tests for state_machine transitions; unit tests for version_locked_update; DB-level constraint tests (e.g. total_amount_integrity); full idempotency matrix; ledger update IntegrityError handling; audit entityType filter for ledger entities. InvariantTests are stubs.

---

## SECTION 9 — CI / GOVERNANCE

**Pre-commit hooks** (`.pre-commit-config.yaml`): black 24.3.0, flake8 7.0.0, mypy v1.8.0. No `files` or `args`; run from repo root. Flake8 config lives in `backend/.flake8`; when pre-commit runs from root, flake8 may not use backend/.flake8 (config discovery from cwd).

**Flake8:** backend/.flake8: max-line-length 88, extend-ignore E203 W503, exclude .git, pycache, build, dist, migrations, venv, .venv; backend/tests/* S101.

**Black:** pyproject.toml [tool.black] line-length 88, target py312, exclude .venv, build, dist.

**Mypy:** No mypy.ini or [tool.mypy] in repo; pre-commit runs mypy without project config.

**GitHub Actions:**  
- **ci.yml:** develop branch; governance (migrations check, docs_check, engineering_audit); runtime-smoke-test (Postgres + backend, health, login).  
- **backend-ci.yml:** main, phase-2-ledger; Black, Flake8, manage.py test, deep_invariant_probe. Python 3.11 in backend-ci (settings/default may differ).

**Branch protection (docs only):** docs/BRANCH_PROTECTION_POLICY.md — require PR, Backend CI pass, no force push, linear history, no direct push to main. Actual rules are repository settings (not in repo).

**Commit-msg:** scripts/git-hooks/commit-msg enforces pattern `^(feat|fix|refactor|chore|test|docs|perf|ci|revert)(\(.+\))?: .+`. Not automatically installed (user must install hooks).

**Freeze tags:** governance-freeze, phase-2-ledger-freeze, v0.1.0-arch-freeze.

**Enforced locally:** Pre-commit (black, flake8, mypy) if installed; commit-msg only if hook installed.

**Enforced in CI:** Black and Flake8 (backend-ci); tests and deep_invariant_probe (backend-ci); migrations check, docs_check, engineering_audit (ci.yml on develop). concurrency_stress_test and idempotency_replay_probe not in CI.

---

## SECTION 10 — GIT STATE

**Current branch:** chore/lint-cleanup

**Local branches:** chore/lint-cleanup, develop, main, phase-2-ledger, test-protection

**Remote branches:** remotes/origin/chore/lint-cleanup, develop, main, phase-2-ledger, test-protection

**Tags:** governance-freeze, phase-2-ledger-freeze, v0.1.0-arch-freeze

**Last 10 commits (oneline):**  
a18d0a0 chore(governance): strict flake8, pre-commit, backend CI, probes, branch policy  
ce86713 chore: lint cleanup — F401, E402, E501, F541; no behavior change  
5e327f1 Phase 2 ledger: views, services, probe script and override example  
e4e2de8 Fix full system invariant tests (Test 3-12)  
96cfa94 fix: improve test harness with better error handling and debugging  
0268b38 fix: correct migration syntax - add missing 'name' parameter to AddField operations  
8f02ea5 fix: CRITICAL - add idempotency key passing from views to services for all mutation endpoints  
9342c62 feat: add Phase 2 constraints, version locking, and immutable financial lock enforcement  
5d9cd3f feat: update services.py to support ledger-driven payment creation with validation, snapshots, and idempotency  
5a62f28 feat: extend PaymentRequest model with Phase 2 nullable fields (entity_type, vendor, subcontractor, site, amount breakdown, snapshots, version, execution_id)

**Untracked:** None reported by git status (only modified).

**Modified (short):** M backend/core/__pycache__/settings.cpython-312.pyc

**.pyc tracked:** backend/core/__pycache__/settings.cpython-312.pyc is **modified** (and under a path that should typically be in .gitignore). Other .pyc files under backend/ exist on disk but are not listed in git status as staged/committed; one .pyc is in the index (modified).

---

## SECTION 11 — FAILURE SURFACE ANALYSIS

**Places that can still produce 500:**

1. **Uncaught IntegrityError in views:** Ledger **update** endpoints (update_client, update_site, update_vendor, update_subcontractor) catch DomainError and re-raise but do **not** catch IntegrityError. A unique constraint or FK violation during update would propagate to the global handler and return 500 INTERNAL_ERROR. Payments and ledger **create** endpoints do catch IntegrityError and return 409 CONFLICT.

2. **Unhandled exceptions in service layer:** Any non-DomainError exception (e.g. OperationalError, ProgrammingError) raised inside a service and not caught in the view will be handled by the global exception handler and return 500 (and be logged). Views that only `except DomainError: raise` and `except IntegrityError: ...` do not catch other DB or runtime errors.

3. **health_check:** Catches Exception and returns 503 with JSON; does not return 500. So health is safe.

4. **download_soa_document:** Catches OSError by raising Http404; other exceptions would propagate and could become 500 unless DRF or middleware catches them.

**Missing IntegrityError handling:** Ledger PATCH views (update_client, update_site, update_vendor, update_subcontractor) do not have `except IntegrityError`; they only have `except DomainError: raise`. So DB integrity violations on update → 500.

**Race window:** cancel_batch, reject_request, mark_paid, upload_soa use select_for_update().get() **outside** the transaction.atomic() that performs the write. Another transaction can modify the row between the lock release and the write. Version locking in approve/reject/mark_paid mitigates concurrent approval but the initial lock is not held across the full operation in those three.

**Service layer bypass:** No views perform model.save() or create() directly for payment/ledger/audit mutations; they call services. So no bypass found.

**Error code mapping:** DomainError codes map consistently (INVALID_STATE→409, etc.). IntegrityError in payment/ledger create and payment mutation views is mapped to CONFLICT and 409. Ledger update views do not map IntegrityError (they don’t catch it). Audit view validates entityType and returns 400 for invalid; entityType allowed set is only PaymentBatch, PaymentRequest (not Client, Site, etc.).

---

## SECTION 12 — ARCHITECTURAL MATURITY SCORE

**Domain separation (7/10):** Clear app boundaries (payments, ledger, users, audit, auth). Services encapsulate mutations; views are thin. Legacy `backend/payments/` duplicate and model file vs migration 0006 for amount_positive slightly blur consistency.

**Transaction safety (6/10):** Widespread use of transaction.atomic() and version_locked_update for critical flows; but select_for_update in cancel_batch, reject_request, mark_paid, upload_soa is not inside the same atomic as the write, leaving a race window. REPEATABLE READ used in reject_request and mark_paid.

**Error mapping consistency (7/10):** Standard error shape and DomainError→status mapping; IntegrityError→409 on create/mutation views. Ledger update views omit IntegrityError handling and can surface 500.

**CI discipline (7/10):** backend-ci runs Black, Flake8, tests, deep_invariant_probe; ci.yml runs migrations check, docs_check, engineering_audit and smoke test. concurrency_stress_test and idempotency_replay_probe not in CI; Python version mismatch (3.11 in backend-ci vs 3.12 in ci.yml).

**Test robustness (5/10):** InvariantTests are stubs; full_system_invariant_test and probes provide scenario coverage but depend on tokens/env; no unit tests for state machine or version locking; idempotency and concurrency probes not in CI.

**Governance enforcement (6/10):** Pre-commit and commit-msg documented; branch protection and Backend CI required by policy doc. Commit-msg hook not auto-installed; pre-commit flake8 may not use backend/.flake8 when run from root.

**Production readiness (6/10):** Strong points: JWT, roles, idempotency, audit log, no traceback leak. Gaps: ledger update 500 on IntegrityError, select_for_update/atomic ordering in four service functions, one .pyc modified in repo, and optional hardening (rate limit, CORS, full probe coverage in CI).

---

*End of Phase 2 Detailed Forensic Report. No files were modified.*
