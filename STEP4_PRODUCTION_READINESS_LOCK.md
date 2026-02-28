# STEP 4 — Production Readiness Lock

**Phase 2 Controlled Execution Plan — Verification Artifact**

**Date:** 2025-02-20

---

## 1. CI migration drift check

**Workflow:** [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml)

**Change:** Added a step **Migration drift check** after **Install dependencies** and before **Black check**. The step runs:

```bash
cd backend
python manage.py makemigrations --check --dry-run
```

with env: `DJANGO_SETTINGS_MODULE=core.settings`, `SECRET_KEY`, `DEBUG=True`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB=testdb`.

**Result:** PRs and pushes to `main` and `phase-2-ledger` will fail CI if there are uncommitted model changes (migration drift).

---

## 2. Authority smoke test

**Location:** [backend/apps/users/tests.py](backend/apps/users/tests.py)

**Test:** `AuthoritySmokeTests.test_cannot_create_admin_via_api`

- Creates an ADMIN user via `User.objects.create_superuser` (shell/superuser path).
- Obtains JWT via `POST /api/v1/auth/login`.
- Calls `POST /api/v1/users/` with `role=ADMIN` and `Idempotency-Key` header.
- Asserts status 400 and response contains “Cannot create ADMIN users via API”.
- Asserts no user with the attempted username was created.

**CI:** Run as part of `python manage.py test` in backend-ci (existing **Run Tests** step). No separate step required.

---

## 3. Transaction / state machine smoke flow

**Script:** [backend/scripts/deep_invariant_probe.py](backend/scripts/deep_invariant_probe.py)

**Flow covered:** Create vendor → create site → create batch → add request → (attempt approve without submit; expect failure) → submit batch → approve request → **mark_paid** (added in Step 4) → (attempt PATCH after approval; expect failure).

This is the **transaction/state-machine smoke flow**: create batch → add request → submit → approve → mark_paid, with state-machine and idempotency checks.

**CI:** Run in backend-ci. The workflow was updated so that before the probe: **Run migrations** applies migrations to the test DB, **Create admin user** ensures an admin user exists for login, and **Start backend server** runs `python manage.py runserver 8000` in the background. The **Deep Invariant Probe** step then runs with `BASE_URL=http://127.0.0.1:8000`, `E2E_USERNAME=admin`, `E2E_PASSWORD=admin`.

---

## 4. Admin creation runbook

**Location:** [docs/ADMIN_CREATION_RUNBOOK.md](docs/ADMIN_CREATION_RUNBOOK.md)

**Contents:** How to create the first ADMIN user via `python manage.py shell` and `User.objects.create_superuser(username=..., password=...)`. States that no API or UI can create ADMIN and that at least one ADMIN should be ensured by operational procedures.

---

## 5. Docker and env readiness

**Docker Compose:** [docker-compose.yml](docker-compose.yml)

- **postgres:** image postgres:15, env `POSTGRES_DB=internal_payments`, `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`, healthcheck `pg_isready`.
- **backend:** build `./backend`, depends on postgres healthy, `env_file: ./backend/.env`, override `ALLOWED_HOSTS=localhost,127.0.0.1,backend`, ports 8000:8000, healthcheck `curl -fsS http://localhost:8000/api/health/`.

**Backend env:** [backend/.env.example](backend/.env.example) documents:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` for DB connectivity.
- Copy to `backend/.env` for local runs; root `.env` for Docker Compose if needed.

**Required for backend:** `SECRET_KEY` (required by settings), `POSTGRES_*` for DB. `ALLOWED_HOSTS` is set in compose for the backend service. Health endpoint: `/api/health/` (used by backend service healthcheck).

**Conclusion:** Docker and env are sufficient for running backend + Postgres; required vars and health check are documented and in use.

---

## 6. Summary and declaration

| Item | Status |
|------|--------|
| CI migration drift check | Added in backend-ci |
| Authority smoke test | Added in apps.users.tests; runs with manage.py test |
| Transaction/state-machine flow | deep_invariant_probe extended with mark_paid; runs in backend-ci |
| Admin creation runbook | docs/ADMIN_CREATION_RUNBOOK.md added |
| Docker + env | Confirmed and documented above |

**Final declaration:** **PASS**

Migration drift check runs in CI. Authority smoke test exists and is part of the test suite. Transaction/state-machine flow (probe) extended and run in CI. Runbook exists. Docker and env confirmed and documented.
