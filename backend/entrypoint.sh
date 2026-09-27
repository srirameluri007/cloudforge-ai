#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "$SEED_DEMO" = "true" ]; then
  echo "Seeding demo data..."
  python -m app.seed
fi

echo "Starting CloudForge AI backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
