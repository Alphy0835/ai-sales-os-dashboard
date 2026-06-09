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

## Architecture (production)

Browser traffic hits **one public hostname** (e.g. `https://app.example.com`). Next.js acts as a **BFF**: the browser calls same-origin `/api/v1/…` with httpOnly cookies; Next rewrites those requests to Django on the internal Docker network (`API_BACKEND_URL=http://api:8000`).

Do **not** point the browser at a separate API subdomain in production — cross-origin API URLs break cookie auth.

## Prerequisites

- Docker Engine + Compose v2 on the host
- Production `.env` at repo root (never commit; copy from [`.env.example`](../../.env.example))
- Reverse proxy on the host (nginx or Caddy) terminating TLS and forwarding to `127.0.0.1:3000`
- Host firewall: only **80/443** public (see [Firewall](#firewall))
- **Backup before deploy:** [`scripts/backup-postgres.sh`](../../scripts/backup-postgres.sh) or [`scripts/backup-postgres.ps1`](../../scripts/backup-postgres.ps1)

## Services (production compose)

| Service | Build context | Host exposure | Role |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | internal only | Primary DB |
| `redis` | `redis:7-alpine` | internal only | Celery broker |
| `api` | `apps/api` | **no public port** | Django + Gunicorn (no `--reload`, no `seed_demo`) |
| `worker` | `apps/api` | internal only | Celery worker |
| `beat` | `apps/api` | internal only | Celery Beat — daily `integrations.purge_expired_transcripts` (03:00 UTC, see [`settings.py`](../../apps/api/config/settings.py)) |
| `web` | `apps/web` (multi-stage **baked** image) | `127.0.0.1:${WEB_PORT:-3000}` | Next.js standalone (`node server.js`); build args bake BFF env at image build |

Postgres, Redis, `api`, `worker`, and `beat` have **no host port mapping** — only containers on the Docker network reach them. `web` binds to **localhost only** so the reverse proxy is the sole public entry point.

## Environment checklist

Set these in `.env` before first deploy:

| Variable | Required | Notes |
|---|---|---|
| `POSTGRES_PASSWORD` | **yes** | Strong password; compose fails fast if unset |
| `POSTGRES_DB`, `POSTGRES_USER` | yes | Defaults: `ai_sales_os` |
| `DJANGO_SECRET_KEY` | **yes** | ≥ 32 random bytes; no default in prod |
| `DJANGO_ENV` | **yes** | Set to `production` (or `DJANGO_DEBUG=false`) |
| `DJANGO_DEBUG` | yes | Must be `false` (compose also sets `DJANGO_DEBUG=false` on api/worker/beat) |
| `DJANGO_ALLOWED_HOSTS` | **yes** | Comma-separated hostnames Django accepts — include internal `api` **and** your public app domain if needed (see [TLS behind reverse proxy](#tls-behind-reverse-proxy-secure_proxy_ssl_header)) |
| `CORS_ALLOWED_ORIGINS` | **yes** | Browser origin(s), e.g. `https://app.example.com` |
| `NEXT_PUBLIC_API_URL` | **yes** | Must be **empty** (`""`) in production — browser uses same-origin `/api/v1`; do **not** set a cross-origin API URL |
| `API_BACKEND_URL` | auto | Compose sets `http://api:8000` for Next rewrites; used as Docker build arg for `web` |
| `REDIS_URL` | auto | Overridden to `redis://redis:6379/0` inside compose |
| `DATABASE_URL` | auto | Overridden to internal `postgres` host in compose |
| `GUNICORN_WORKERS` | optional | Default `3` (range 2–4 recommended) |
| `WEB_PORT` | optional | Host bind port for `web`; default `3000`, bound to `127.0.0.1` only |
| `THROTTLE_LOGIN`, `THROTTLE_AGENT` | optional | Defaults: `10/min`, `30/min` |
| `TRANSCRIPT_RETENTION_DAYS` | optional | Default `90`; purged by Beat task |

Do **not** run `seed_demo` in production unless creating a one-off staging sandbox.

## Reverse proxy

Terminate TLS on the host and proxy **only** to the Next.js container on localhost. Pass `X-Forwarded-Proto: https` so Django (via BFF rewrites) can detect HTTPS when `SECURE_SSL_REDIRECT` is enabled.

Replace `app.example.com` with your domain. Ensure DNS points at this host before enabling TLS.

### nginx

```nginx
# /etc/nginx/sites-available/ai-sales-os
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site, test config, reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Caddy

```caddy
# /etc/caddy/Caddyfile
app.example.com {
    reverse_proxy 127.0.0.1:3000 {
        header_up X-Forwarded-Proto https
    }
}
```

Caddy obtains and renews certificates automatically. Reload after edits:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Firewall

Expose **only** HTTP/HTTPS to the internet. Everything else stays on the Docker network or localhost.

| Port / binding | Public? | Notes |
|---|---|---|
| `80`, `443` | yes | Reverse proxy (nginx/Caddy) |
| `127.0.0.1:3000` (`web`) | no | Localhost only; proxy upstream |
| `api:8000` | no | No host mapping in prod compose |
| Postgres / Redis | no | Internal Docker network only |

**Example (ufw on Ubuntu):**

```bash
sudo ufw default deny incoming
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Verify `web` is not reachable from outside the host:

```bash
curl -sf http://127.0.0.1:3000/ -o /dev/null   # should succeed on the host
# From another machine: connection to <host-ip>:3000 should fail/refuse
```

## TLS behind reverse proxy (`SECURE_PROXY_SSL_HEADER`)

When `DJANGO_ENV=production` (or `DJANGO_SECURE=true`), Django enables HTTPS security settings in [`apps/api/config/settings.py`](../../apps/api/config/settings.py):

- `SECURE_SSL_REDIRECT = True` — redirects HTTP requests to HTTPS
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — treats the request as HTTPS when the reverse proxy sets `X-Forwarded-Proto: https`

**Why this matters:** TLS terminates at nginx/Caddy; the hop from proxy → Next → Django may be plain HTTP inside the host/container network. Without `SECURE_PROXY_SSL_HEADER`, Django sees HTTP and can **301-redirect in a loop** or break health checks.

**`DJANGO_ALLOWED_HOSTS`:** include at minimum the internal Docker hostname `api` (Next rewrites target `http://api:8000`). If you expose Django Admin on a separate hostname or run direct in-container health checks, also include `localhost`, `127.0.0.1`, and your public domain(s).

Example production `.env` fragment:

```bash
DJANGO_ENV=production
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api,localhost,127.0.0.1,app.example.com
CORS_ALLOWED_ORIGINS=https://app.example.com
NEXT_PUBLIC_API_URL=
API_BACKEND_URL=http://api:8000
```

## Celery Beat (retention purge)

The `beat` service in [`docker-compose.prod.yml`](../../docker-compose.prod.yml) runs:

```bash
celery -A config beat -l info
```

It schedules `integrations.purge_expired_transcripts` daily at **03:00 UTC** (`CELERY_BEAT_SCHEDULE` in settings). The `worker` service must be running for tasks to execute.

After deploy, confirm Beat is up:

```bash
docker compose -f docker-compose.prod.yml ps beat worker
docker compose -f docker-compose.prod.yml logs beat --tail 30
```

Manual one-off purge (ops/debug):

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py purge_transcripts
```

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

### Web image build note

Production `web` uses a **multi-stage Dockerfile** — `npm run build` runs at **image build** time with `NEXT_PUBLIC_API_URL` and `API_BACKEND_URL` build args. Container start runs prebuilt `node server.js` (no rebuild on restart).

Changing BFF-related env vars requires rebuilding the `web` image:

```bash
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d web
```

Keep `NEXT_PUBLIC_API_URL` empty for same-origin cookie auth.

## Health checks

- Postgres / Redis: compose healthchecks; `api`, `worker`, and `beat` wait until healthy
- API readiness (inside container): `docker compose -f docker-compose.prod.yml exec api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ready/')"`
- Public smoke (through BFF + TLS): `curl -f https://app.example.com/api/v1/health/ready/`
- Web UI: open `https://app.example.com` and log in

## Post-deploy

- Confirm Celery worker and beat: `docker compose -f docker-compose.prod.yml logs worker beat --tail 20`
- Spot-check login, dashboard, and one write path
- If deploy fails, follow [rollback.md](rollback.md)

## Related

- [auth-and-access-control.md](../security/auth-and-access-control.md) — cookie auth flow, logout blacklist
- [frontend-docs.md](../frontend/frontend-docs.md) — BFF client (`credentials: "include"`, empty `NEXT_PUBLIC_API_URL`)
- [environments.md](environments.md) — local vs prod overview
- [backup-and-restore.md](backup-and-restore.md) — scheduled backups and restore drills
- [rollback.md](rollback.md) — revert a bad release
