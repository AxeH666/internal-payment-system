#!/bin/bash
# Database Backup Script for Internal Payment Workflow System
# Usage: ./scripts/backup_db.sh [backup_directory]
# 
# This script creates a timestamped PostgreSQL backup.
# Requires: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST environment variables
#           or access to docker-compose postgres service

set -euo pipefail

# Configuration
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

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

# Check if running in Docker or locally
if command -v docker-compose &> /dev/null && docker-compose ps postgres &> /dev/null; then
    # Running via docker-compose
    echo "Creating backup via docker-compose..."
    mkdir -p "${BACKUP_DIR}"
    
    # Export password for pg_dump
    export PGPASSWORD="${PG_PASSWORD}"
    
    docker-compose exec -T postgres pg_dump -U "${PG_USER}" -h localhost "${PG_DB}" | gzip > "${BACKUP_FILE}"
    
    unset PGPASSWORD
else
    # Running locally (requires pg_dump)
    if ! command -v pg_dump &> /dev/null; then
        echo "Error: pg_dump not found. Install PostgreSQL client tools."
        exit 1
    fi
    
    echo "Creating backup locally..."
    mkdir -p "${BACKUP_DIR}"
    
    export PGPASSWORD="${PG_PASSWORD}"
    pg_dump -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" | gzip > "${BACKUP_FILE}"
    unset PGPASSWORD
fi

# Verify backup was created
if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✓ Backup created successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
    
    # Clean up old backups (keep last 30 days)
    find "${BACKUP_DIR}" -name "backup_*.sql.gz" -type f -mtime +30 -delete
    echo "✓ Cleaned up backups older than 30 days"
else
    echo "✗ Error: Backup file was not created or is empty"
    exit 1
fi
