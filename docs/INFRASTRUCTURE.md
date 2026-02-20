# Infrastructure Documentation

**Project:** Internal Payment Workflow System (MVP v1)  
**Document Version:** 1.0  
**Owner:** INFRA_ENGINEER  
**Last Updated:** 2025-02-12

---

## Overview

This document describes the infrastructure setup, deployment procedures, and operational requirements for the Internal Payment Workflow System. All infrastructure follows DevOps best practices with a focus on reproducibility, security, and environment parity.

---

## Core Principles

1. **Docker-based PostgreSQL from Day 1** - No SQLite fallback, PostgreSQL is mandatory
2. **.env based configuration** - All configuration via environment variables
3. **No secrets in code** - All secrets must come from environment variables
4. **Deterministic migrations** - All database changes via Django migrations
5. **Reproducible setup** - One command to get running
6. **Environment parity** - Local and production use identical configuration

---

## Architecture

### Services

The system consists of two main services:

1. **PostgreSQL Database** (`postgres`)
   - Version: 16.4 (pinned)
   - Port: 5432
   - Persistent volume: `postgres_data`
   - Health checks enabled

2. **Django Backend** (`backend`)
   - Python 3.11.9
   - Django 4.2.11
   - Gunicorn WSGI server
   - Port: 8000
   - Health check endpoint: `/health/`

### Network

- All services run on `internal-payment-network` bridge network
- Services communicate via service names (e.g., `postgres`)

### Volumes

- `postgres_data`: PostgreSQL data persistence
- `static_volume`: Static files
- `media_volume`: Media files

---

## Environment Configuration

### Required Environment Variables

All configuration is done via `.env` file. Copy `.env.example` to `.env` and configure:

#### Critical (No Defaults)

- `SECRET_KEY`: Django secret key (required)
- `POSTGRES_PASSWORD`: Database password (required)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (required in production)

#### Database

- `POSTGRES_DB`: Database name (default: `internal_payment`)
- `POSTGRES_USER`: Database user (default: `postgres`)
- `POSTGRES_HOST`: Database host (`postgres` for docker-compose, `localhost` for local)
- `POSTGRES_PORT`: Database port (default: `5432`)

#### Application

- `DEBUG`: Debug mode (`True`/`False`, default: `False`)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `LOG_FORMAT`: Log format (`json` or `text`)

#### Production Security

- `HTTPS_ENFORCED`: Enforce HTTPS (`True`/`False`)
- `SECURE_SSL_REDIRECT`: Redirect HTTP to HTTPS
- `SESSION_COOKIE_SECURE`: Secure session cookies
- `CSRF_COOKIE_SECURE`: Secure CSRF cookies

### Environment Variable Validation

The application **will not start** if required variables are missing. No fallbacks or defaults for:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST`

---

## Setup Instructions

### Prerequisites

- Docker 20.10+
- docker-compose 2.0+
- Bash shell

### Initial Setup

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd internal-payment-system
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set all required values
   ```

3. **Generate SECRET_KEY**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Run setup script**
   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

5. **Start services**
   ```bash
   docker-compose up -d
   ```

6. **Run migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

7. **Create superuser** (optional)
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

### Verification

Check health endpoint:
```bash
curl http://localhost:8000/health/
```

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "config": "healthy"
  }
}
```

---

## Database Management

### Migrations

All database changes must go through Django migrations:

```bash
# Create migration
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Check migration status
docker-compose exec backend python manage.py showmigrations
```

**Rule:** No manual SQL changes. All schema changes via migrations.

### Backups

#### Create Backup

```bash
./scripts/backup_db.sh [backup_directory]
```

Backups are:
- Timestamped: `backup_YYYYMMDD_HHMMSS.sql.gz`
- Stored in `./backups/` by default
- Automatically cleaned up after 30 days

#### Restore Backup

```bash
./scripts/restore_db.sh backups/backup_20250212_120000.sql.gz
```

**WARNING:** Restore will overwrite the current database!

### Backup Schedule

- **Development:** Manual backups before major changes
- **Production:** Daily automated backups (configure via cron/systemd)

Example cron job:
```cron
0 2 * * * /path/to/scripts/backup_db.sh /backups/production
```

---

## Logging

### Log Format

Logs are structured JSON by default (configurable via `LOG_FORMAT`):

```json
{
  "timestamp": "2025-02-12T12:00:00+00:00",
  "level": "INFO",
  "logger": "apps.payments",
  "message": "Payment request created",
  "module": "views",
  "function": "create_payment",
  "line": 42
}
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Accessing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] `.env` configured with production values
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` includes production domain
- [ ] `HTTPS_ENFORCED=True` in production
- [ ] `SECRET_KEY` is strong and unique
- [ ] `POSTGRES_PASSWORD` is strong and unique
- [ ] Database backup plan in place
- [ ] Health check endpoint accessible
- [ ] Logs are being collected and monitored

### Deployment Steps

1. **Backup database**
   ```bash
   ./scripts/backup_db.sh /backups/pre-deployment
   ```

2. **Pull latest code**
   ```bash
   git pull origin main
   ```

3. **Rebuild containers**
   ```bash
   docker-compose build backend
   ```

4. **Run migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Collect static files**
   ```bash
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

6. **Restart services**
   ```bash
   docker-compose up -d
   ```

7. **Verify health**
   ```bash
   curl https://your-domain.com/health/
   ```

### Rollback Procedure

1. **Stop services**
   ```bash
   docker-compose down
   ```

2. **Restore database backup**
   ```bash
   ./scripts/restore_db.sh /backups/pre-deployment/backup_*.sql.gz
   ```

3. **Checkout previous code version**
   ```bash
   git checkout <previous-commit>
   ```

4. **Restart services**
   ```bash
   docker-compose up -d
   ```

---

## Security Hardening

### Production Requirements

1. **HTTPS Enforcement**
   - Set `HTTPS_ENFORCED=True`
   - Configure reverse proxy (nginx/traefik) for TLS termination
   - Redirect HTTP to HTTPS

2. **Secrets Management**
   - Never commit `.env` to version control
   - Use secret management service in production (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Rotate secrets regularly

3. **Database Security**
   - Use strong passwords
   - Restrict database access to application network only
   - Enable SSL connections in production

4. **Application Security**
   - `DEBUG=False` in production
   - `ALLOWED_HOSTS` properly configured
   - Security headers enabled
   - CSRF protection enabled

---

## Monitoring

### Health Checks

Health check endpoint: `GET /health/`

Returns:
- `200`: All checks passing
- `503`: One or more checks failing

Checks performed:
- Database connectivity
- Critical configuration

### Log Monitoring

Monitor logs for:
- Error rates
- Database connection issues
- Authentication failures
- Payment processing errors

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d internal_payment
```

### Application Won't Start

1. Check environment variables:
   ```bash
   docker-compose config
   ```

2. Check logs:
   ```bash
   docker-compose logs backend
   ```

3. Verify `.env` file exists and is properly formatted

### Migration Issues

```bash
# Check migration status
docker-compose exec backend python manage.py showmigrations

# Fake migration if needed (use with caution)
docker-compose exec backend python manage.py migrate --fake <app_name> <migration_name>
```

---

## Maintenance

### Regular Tasks

- **Daily:** Verify backups are created
- **Weekly:** Review logs for errors
- **Monthly:** Test restore procedure
- **Quarterly:** Review and update dependencies

### Database Maintenance

```bash
# Analyze tables
docker-compose exec postgres psql -U postgres -d internal_payment -c "ANALYZE;"

# Vacuum database
docker-compose exec postgres psql -U postgres -d internal_payment -c "VACUUM ANALYZE;"
```

---

## Support

For infrastructure issues:
1. Check logs: `docker-compose logs`
2. Verify health: `curl http://localhost:8000/health/`
3. Review this documentation
4. Contact INFRA_ENGINEER

---

*This infrastructure setup enforces environment stability and reproducibility. All changes must maintain these principles.*
