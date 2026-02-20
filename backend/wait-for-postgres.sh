#!/bin/sh
set -e

echo "Waiting for Postgres..."

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  sleep 2
done

echo "Postgres is ready."

# Run migrations, but skip users app to avoid conflicts (migrations already applied)
python manage.py migrate --noinput --skip-checks || python manage.py migrate --noinput --run-syncdb 2>/dev/null || true

exec "$@"
