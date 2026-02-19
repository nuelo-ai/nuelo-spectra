#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Backend Docker Entrypoint
# Waits for PostgreSQL, runs migrations, starts uvicorn
# ============================================================

# --- Parse DB connection from DATABASE_URL ---
# Supports both postgresql+asyncpg://... and postgresql://... formats
DB_HOST="${DB_HOST:-$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')}"
DB_PORT="${DB_PORT:-$(echo "$DATABASE_URL" | sed -E 's|.*@[^:]+:([0-9]+)/.*|\1|')}"
DB_PORT="${DB_PORT:-5432}"

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

# --- Wait for PostgreSQL with bounded retries ---
MAX_RETRIES=30
RETRY_INTERVAL=2
RETRIES=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
  RETRIES=$((RETRIES + 1))
  if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
    echo "[entrypoint] ERROR: PostgreSQL not ready after ${MAX_RETRIES} attempts ($(( MAX_RETRIES * RETRY_INTERVAL ))s). Exiting."
    exit 1
  fi
  echo "[entrypoint] PostgreSQL not ready (attempt ${RETRIES}/${MAX_RETRIES}), retrying in ${RETRY_INTERVAL}s..."
  sleep "$RETRY_INTERVAL"
done

echo "[entrypoint] PostgreSQL is ready."

# --- Run Alembic migrations ---
echo "[entrypoint] Running database migrations..."
/app/.venv/bin/python -m alembic upgrade head
echo "[entrypoint] Migrations complete."

# --- Start uvicorn via exec (replaces bash as PID 1) ---
echo "[entrypoint] Starting uvicorn on port 8000 with ${UVICORN_WORKERS:-1} worker(s)..."
exec /app/.venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${UVICORN_WORKERS:-1}"
