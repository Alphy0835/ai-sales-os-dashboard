#!/usr/bin/env bash
# CI prod-compose smoke: validate, build, migrate, seed, health check.
# Run from repo root: ./scripts/ci-prod-smoke.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker-compose.prod.yml"
WEB_PORT="${WEB_PORT:-3000}"
BFF_HEALTH="http://127.0.0.1:${WEB_PORT}/api/v1/health/ready/"

log() { printf '%s\n' "$*"; }
ok() { log "OK: $*"; }
fail() { log "FAIL: $*" >&2; }

cleanup() {
  local exit_code=$?
  log "Tearing down compose stack (down -v)..."
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT

create_ci_env() {
  if [[ ! -f .env.local-prod.example ]]; then
    fail ".env.local-prod.example not found"
    exit 1
  fi

  cp .env.local-prod.example .env

  local pg_pass="ci-prod-postgres-smoke-secret"
  local django_key="ci-prod-django-secret-key-32chars-minimum"
  local creds_key="ci-prod-credentials-key-32chars-min"

  sed -i \
    -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${pg_pass}/" \
    -e "s#^DATABASE_URL=.*#DATABASE_URL=postgres://ai_sales_os:${pg_pass}@postgres:5432/ai_sales_os#" \
    -e "s/^DJANGO_SECRET_KEY=.*/DJANGO_SECRET_KEY=${django_key}/" \
    -e "s/^AI_CREDENTIALS_KEY=.*/AI_CREDENTIALS_KEY=${creds_key}/" \
    .env

  ok "Created .env from .env.local-prod.example (CI-safe secrets)"
}

wait_for_api_health() {
  local max_attempts="${1:-90}"
  local i

  log "Waiting for API health (in-container)..."
  for ((i = 1; i <= max_attempts; i++)); do
    if docker compose -f "$COMPOSE_FILE" exec -T api python -c \
      "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/v1/health/ready/'); exit(0 if r.status == 200 else 1)" \
      >/dev/null 2>&1; then
      ok "API health/ready (attempt ${i})"
      return 0
    fi
    sleep 5
  done

  fail "API health/ready timed out after $((max_attempts * 5))s"
  docker compose -f "$COMPOSE_FILE" logs api --tail 80 || true
  return 1
}

wait_for_bff_health() {
  local max_attempts="${1:-36}"
  local i

  log "Waiting for BFF health (web → api)..."
  for ((i = 1; i <= max_attempts; i++)); do
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 "$BFF_HEALTH" || echo "000")"
    if [[ "$code" == "200" ]]; then
      ok "BFF health/ready — HTTP 200 (attempt ${i})"
      return 0
    fi
    sleep 5
  done

  fail "BFF health/ready timed out ($BFF_HEALTH)"
  docker compose -f "$COMPOSE_FILE" logs web --tail 40 || true
  docker compose -f "$COMPOSE_FILE" logs api --tail 40 || true
  return 1
}

curl_smoke_health() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 "$BFF_HEALTH" || echo "000")"
  if [[ "$code" == "200" ]]; then
    ok "Smoke health curl — HTTP 200 ($BFF_HEALTH)"
    return 0
  fi
  fail "Smoke health curl — HTTP $code ($BFF_HEALTH)"
  return 1
}

main() {
  log "=== CI prod compose smoke ==="

  if ! command -v docker >/dev/null 2>&1; then
    fail "docker CLI not found"
    exit 1
  fi

  create_ci_env

  log "Validating compose config..."
  docker compose -f "$COMPOSE_FILE" config >/dev/null
  ok "docker compose config"

  log "Building and starting stack..."
  docker compose -f "$COMPOSE_FILE" up -d --build

  wait_for_api_health
  wait_for_bff_health

  log "Running migrations..."
  docker compose -f "$COMPOSE_FILE" exec -T api python manage.py migrate --noinput
  ok "migrate --noinput"

  log "Seeding pilot-local tenant..."
  docker compose -f "$COMPOSE_FILE" exec -T -e ALLOW_SEED_PILOT=1 api python manage.py seed_pilot_local
  ok "seed_pilot_local"

  curl_smoke_health

  log "CI prod compose smoke passed."
}

main "$@"
