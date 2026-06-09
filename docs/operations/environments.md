Doc ID: OPS-ENV-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/architecture/system-overview.md, docs/backend/backend-docs.md, docs/frontend/frontend-docs.md, docs/security/secrets-management.md
Update together with: deployment.md, system-overview.md
Update trigger: новое окружение, сервис, env-переменная или изменение портов
Review required: operations, backend
Maturity: L2

# Environments

## Overview

| Environment | Purpose | Database | Domain (example) |
|---|---|---|---|
| **local** | Developer machine + Docker Compose | PostgreSQL in Docker | localhost:3000 / :8000 |
| **staging** | Pre-prod checks | Managed Postgres | TBD |
| **production** | SaaS customers | Managed Postgres | TBD |

Rule: staging ≠ production credentials; secrets never in git.

## Local (Docker Compose)

Services defined in [`docker-compose.yml`](../../docker-compose.yml):

| Service | Image / build | Port | Role |
|---|---|---|---|
| `postgres` | pgvector/pgvector:pg16 | 5432 | Primary DB |
| `redis` | redis:7-alpine | 6379 | Celery broker + cache |
| `api` | build `apps/api` | 8000 | Django + DRF |
| `worker` | build `apps/api` | — | Celery worker |
| `web` | build `apps/web` | 3000 | Next.js |

### Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000  
- Admin: http://localhost:8000/admin/  
- OpenAPI: http://localhost:8000/api/schema/

Demo users (after `seed_demo`): see `.env.example`.

### Local without Docker (API only)

```bash
docker compose up -d postgres redis
cd apps/api
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

```bash
cd apps/web && npm install && npm run dev
```

## Environment Variables

Copy [`.env.example`](../../.env.example). Key groups:

| Variable | Used by | Description |
|---|---|---|
| `POSTGRES_*` | api, worker | Database connection |
| `REDIS_URL` | api, worker | Celery broker |
| `DJANGO_SECRET_KEY` | api | Django secret |
| `DJANGO_DEBUG` | api | `true` local only |
| `DJANGO_ALLOWED_HOSTS` | api | Comma-separated hosts |
| `CORS_ALLOWED_ORIGINS` | api | e.g. `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | web | Browser → API base URL |

Production/staging: add `S3_*`, `OPENAI_API_KEY` when STAGE-002+ enabled.

## Staging / Production (TBD)

- Managed PostgreSQL (pgvector enabled).
- Redis managed or container sidecar.
- `DJANGO_DEBUG=false`, strong `SECRET_KEY`, HTTPS only.
- Object storage bucket per environment.
- CI: lint + test + migrate on deploy.

## Related Docs

- [deployment.md](deployment.md) — deploy process (template)
- [secrets-management.md](../security/secrets-management.md)
