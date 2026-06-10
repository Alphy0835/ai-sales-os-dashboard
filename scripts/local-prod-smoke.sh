#!/usr/bin/env bash
# Smoke test for local production-like stack (docker-compose.prod.yml).
# Run from repo root: ./scripts/local-prod-smoke.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker-compose.prod.yml"
WEB_PORT="${WEB_PORT:-3000}"
BFF_HEALTH="http://127.0.0.1:${WEB_PORT}/api/v1/health/ready/"
DEMO_EMAIL="${SMOKE_DEMO_EMAIL:-manager@demo.local}"
DEMO_PASSWORD="${SMOKE_DEMO_PASSWORD:-demo1234}"

failures=0

log() { printf '%s\n' "$*"; }
ok() { log "OK: $*"; }
warn() { log "WARN: $*"; }
fail() { log "FAIL: $*"; failures=$((failures + 1)); }

load_env() {
  if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
    WEB_PORT="${WEB_PORT:-3000}"
    BFF_HEALTH="http://127.0.0.1:${WEB_PORT}/api/v1/health/ready/"
  fi
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "docker CLI not found — install Docker Desktop or Docker Engine"
    return 1
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker daemon not running — start Docker Desktop and retry"
    return 1
  fi
  return 0
}

check_compose_running() {
  local running
  running="$(docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null || true)"
  if [[ -z "$running" ]]; then
    fail "docker-compose.prod.yml stack is not running"
    log ""
    log "Start the stack:"
    log "  cp .env.local-prod.example .env   # if you have no .env yet"
    log "  docker compose -f docker-compose.prod.yml up -d --build"
    log ""
    log "Optional demo users for login smoke:"
    log "  docker compose -f docker-compose.prod.yml exec api python manage.py seed_demo"
    return 1
  fi
  ok "compose services running: $(echo "$running" | tr '\n' ' ' | sed 's/ $//')"
  return 0
}

curl_health() {
  local url="$1"
  local label="$2"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 "$url" || echo "000")"
  if [[ "$code" == "200" ]]; then
    ok "$label — HTTP $code ($url)"
    return 0
  fi
  fail "$label — HTTP $code ($url)"
  return 1
}

check_bff_health() {
  curl_health "$BFF_HEALTH" "BFF health (web → api)"
}

check_direct_api_health() {
  if docker compose -f "$COMPOSE_FILE" ps --status running api 2>/dev/null | grep -q api; then
    if docker compose -f "$COMPOSE_FILE" exec -T api python -c \
      "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/v1/health/ready/'); exit(0 if r.status == 200 else 1)" \
      >/dev/null 2>&1; then
      ok "Direct API health (in-container :8000)"
      return 0
    fi
    fail "Direct API health (in-container :8000)"
    return 1
  fi
  warn "api service not running — skipped direct API health"
  return 0
}

check_login_smoke() {
  if [[ "${SKIP_LOGIN_SMOKE:-}" == "1" ]]; then
    warn "login smoke skipped (SKIP_LOGIN_SMOKE=1)"
    return 0
  fi

  local tmp http_code
  tmp="$(mktemp)"
  http_code="$(curl -s -o "$tmp" -w '%{http_code}' \
    -X POST "${BFF_HEALTH%/health/ready/}auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}" \
    --connect-timeout 5 --max-time 15 || echo "000")"

  if [[ "$http_code" == "200" ]]; then
    ok "Login smoke ($DEMO_EMAIL) — HTTP 200"
    rm -f "$tmp"
    return 0
  fi

  if [[ "$http_code" == "401" || "$http_code" == "400" ]]; then
    warn "Login smoke skipped — demo user not seeded (HTTP $http_code). Run: docker compose -f $COMPOSE_FILE exec api python manage.py seed_demo"
    rm -f "$tmp"
    return 0
  fi

  fail "Login smoke — HTTP $http_code"
  if [[ -s "$tmp" ]]; then
    log "  response: $(head -c 200 "$tmp")"
  fi
  rm -f "$tmp"
  return 1
}

main() {
  log "=== Local prod smoke (Gate A1) ==="
  load_env

  check_docker || exit 1
  check_compose_running || exit 1

  check_bff_health
  check_direct_api_health
  check_login_smoke

  log ""
  if [[ "$failures" -gt 0 ]]; then
    log "Smoke finished with $failures failure(s)."
    exit 1
  fi
  log "Smoke passed."
}

main "$@"
