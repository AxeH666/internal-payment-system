# Quick Start Guide

## Prerequisites

- Docker 20.10+
- docker-compose 2.0+
- Bash shell

## Setup (5 minutes)

1. **Clone and navigate**
   ```bash
   cd internal-payment-system
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Generate SECRET_KEY**
   ```bash
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output and paste it into `backend/.env` as `SECRET_KEY=...`

4. **Set database password**
   Edit `backend/.env` and set `POSTGRES_PASSWORD` to a strong password.

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

## Verify Installation

```bash
# Check health
curl http://localhost:8000/health/

# Check logs
docker-compose logs backend
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Run Django management commands
docker-compose exec backend python manage.py <command>

# Create database backup
./scripts/backup_db.sh

# Access database shell
docker-compose exec postgres psql -U postgres -d internal_payment
```

## Development Mode

For development with hot reload:

1. Copy override file:
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

2. Start services:
   ```bash
   docker-compose up
   ```

The backend will run Django's development server with hot reload enabled.

## Troubleshooting

**Services won't start:**
- Check `.env` file exists and has all required variables
- Verify Docker is running: `docker ps`
- Check logs: `docker-compose logs`

**Database connection errors:**
- Ensure PostgreSQL container is healthy: `docker-compose ps postgres`
- Verify `POSTGRES_PASSWORD` is set in `.env`
- Check database logs: `docker-compose logs postgres`

**Migration errors:**
- Check database is accessible: `docker-compose exec postgres pg_isready`
- Review migration status: `docker-compose exec backend python manage.py showmigrations`

For detailed information, see [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md).
