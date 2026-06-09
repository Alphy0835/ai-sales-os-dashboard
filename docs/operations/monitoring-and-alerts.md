Doc ID: OPS-MONITOR-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/deployment.md, docs/architecture/api-contracts.md, docker-compose.prod.yml
Update together with: deployment.md, api-contracts.md, apps/api/config/settings.py
Update trigger: new health check, log format change, alert rule change
Review required: operations, backend
Maturity: L2

# Monitoring and Alerts

MVP observability for AI Sales OS: **structured JSON logs** on stdout and **HTTP health endpoints** for liveness/readiness. No external APM (e.g. Sentry) in this slice — logs and probes integrate with your host or orchestrator (Docker, Kubernetes, cloud log drain).

## Health endpoints

| Endpoint | Purpose | Expected | Use |
|---|---|---|---|
| `GET /api/v1/health/` | **Liveness** — process is up | Always `200` if Gunicorn/Django responds | Load balancer ping; restart if process dead |
| `GET /api/v1/health/ready/` | **Readiness** — dependencies OK | `200` when DB + Redis + Celery worker respond; `503` otherwise | Deploy gate, Docker healthcheck, traffic routing |

### Readiness checks

| Check | What it verifies |
|---|---|
| `database` | `connection.ensure_connection()` against configured DB |
| `redis` | `PING` on `CELERY_BROKER_URL` (Redis broker) |
| `celery` | `app.control.inspect().ping()` — at least one worker responds |

### Example readiness response

**200 — all checks pass**

```json
{
  "status": "ok",
  "service": "ai-sales-os-api",
  "checks": {
    "database": { "status": "ok" },
    "redis": { "status": "ok" },
    "celery": { "status": "ok" }
  }
}
```

**503 — dependency failure**

```json
{
  "status": "error",
  "service": "ai-sales-os-api",
  "checks": {
    "database": { "status": "ok" },
    "redis": { "status": "ok" },
    "celery": { "status": "error", "error": "no workers responded" }
  }
}
```

### Production Docker

[`docker-compose.prod.yml`](../../docker-compose.prod.yml) configures the `api` service healthcheck against `/api/v1/health/ready/`. Postgres and Redis have their own compose healthchecks; the API readiness probe confirms the app can use them and that a Celery worker is reachable.

## Structured logging (API)

Django logs to **stdout** as **JSON** via `python-json-logger` (`LOGGING` in `apps/api/config/settings.py`).

| Env var | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Root logger level |
| `DJANGO_LOG_LEVEL` | `INFO` | Django framework logger |

Each line is a JSON object (timestamp, logger name, level, message). Ship container stdout to your log aggregator (CloudWatch, Loki, Datadog, ELK, etc.) and query/filter on `levelname`, `name`, and message fields.

Readiness check failures are logged at `WARNING` on the `core.views` logger with the error detail.

## What to monitor (minimum)

| Signal | Source | Alert when |
|---|---|---|
| API uptime | LB or synthetic probe on `/health/` | Non-200 for > 1 min |
| API ready | `/health/ready/` or Docker health | `503` or unhealthy for > 2 min |
| Error rate | JSON logs (`levelname`: ERROR) | Spike vs baseline |
| Postgres | Compose `pg_isready` / host metrics | Unhealthy or disk > 80% |
| Redis | Compose `redis-cli ping` | Unhealthy |
| Celery queue depth | Redis / Flower (optional) | Backlog growing without drain |
| Worker process | Container restart count | Frequent restarts |

## Alert routing (configure on your platform)

Define who gets paged vs emailed in your incident tool (PagerDuty, Opsgenie, Slack webhook, etc.). Suggested tiers:

| Severity | Condition | Notify |
|---|---|---|
| **P1** | API readiness failing in prod; DB unreachable | On-call engineer |
| **P2** | Celery workers down; elevated 5xx on API | Engineering channel |
| **P3** | Elevated login throttle / disk warning | Daily digest |

Document on-call rotation in [`incident-response.md`](../security/incident-response.md) when that runbook is filled (P2 roadmap item).

## Related

- Deploy and verify: [deployment.md](deployment.md)
- Endpoint contract: [api-contracts.md](../architecture/api-contracts.md) — API-HEALTH-001, API-HEALTH-002
