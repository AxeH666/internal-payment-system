#!/bin/sh
set -e

echo "Waiting for Postgres..."

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  sleep 2
done

echo "Postgres is ready."

python manage.py migrate --noinput --run-syncdb

exec "$@"
