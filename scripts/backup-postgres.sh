#!/usr/bin/env bash
# Dump PostgreSQL to backups/<db>_<timestamp>.sql.gz
# Run from repo root: ./scripts/backup-postgres.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_DB="${POSTGRES_DB:-ai_sales_os}"
POSTGRES_USER="${POSTGRES_USER:-ai_sales_os}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT/backups"
OUTPUT="$OUT_DIR/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

mkdir -p "$OUT_DIR"

dump_via_compose() {
  local compose_file="$1"
  docker compose -f "$compose_file" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" --no-owner --no-acl "$POSTGRES_DB"
}

if docker compose -f docker-compose.prod.yml ps postgres --status running -q 2>/dev/null | grep -q .; then
  dump_via_compose docker-compose.prod.yml | gzip > "$OUTPUT"
elif docker compose ps postgres --status running -q 2>/dev/null | grep -q .; then
  dump_via_compose docker-compose.yml | gzip > "$OUTPUT"
elif command -v pg_dump >/dev/null 2>&1; then
  DATABASE_URL="${DATABASE_URL:-postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}}"
  pg_dump "$DATABASE_URL" --no-owner --no-acl | gzip > "$OUTPUT"
else
  echo "No running postgres container and pg_dump not found." >&2
  exit 1
fi

echo "Backup written to $OUTPUT"
