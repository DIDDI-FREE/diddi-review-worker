#!/bin/sh
# Apply database migrations before starting the API. Retry a few times so the
# container tolerates Postgres still booting. A persistent failure is fatal.
set -e

attempts=0
until alembic upgrade head; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 10 ]; then
    echo "alembic upgrade head failed after $attempts attempts" >&2
    exit 1
  fi
  echo "database not ready, retrying migrations ($attempts/10)..." >&2
  sleep 3
done

exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000
