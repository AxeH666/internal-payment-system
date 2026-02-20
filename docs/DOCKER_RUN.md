# Phase 1.8 — Docker & PostgreSQL: Run Instructions

## Prerequisites

- Docker and Docker Compose installed
- Fresh clone of the repository

## Exact Run Instructions

### 1. Create `.env` at project root

From the project root (where `docker-compose.yml` lives):

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set values for:
- `POSTGRES_PASSWORD` (required)
- `SECRET_KEY` (required)

Do not commit `backend/.env`.

### 2. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 3. Verify container and health

```bash
docker-compose ps
docker-compose exec postgres pg_isready -U postgres -d internal_payment
```

Expected: `internal_payment:5432 - accepting connections`

### 4. (Optional) Run with pgAdmin

```bash
# Set PGADMIN_EMAIL and PGADMIN_PASSWORD in .env, then:
docker-compose --profile tools up -d
```

pgAdmin: http://localhost:5050

## Stop and data persistence

```bash
docker-compose down
```

Data persists in the named volume `postgres_data`. Restart with `docker-compose up -d postgres` to keep using the same data.

## Determinism and restart

- Image: `postgres:15` (fixed version)
- All credentials from `.env`; none in `docker-compose.yml`
- Restart policy: `unless-stopped`
- Volume: `postgres_data` (named, persistent)
