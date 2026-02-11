# Technology Stack Specification

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Scope:** Single company, internal web-only, MVP  
**Last Updated:** 2025-02-11

---

## Title and Metadata

| Field | Value |
|-------|-------|
| Document Title | Technology Stack Specification |
| Project | Internal Payment Workflow System |
| Version | 1.0 |
| Scope | MVP v1 |

---

## Runtime Environment

| Component | Version | Notes |
|-----------|---------|-------|
| OS | Ubuntu 22.04 LTS (WSL) | Development and deployment target. |
| Python | 3.11.9 | Pinned. No other Python version supported. |
| Node.js | 20.18.0 | Pinned. No other Node version supported. |
| PostgreSQL | 16.4 | Pinned. No other database version supported. |

---

## Backend Stack

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.0.10 | Web framework. |
| djangorestframework | 3.15.1 | REST API. |
| djangorestframework-simplejwt | 5.3.1 | JWT authentication. |
| psycopg2-binary | 2.9.9 | PostgreSQL adapter. |

All backend dependencies are listed in requirements.txt with exact versions. No version ranges.

---

## Frontend Stack

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.2.0 | UI library. |
| react-dom | 18.2.0 | React DOM renderer. |
| react-router-dom | 6.28.0 | Client-side routing. |
| axios | 1.7.7 | HTTP client. |
| vite | 5.4.10 | Build tool and dev server. |

All frontend dependencies are listed in package.json with exact versions. No caret (^) or tilde (~) ranges.

---

## Database Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16.4 | Primary data store. |
| Django migrations | Built-in | Schema versioning. No manual SQL. |

No Redis, Memcached, or other auxiliary stores in MVP.

---

## Authentication Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| djangorestframework-simplejwt | 5.3.1 | Access token and refresh token issuance. |
| Django auth | Built-in | User model, password hashing. |

JWT access token lifetime: 15 minutes. Refresh token lifetime: 7 days. Token rotation on refresh.

---

## Logging & Monitoring Stack

| Component | Purpose |
|-----------|---------|
| Python logging (stdlib) | Application logs. |
| Structured JSON format | Log output format. One JSON object per line. |

No third-party log aggregator in MVP. No Datadog, Splunk, or ELK. Logs written to stdout. Host-level aggregation is out of scope.

---

## Testing Stack

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | 8.3.3 | Test runner. |
| pytest-django | 4.8.0 | Django integration for pytest. |
| coverage | 7.4.1 | Code coverage measurement. |

Unit tests and integration tests use pytest. Coverage reports generated via coverage run and coverage report. No other test framework.

---

## Development Environment Standards

1. **IDE:** No prescribed IDE. Use any editor that supports Python and JavaScript.

2. **Python:** Virtual environment required. Use python -m venv or equivalent. Activate before install or run.

3. **Node:** nvm or equivalent recommended for Node version management. Exact version 20.18.0 required.

4. **PostgreSQL:** Local instance or Docker. Version 16.4 required.

5. **Pre-commit:** Optional. Not required for MVP.

---

## Dependency Management Rules

1. **Backend:** requirements.txt lists all Python dependencies with exact versions (==). No unpinned dependencies. No version ranges.

2. **Frontend:** package.json lists all dependencies with exact versions. No caret (^) or tilde (~) ranges. package-lock.json is committed and enforced. All installs use npm ci.

3. **No transitive unpinning:** All direct dependencies are pinned. Transitive dependencies are locked by pip or npm lockfile.

4. **Updates:** Dependency updates require explicit change to requirements.txt or package.json and document revision. No automated upgrade pipelines in MVP.

---

## Version Locking Policy

1. **No auto upgrades:** Dependencies are not upgraded automatically. Manual review required.

2. **Major upgrades:** Major version upgrades (e.g. Django 5 to Django 6) require architecture review and document revision. Not permitted without formal approval.

3. **Minor upgrades:** Minor version upgrades require testing and may require document revision.

4. **Patch upgrades:** Patch upgrades (e.g. 5.0.10 to 5.0.11) require testing before merge. No automatic merge.

---

## Environment Configuration Strategy

1. **.env usage:** Environment variables are loaded from .env file in development. .env is not committed. .env.example documents required variables without values.

2. **No secrets in repo:** Passwords, tokens, and API keys are never committed. All secrets supplied via environment variables or secret store at runtime.

3. **DEBUG:** DEBUG must be False in production. DEBUG is read from environment variable. Default is False.

4. **Required variables:** DJANGO_SECRET_KEY, DATABASE_URL (or individual DB vars), ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS. JWT signing key derived from DJANGO_SECRET_KEY or separate variable.

---

## Deployment Baseline

1. **Docker required:** Application is deployed using Docker. Dockerfile defines the build. No non-Docker deployment path for MVP.

2. **Single container backend:** One Docker container for the Django backend. No multi-container backend. No Celery, no separate worker containers.

3. **Separate frontend build:** Frontend is built with Vite (npm run build). Build output is served by Django static files or by a reverse proxy. No separate frontend container required if static files are served by Django.

4. **HTTPS enforced:** Production traffic must use HTTPS. HTTP redirects to HTTPS or connection is rejected. TLS termination at reverse proxy or load balancer.

5. **Database:** PostgreSQL runs in separate container or external service. Not bundled in application container.

---

## Stack Freeze Declaration

This technology stack specification is frozen for MVP v1. No runtime version, package version, or deployment baseline may be added, removed, or altered without a formal change control process and document revision.
