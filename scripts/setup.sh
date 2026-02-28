#!/bin/bash
# Setup Script for Internal Payment Workflow System
# This script helps set up the development environment

set -euo pipefail

echo "=== Internal Payment Workflow System - Setup ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and set all required values:"
        echo "   - SECRET_KEY (generate with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\")"
        echo "   - POSTGRES_PASSWORD"
        echo "   - ALLOWED_HOSTS"
        echo ""
        read -p "Press Enter after you've configured .env..."
    else
        echo "✗ Error: .env.example not found"
        exit 1
    fi
else
    echo "✓ .env file already exists"
fi

# Check Docker and docker-compose
if ! command -v docker &> /dev/null; then
    echo "✗ Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ Error: docker-compose is not installed"
    exit 1
fi

echo "✓ Docker and docker-compose are available"
echo ""

# Start services
echo "Starting services with docker-compose..."
docker-compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Check PostgreSQL health
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ Error: PostgreSQL is not ready"
    exit 1
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Ensure .env is properly configured"
echo "2. Start the backend: docker-compose up backend"
echo "3. Run migrations: docker-compose exec backend python manage.py migrate"
echo "4. Create superuser: docker-compose exec backend python manage.py createsuperuser"
echo ""
