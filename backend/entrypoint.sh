#!/bin/sh
set -eu

echo "[entrypoint] Starting backend container"

# ── Required env-var validation ──
MISSING=""
for VAR in DATABASE_URL SECRET_KEY; do
  eval VAL=\${${VAR}:-}
  if [ -z "$VAL" ]; then
    MISSING="$MISSING $VAR"
  fi
done
if [ -n "$MISSING" ]; then
  echo "[entrypoint] ERROR: Missing required environment variables:$MISSING"
  exit 1
fi

if [ "${WAIT_FOR_DB:-true}" = "true" ]; then
  echo "[entrypoint] Waiting for database readiness"
  ATTEMPTS=0
  MAX_ATTEMPTS="${DB_WAIT_MAX_ATTEMPTS:-30}"
  SLEEP_SECONDS="${DB_WAIT_SLEEP_SECONDS:-2}"

  while ! python -c "from database_config import engine; conn = engine.connect(); conn.close()" >/dev/null 2>&1; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
      echo "[entrypoint] Database did not become ready in time"
      exit 1
    fi
    sleep "$SLEEP_SECONDS"
  done
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "[entrypoint] Running alembic migrations"
  python -m alembic upgrade head
fi

WORKERS="${UVICORN_WORKERS:-4}"
LOG_LEVEL="${UVICORN_LOG_LEVEL:-info}"

echo "[entrypoint] Starting Uvicorn with ${WORKERS} workers"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers "$WORKERS" --log-level "$LOG_LEVEL"
