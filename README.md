# Internal Payment Workflow System

**MVP v1** — A structured web-based workflow for creating, submitting, and approving internal payment requests within a single company.

[![Phase 1 Certified](https://img.shields.io/badge/Phase%201-Certified-brightgreen)](#phase-1-certification) [![Architecture v0.1.0](https://img.shields.io/badge/Architecture-v0.1.0--frozen-blue)](#architecture-freeze)

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [Branch Governance](#branch-governance)
- [Governance & Certification](#governance--certification)
- [Infrastructure](#infrastructure)

---

## Overview

The Internal Payment Workflow System replaces ad-hoc payment processes (email, spreadsheets) with a centralized workflow that provides:

- **Payment batch creation** — Group requests and submit for approval
- **Role-based access** — CREATOR, APPROVER, VIEWER roles
- **Approval workflow** — Approve or reject with optional comments
- **Audit trail** — Immutable log of all domain events
- **Statement of Account (SOA)** — Versioned document attachments

| Component | Status |
|-----------|--------|
| Backend API | ✅ Complete |
| Frontend SPA | ✅ Complete |
| Docker Infrastructure | ✅ Operational |
| Phase 1 Certification | ✅ Passed |

---

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local scripts)

### Setup (5 minutes)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd internal-payment-system
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Configure required variables** — Edit `backend/.env`:
   - `SECRET_KEY` — Generate with:  
     `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `POSTGRES_PASSWORD` — Set a strong password  
   - `POSTGRES_DB` — Must match docker-compose (`internal_payments`)

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Run migrations** (if not auto-applied)
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

6. **Create a user** (for testing)
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

### Verify Installation

```bash
# Health check (correct endpoint: /api/health/)
curl http://localhost:8000/api/health/

# Expected: {"status":"ok","database":"connected","architecture_version":"v0.1.0"}
```

### Common Commands

| Action | Command |
|--------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f backend` |
| Run migrations | `docker-compose exec backend python manage.py migrate` |
| Django shell | `docker-compose exec backend python manage.py shell` |
| Database backup | `./scripts/backup_db.sh` |
| Database restore | `./scripts/restore_db.sh <backup_file>` |

See [QUICKSTART.md](QUICKSTART.md) and [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) for detailed setup and troubleshooting.

---

## Project Structure

```
internal-payment-system/
├── backend/                 # Django REST API
│   ├── apps/
│   │   ├── auth/            # Login, logout, JWT
│   │   ├── users/           # User model, /users/me, /users
│   │   ├── payments/        # Batches, requests, approval, SOA
│   │   └── audit/           # Audit log query
│   ├── core/                # Settings, middleware, permissions
│   ├── Dockerfile
│   └── manage.py
├── frontend/                # React SPA (Vite)
│   └── src/
│       ├── pages/           # Route screens
│       ├── components/      # ProtectedRoute, RoleBasedRoute
│       └── utils/           # API client, auth, error handling
├── docs/                    # Frozen specification (10 documents)
├── scripts/                 # setup.sh, backup_db.sh, restore_db.sh
├── docker-compose.yml
├── docs_check.py            # Documentation integrity
├── engineering_audit.py     # Backend discipline checks
├── phase1_certification.py  # Full Phase 1 certification
└── phase_1_12_smoke_test.py # Smoke test
```

---

## Documentation

All specifications are frozen at architecture version **v0.1.0**. Changes require formal change control.

| # | Document | Description |
|---|----------|-------------|
| 1 | [01_PRD.md](docs/01_PRD.md) | Product Requirements |
| 2 | [02_DOMAIN_MODEL.md](docs/02_DOMAIN_MODEL.md) | Domain entities and invariants |
| 3 | [03_STATE_MACHINE.md](docs/03_STATE_MACHINE.md) | PaymentRequest & PaymentBatch states |
| 4 | [04_API_CONTRACT.md](docs/04_API_CONTRACT.md) | REST API specification |
| 5 | [05_SECURITY_MODEL.md](docs/05_SECURITY_MODEL.md) | Auth, JWT, RBAC |
| 6 | [06_BACKEND_STRUCTURE.md](docs/06_BACKEND_STRUCTURE.md) | Django layout, service layer |
| 7 | [07_APP_FLOW.md](docs/07_APP_FLOW.md) | Routes, screens, visibility rules |
| 8 | [08_FRONTEND_GUIDELINES.md](docs/08_FRONTEND_GUIDELINES.md) | Frontend principles |
| 9 | [09_TECH_STACK.md](docs/09_TECH_STACK.md) | Versions, dependencies |
| 10 | [10_IMPLEMENTATION_PLAN.md](docs/10_IMPLEMENTATION_PLAN.md) | Phase sequencing |

Additional: [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) | [DOCKER_RUN.md](docs/DOCKER_RUN.md) | [ARCHITECTURE_FREEZE.md](docs/ARCHITECTURE_FREEZE.md)

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2, Django REST Framework, SimpleJWT |
| Database | PostgreSQL 15 |
| Frontend | React 18.2, Vite 5.4, Axios, React Router |
| Runtime | Python 3.11, Gunicorn |
| Infra | Docker, Docker Compose |

---

## Branch Governance

### Branch Structure

| Branch | Purpose | Rules |
|--------|---------|-------|
| `main` | Production-ready only | Protected; merges from `develop` or `hotfix/*` only via PR |
| `develop` | Integration | Default; merges from `feature/*`; must pass `docs_check.py` and `engineering_audit.py` |
| `feature/<name>` | One feature per branch | Created from `develop`; merged via PR |
| `hotfix/<issue>` | Emergency fixes | Created from `main`; merged to both `main` and `develop` |

### Workflow Rules

1. **No direct commits to main** — All changes via Pull Request
2. **All merges via PR** — No force merges; CI must pass
3. **develop requirements** — Must pass `docs_check.py`, `engineering_audit.py`, and tests
4. **Naming** — Features: `feature/PROJ-123-name`; Hotfixes: `hotfix/PROJ-456-issue`

### Architecture Freeze

**Tag:** `v0.1.0-arch-freeze`

Architecture is frozen at this tag. All changes requiring modifications to domain, API, or state machine must follow formal change control.

---

## Governance & Certification

### Pre-commit Checks

The pre-commit hook enforces:

- `docs_check.py` — Documentation integrity
- `engineering_audit.py` — Backend layering, permissions, branch/tag checks
- `black --check` — Code formatting
- `flake8` — Linting
- Blocks direct commits to `main`

### Phase 1 Certification

Run full Phase 1 certification (requires Docker and running backend):

```bash
python3 phase1_certification.py
```

Or with Docker tests skipped (e.g. CI without Docker):

```bash
python3 phase1_certification.py --skip-docker-tests
```

Smoke test (docs + engineering + health + login):

```bash
python3 phase_1_12_smoke_test.py
```

### CI Pipeline

GitHub Actions runs on PRs to `develop`:

- Docker backend build
- Migration integrity check
- `docs_check.py`, `engineering_audit.py`
- Runtime smoke (health endpoint, login)

---

## Infrastructure

- **PostgreSQL** — `postgres:15`, persistent volume `postgres_data`
- **Backend** — Django + Gunicorn on port 8000, health check via `/api/health/`
- **Scripts** — `scripts/setup.sh`, `scripts/backup_db.sh`, `scripts/restore_db.sh`

See [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) for deployment, backup, and production hardening.

---

## License & Classification

Internal Use. Single-company deployment. See [AGENT_RULEBOOK.md](AGENT_RULEBOOK.md) for AI agent constraints.
