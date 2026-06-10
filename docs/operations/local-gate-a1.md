Doc ID: OPS-LOCAL-A1-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/deployment.md, docs/operations/environments.md, docs/operations/integrator-vps-pilot.md
Update together with: docker-compose.prod.yml, .env.local-prod.example, scripts/local-prod-smoke.*
Update trigger: local prod compose, env var, or Gate A step change
Review required: operations, backend
Maturity: L2

# Gate A1 — Local production-like stack (Windows / localhost)

**Not VPS.** Run [`docker-compose.prod.yml`](../../docker-compose.prod.yml) on your machine to validate the same stack shape as production before deploy (Phase D).

## Prerequisites

- Docker Desktop for Windows (WSL2 backend recommended)
- Git repo cloned locally
- Ports free: `127.0.0.1:3000` (web BFF)

## Quick start (Windows PowerShell)

From the repository root:

```powershell
# 1. Environment
Copy-Item .env.local-prod.example .env
# Edit .env: set POSTGRES_PASSWORD, DJANGO_SECRET_KEY, AI_CREDENTIALS_KEY to unique values

# 2. Build and start prod compose
docker compose -f docker-compose.prod.yml up -d --build

# 3. Wait for healthy services (first start may take 2–3 min)
docker compose -f docker-compose.prod.yml ps

# 4. Smoke
.\scripts\local-prod-smoke.ps1
```

macOS / Linux: use `./scripts/local-prod-smoke.sh` instead.

## What runs

| Service | Host access | Notes |
|---|---|---|
| `web` | http://127.0.0.1:3000 | BFF — browser hits same-origin `/api/v1/…` |
| `api` | internal only | Gunicorn; health via smoke script or `docker compose exec` |
| `postgres`, `redis`, `worker`, `beat` | internal only | Same as [deployment.md](deployment.md) |

No reverse proxy or TLS required locally. Set `DJANGO_SECURE=false` in `.env` (see `.env.local-prod.example`).

## Optional: demo tenant for login smoke

Production compose does **not** run `seed_demo` on startup. For login smoke:

```powershell
docker compose -f docker-compose.prod.yml exec api python manage.py seed_demo
.\scripts\local-prod-smoke.ps1
```

Demo credentials: `manager@demo.local` / `demo1234` (see `.env.example`).

Skip login check: `$env:SKIP_LOGIN_SMOKE = "1"; .\scripts\local-prod-smoke.ps1`

## Post-start checklist (A1)

- [ ] `docker compose -f docker-compose.prod.yml ps` — `api`, `worker`, `beat` healthy
- [ ] BFF health: http://127.0.0.1:3000/api/v1/health/ready/ → 200
- [ ] Admin: http://127.0.0.1:3000/admin/
- [ ] Optional: `seed_demo` + login smoke passes
- [ ] Knowledge index (after first tenant data): `docker compose -f docker-compose.prod.yml exec api python manage.py reindex_knowledge`
- [ ] Full autotest suite green locally (see [testing-strategy.md](../quality/testing-strategy.md))

## Validate compose file (no build)

```powershell
docker compose -f docker-compose.prod.yml config
```

## Stop / reset

```powershell
docker compose -f docker-compose.prod.yml down
# Full reset including DB volume:
docker compose -f docker-compose.prod.yml down -v
```

## Troubleshooting

| Symptom | Check |
|---|---|
| `POSTGRES_PASSWORD` error | `.env` missing or variable unset — copy from `.env.local-prod.example` |
| `api` unhealthy | `docker compose -f docker-compose.prod.yml logs api --tail 80` — often `DJANGO_SECRET_KEY` &lt; 32 chars or missing `AI_CREDENTIALS_KEY` |
| BFF health 502/504 | `web` started before `api` ready — wait and retry smoke |
| Login smoke skipped (401) | Run `seed_demo` (see above) |
| Port 3000 in use | Set `WEB_PORT=3001` in `.env` and rebuild `web` |

## Related

- [deployment.md](deployment.md) — full production deploy (VPS, TLS, firewall)
- [integrator-vps-pilot.md](integrator-vps-pilot.md) — tenant onboarding (same steps on localhost for A2)
