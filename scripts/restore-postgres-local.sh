#!/usr/bin/env bash
# Restore PostgreSQL from a .sql.gz backup into docker-compose.prod.yml postgres.
# Usage (repo root): ./scripts/restore-postgres-local.sh backups/ai_sales_os_YYYYMMDD_HHMMSS.sql.gz
#
# Destructive: drops and recreates the application database. Stops api/worker/beat/web during restore.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-backup.sql.gz>" >&2
  exit 1
fi

BACKUP="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
COMPOSE_FILE="docker-compose.prod.yml"

if [ ! -f "$BACKUP" ]; then
  echo "Backup file not found: $BACKUP" >&2
  exit 1
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_DB="${POSTGRES_DB:-ai_sales_os}"
POSTGRES_USER="${POSTGRES_USER:-ai_sales_os}"

if ! docker compose -f "$COMPOSE_FILE" ps postgres --status running -q 2>/dev/null | grep -q .; then
  echo "Postgres is not running. Start stack first:" >&2
  echo "  docker compose -f $COMPOSE_FILE up -d postgres" >&2
  exit 1
fi

echo "Stopping writers (api, worker, beat, web)..."
docker compose -f "$COMPOSE_FILE" stop api worker beat web 2>/dev/null || true

echo "Recreating database $POSTGRES_DB..."
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();"

docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d postgres -c \
  "DROP DATABASE IF EXISTS ${POSTGRES_DB};"

docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d postgres -c \
  "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"

echo "Restoring from $BACKUP..."
if ! gunzip -c "$BACKUP" | docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
  echo "Restore failed — database may be partial. Writers remain stopped." >&2
  exit 1
fi

echo "Starting application services..."
docker compose -f "$COMPOSE_FILE" up -d api worker beat web

echo ""
echo "Restore complete. Verify:"
echo "  curl -sf http://127.0.0.1:3000/api/v1/health/ready/"
echo "  docker compose -f $COMPOSE_FILE exec api python manage.py showmigrations | tail -5"
echo "See docs/operations/local-gate-checklist.md — A3 restore drill."
