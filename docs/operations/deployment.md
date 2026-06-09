Doc ID: OPS-DEPLOY-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/environments.md, docs/operations/rollback.md, docs/operations/backup-and-restore.md, docs/security/secrets-management.md
Update together with: docker-compose.prod.yml, .env.example, environments.md
Update trigger: new service, port, env var, or deploy step change
Review required: operations, backend
Maturity: L2

# Deployment

Production deploy uses [`docker-compose.prod.yml`](../../docker-compose.prod.yml) at the repo root. Local dev stays on [`docker-compose.yml`](../../docker-compose.yml) (hot reload, `seed_demo`).

## Prerequisites

- Docker Engine + Compose v2 on the host
- Production `.env` at repo root (never commit; copy from [`.env.example`](../../.env.example))
- DNS / TLS terminated in front of the stack (reverse proxy or load balancer)
- **Backup before deploy:** [`scripts/backup-postgres.sh`](../../scripts/backup-postgres.sh) or [`scripts/backup-postgres.ps1`](../../scripts/backup-postgres.ps1)

## Services (production compose)

| Service | Build context | Port (default) | Role |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | internal only | Primary DB |
| `redis` | `redis:7-alpine` | internal only | Celery broker |
| `api` | `apps/api` | `8000` | Django + Gunicorn (no `--reload`, no `seed_demo`) |
| `worker` | `apps/api` | — | Celery worker |
| `web` | `apps/web` | `3000` | Next.js (`npm run build` + `npm run start`) |

Postgres and Redis have **no host port mapping** in prod compose — only other containers reach them on the Docker network.

## Environment checklist

Set these in `.env` before first deploy:

| Variable | Required | Notes |
|---|---|---|
| `POSTGRES_PASSWORD` | **yes** | Strong password; compose fails fast if unset |
| `POSTGRES_DB`, `POSTGRES_USER` | yes | Defaults: `ai_sales_os` |
| `DJANGO_SECRET_KEY` | **yes** | ≥ 32 random bytes; no default in prod |
| `DJANGO_DEBUG` | yes | Must be `false` (compose also sets `DJANGO_DEBUG=false` on api/worker) |
| `DJANGO_ALLOWED_HOSTS` | **yes** | Comma-separated API hostnames, e.g. `api.example.com` |
| `CORS_ALLOWED_ORIGINS` | **yes** | Browser origin(s), e.g. `https://app.example.com` |
| `NEXT_PUBLIC_API_URL` | **yes** | Public API URL baked into Next.js at **build** time (e.g. `https://api.example.com`) |
| `REDIS_URL` | auto | Overridden to `redis://redis:6379/0` inside compose |
| `DATABASE_URL` | auto | Overridden to internal `postgres` host in compose |
| `GUNICORN_WORKERS` | optional | Default `3` (range 2–4 recommended) |
| `API_PORT`, `WEB_PORT` | optional | Host bind ports; default `8000`, `3000` |
| `THROTTLE_LOGIN`, `THROTTLE_AGENT` | optional | Defaults: `10/min`, `30/min` |

Do **not** run `seed_demo` in production unless creating a one-off staging sandbox.

## Deploy steps

From the repository root:

```bash
# 1. Backup database
./scripts/backup-postgres.sh          # macOS / Linux
# .\scripts\backup-postgres.ps1       # Windows

# 2. Pull latest code and build images
git pull
docker compose -f docker-compose.prod.yml build

# 3. Start (or recreate) stack
docker compose -f docker-compose.prod.yml up -d

# 4. Verify
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api --tail 50
```

### What runs on API startup

The `api` container command (no manual step needed on normal deploy):

1. `python manage.py migrate` — apply pending migrations
2. `python manage.py collectstatic --noinput` — gather static files to `apps/api/staticfiles/` (`STATIC_ROOT` in [`apps/api/config/settings.py`](../../apps/api/config/settings.py))
3. `gunicorn config.wsgi:application` — **3 workers** by default, no `--reload`

To run migrate/collectstatic manually (e.g. one-off job):

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py migrate
docker compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput
```

### Web build note

`web` runs `npm run build` on container start. Changing `NEXT_PUBLIC_API_URL` requires rebuilding/restarting `web`:

```bash
docker compose -f docker-compose.prod.yml up -d --build web
```

## Health checks

- Postgres / Redis: compose healthchecks; `api` and `worker` wait until healthy
- API smoke: `curl -f https://api.example.com/api/schema/` (or `/admin/login/`)
- Web: open `https://app.example.com` and log in

## Post-deploy

- Confirm Celery worker is running: `docker compose -f docker-compose.prod.yml logs worker --tail 20`
- Spot-check login, dashboard, and one write path
- If deploy fails, follow [rollback.md](rollback.md)

## Related

- [environments.md](environments.md) — local vs prod overview
- [backup-and-restore.md](backup-and-restore.md) — scheduled backups
- [rollback.md](rollback.md) — revert a bad release
