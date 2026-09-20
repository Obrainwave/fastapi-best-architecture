#!/bin/sh
set -e

echo "Running database migrations..."
cd /app
alembic -c /app/migrations/alembic.ini upgrade head

echo "Starting application..."
exec "$@"