#!/bin/bash
# Database Restore Script for Internal Payment Workflow System
# Usage: ./scripts/restore_db.sh <backup_file>
#
# This script restores a PostgreSQL backup.
# WARNING: This will overwrite the current database!
# Requires: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST environment variables

set -euo pipefail

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Error: Backup file required"
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Load environment variables from .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Database configuration
PG_DB="${POSTGRES_DB:-internal_payment}"
PG_USER="${POSTGRES_USER:-postgres}"
PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_PASSWORD="${POSTGRES_PASSWORD:-}"

# Confirmation prompt
echo "WARNING: This will overwrite the current database '${PG_DB}'!"
echo "Backup file: ${BACKUP_FILE}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if running in Docker or locally
if command -v docker-compose &> /dev/null && docker-compose ps postgres &> /dev/null; then
    # Running via docker-compose
    echo "Restoring backup via docker-compose..."
    
    export PGPASSWORD="${PG_PASSWORD}"
    
    # Drop and recreate database
    docker-compose exec -T postgres psql -U "${PG_USER}" -h localhost -c "DROP DATABASE IF EXISTS ${PG_DB};" postgres || true
    docker-compose exec -T postgres psql -U "${PG_USER}" -h localhost -c "CREATE DATABASE ${PG_DB};" postgres
    
    # Restore backup
    gunzip -c "${BACKUP_FILE}" | docker-compose exec -T postgres psql -U "${PG_USER}" -h localhost "${PG_DB}"
    
    unset PGPASSWORD
else
    # Running locally (requires psql)
    if ! command -v psql &> /dev/null; then
        echo "Error: psql not found. Install PostgreSQL client tools."
        exit 1
    fi
    
    echo "Restoring backup locally..."
    
    export PGPASSWORD="${PG_PASSWORD}"
    
    # Drop and recreate database
    psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -c "DROP DATABASE IF EXISTS ${PG_DB};" postgres || true
    psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -c "CREATE DATABASE ${PG_DB};" postgres
    
    # Restore backup
    gunzip -c "${BACKUP_FILE}" | psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}"
    
    unset PGPASSWORD
fi

echo "✓ Database restored successfully from: ${BACKUP_FILE}"
echo "Note: You may need to run migrations: python manage.py migrate"
