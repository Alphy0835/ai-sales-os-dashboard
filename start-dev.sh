#!/usr/bin/env bash
# AI Sales OS - local dev launcher (macOS / Linux)
# Usage:  ./start-dev.sh
#         ./start-dev.sh --run-tests
#         ./start-dev.sh --docker-all
#         ./start-dev.sh --install-docker
#         ./start-dev.sh --non-interactive

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

DOCKER_ALL=0
RUN_TESTS=0
REQUIRE_DOCKER=0
INSTALL_DOCKER=0
NONINTERACTIVE=0

for arg in "$@"; do
  case "$arg" in
    --docker-all) DOCKER_ALL=1 ;;
    --run-tests) RUN_TESTS=1 ;;
    --require-docker) REQUIRE_DOCKER=1 ;;
    --install-docker) INSTALL_DOCKER=1 ;;
    --non-interactive) NONINTERACTIVE=1 ;;
    -h|--help)
      echo "Usage: ./start-dev.sh [--run-tests] [--docker-all] [--install-docker] [--non-interactive]"
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

export INSTALL_DOCKER NONINTERACTIVE

# shellcheck source=scripts/docker-setup.sh
source "$ROOT/scripts/docker-setup.sh"

step() { echo ""; echo "==> $1"; }

import_dotenv() {
  local path="$1"
  [ -f "$path" ] || return 0
  set -a
  # shellcheck disable=SC1090
  source "$path"
  set +a
}

wait_postgres() {
  step "Waiting for PostgreSQL..."
  local deadline=$((SECONDS + 120))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if docker compose exec -T postgres pg_isready -U ai_sales_os >/dev/null 2>&1; then
      echo "PostgreSQL is ready."
      return 0
    fi
    sleep 2
  done
  echo "PostgreSQL did not become ready in time." >&2
  exit 1
}

set_local_dev_mode() {
  local api_dir="$1"
  export DATABASE_URL="sqlite:///${api_dir}/db.sqlite3"
  export CELERY_TASK_ALWAYS_EAGER=true
}

ensure_python_venv() {
  local api_dir="$1"
  local venv_py="${api_dir}/.venv/bin/python"
  if [ ! -x "$venv_py" ]; then
    step "Creating Python venv..."
    python3 -m venv "${api_dir}/.venv"
  fi
  echo "$venv_py"
}

docker_ready=0
if [ "$(docker_status)" = "ready" ]; then
  docker_ready=1
fi

use_local_mode=0
API_DIR="$ROOT/apps/api"
WEB_DIR="$ROOT/apps/web"

echo "AI Sales OS - local test launcher"
echo "Platform: $(detect_platform)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 not found. Install Python 3.11+." >&2
  exit 1
fi

if [ ! -f "$ROOT/.env" ]; then
  step "Creating .env from .env.example"
  cp "$ROOT/.env.example" "$ROOT/.env"
fi
import_dotenv "$ROOT/.env"

step "Starting Docker services..."

if [ "$DOCKER_ALL" = "1" ]; then
  if [ "$docker_ready" -ne 1 ]; then
    echo "Docker not available. Start Docker Desktop or run without --docker-all." >&2
    exit 1
  fi
  docker compose up --build -d
  wait_postgres
  echo ""
  echo "All services run in Docker."
  echo "  Web:  http://localhost:3000"
  echo "  API:  http://localhost:8000/api/v1/health/"
  echo "  Demo: manager@demo.local / demo1234"
  exit 0
fi

if [ "$docker_ready" -ne 1 ]; then
  if [ "$REQUIRE_DOCKER" = "1" ]; then
    INSTALL_DOCKER=1
    assist="$(docker_setup_assist)"
    if [ "$assist" = "ready" ]; then docker_ready=1; fi
    if [ "$assist" = "quit" ]; then exit 1; fi
    if [ "$docker_ready" -ne 1 ]; then
      echo "Docker is required but not available." >&2
      exit 1
    fi
  elif [ "$RUN_TESTS" = "1" ]; then
    echo "Docker not available - using SQLite for API tests."
    set_local_dev_mode "$API_DIR"
    use_local_mode=1
  else
    assist="$(docker_setup_assist)"
    if [ "$assist" = "quit" ]; then exit 0; fi
    if [ "$assist" = "ready" ]; then
      docker_ready=1
    else
      echo "Using LOCAL mode (SQLite, no Redis/Celery worker)."
      set_local_dev_mode "$API_DIR"
      use_local_mode=1
    fi
  fi
fi

if [ "$docker_ready" = "1" ]; then
  if ! docker compose up -d postgres redis; then
    if [ "$REQUIRE_DOCKER" = "1" ]; then
      echo "docker compose failed. Is Docker running?" >&2
      exit 1
    fi
    echo "docker compose failed - falling back to LOCAL mode."
    set_local_dev_mode "$API_DIR"
    use_local_mode=1
    docker_ready=0
  else
    wait_postgres
  fi
fi

PY="$(ensure_python_venv "$API_DIR")"

step "Installing API dependencies..."
"$PY" -m pip install -q -r "$API_DIR/requirements.txt"

step "Migrating database and seeding demo data..."
if [ "$RUN_TESTS" = "1" ] || [ "$use_local_mode" = "1" ]; then
  set_local_dev_mode "$API_DIR"
fi
(
  cd "$API_DIR"
  "$PY" manage.py migrate --noinput
  "$PY" manage.py seed_demo
)

if [ "$RUN_TESTS" = "1" ]; then
  step "Running API tests..."
  export CELERY_TASK_ALWAYS_EAGER=true
  (
    cd "$API_DIR"
    "$PY" manage.py test accounts.tests integrations.tests analytics.tests -v 1
  )
  echo ""
  echo "All tests passed."
  exit 0
fi

if [ ! -d "$WEB_DIR/node_modules" ]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Install Node.js 20+ or run with --run-tests only." >&2
    exit 1
  fi
  step "Installing web dependencies (npm install)..."
  (cd "$WEB_DIR" && npm install)
fi

step "Starting API, worker, and Next.js in background..."

LOG_DIR="$ROOT/.dev-logs"
mkdir -p "$LOG_DIR"

(
  cd "$API_DIR"
  export DATABASE_URL REDIS_URL CORS_ALLOWED_ORIGINS CELERY_TASK_ALWAYS_EAGER
  [ "$use_local_mode" = "1" ] && export CELERY_TASK_ALWAYS_EAGER=true
  nohup "$PY" manage.py runserver 0.0.0.0:8000 >"$LOG_DIR/api.log" 2>&1 &
  echo $! >"$LOG_DIR/api.pid"
)

if [ "$use_local_mode" -ne 1 ]; then
  (
    cd "$API_DIR"
    export DATABASE_URL REDIS_URL
    nohup "$PY" -m celery -A config worker -l info >"$LOG_DIR/worker.log" 2>&1 &
    echo $! >"$LOG_DIR/worker.pid"
  )
fi

(
  cd "$WEB_DIR"
  export NEXT_PUBLIC_API_URL
  export API_BACKEND_URL="${API_BACKEND_URL:-http://localhost:8000}"
  nohup npm run dev >"$LOG_DIR/web.log" 2>&1 &
  echo $! >"$LOG_DIR/web.pid"
)

echo ""
if [ "$use_local_mode" = "1" ]; then
  echo "Local stack started (LOCAL mode - SQLite, no Docker)."
else
  echo "Local stack started (Docker Postgres + Redis)."
fi
echo "  Web:  http://localhost:3000"
echo "  API:  http://localhost:8000/api/v1/health/"
echo "  Logs: $LOG_DIR/*.log"
echo "  Stop: kill \$(cat $LOG_DIR/*.pid) 2>/dev/null; docker compose stop postgres redis"
echo ""
echo "Demo: manager@demo.local / demo1234"
