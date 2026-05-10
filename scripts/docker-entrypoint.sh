#!/usr/bin/sh
set -e
if [ "${DATABASE_SCHEMA_MANAGED_BY:-app}" = "alembic" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi
exec "$@"
