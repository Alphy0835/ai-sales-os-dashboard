Doc ID: OPS-LOCAL-GATE-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/integrator-vps-pilot.md, docs/operations/backup-and-restore.md, docs/quality/acceptance-criteria.md, plan_0.md
Update together with: scripts/restore-postgres-local.sh, scripts/restore-postgres-local.ps1, docker-compose.prod.yml
Update trigger: Gate A step change, localhost URL change, pilot seed credentials change
Review required: operations, QA
Maturity: L2

# Gate A — Local acceptance checklist

Actionable checklist for **Gate A** (локально готово) before VPS deploy. Run on **`docker-compose.prod.yml`** at `http://127.0.0.1:3000` unless noted.

**Pilot credentials (after A2 setup):** `pilot-mgr@local.test` / `pilot1234`  
**Demo credentials (dev / CI E2E):** `manager@demo.local` / `demo1234`

Related runbook (same steps, swap domain → localhost): [integrator-vps-pilot.md](integrator-vps-pilot.md)

---

## 0. Prerequisites

- [ ] Repo cloned; `.env` copied from `.env.example` with production-like values (`DJANGO_ENV=production`, strong `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`, `AI_CREDENTIALS_KEY`)
- [ ] Docker Engine + Compose v2 available
- [ ] Optional for LLM/agent: `OPENROUTER_API_KEY` in `.env`
- [ ] Google Sheets service account JSON ready (for A2 CRM)

**Local URLs (prod compose via BFF):**

| Resource | URL |
|---|---|
| Web / login | http://127.0.0.1:3000/login |
| Register | http://127.0.0.1:3000/register |
| Manager dashboard | http://127.0.0.1:3000/manager |
| Clients to review | http://127.0.0.1:3000/manager/clients |
| Manager agent | http://127.0.0.1:3000/manager/agent |
| Review history | http://127.0.0.1:3000/manager/reviews |
| AI analytics | http://127.0.0.1:3000/manager/analytics |
| Settings | http://127.0.0.1:3000/manager/settings |
| Employee dashboard | http://127.0.0.1:3000/employee |
| Employee agent | http://127.0.0.1:3000/employee/agent |
| Django Admin (BFF) | http://127.0.0.1:3000/admin/ |
| Health ready | http://127.0.0.1:3000/api/v1/health/ready/ |

---

## A1. Local prod-like stack

- [ ] Stack starts without errors:

  ```bash
  docker compose -f docker-compose.prod.yml build
  docker compose -f docker-compose.prod.yml up -d
  docker compose -f docker-compose.prod.yml ps
  ```

- [ ] Migrations applied (on `api` start) and knowledge indexed:

  ```bash
  docker compose -f docker-compose.prod.yml exec api python manage.py showmigrations | tail -5
  docker compose -f docker-compose.prod.yml exec api python manage.py reindex_knowledge
  docker compose -f docker-compose.prod.yml logs worker --tail 20
  ```

- [ ] **Smoke — health:** `curl -sf http://127.0.0.1:3000/api/v1/health/ready/` → HTTP 200

- [ ] **Smoke — Admin via BFF:** open http://127.0.0.1:3000/admin/ → login as superuser → Accounts visible

- [ ] **Smoke — login:** open http://127.0.0.1:3000/login → successful redirect to role home

- [ ] **Smoke — CRM sync** (after A2 IntegrationSource): manual sync or Beat → `IntegrationSource.status=connected`, `last_sync_at` updated

- [ ] **Full CI locally (automated gate):**

  ```bash
  cd apps/api && python manage.py test
  cd apps/web && npm run test:unit && npm run build
  cd apps/web && npm run test:e2e
  ```

  Playwright uses demo seeds (`manager@demo.local`). Pilot smoke (optional): see [§ A3 Playwright pilot smoke](#a3-playwright-pilot-smoke).

---

## A2. Demo tenant #1 (localhost)

Follow [integrator-vps-pilot.md](integrator-vps-pilot.md) §5–11 with **localhost** URLs above.

- [ ] Superuser created: `docker compose -f docker-compose.prod.yml exec -it api python manage.py createsuperuser`

- [ ] **Admin → Tenant** (e.g. slug `pilot-co`) + **Workspace** (e.g. «ОП Москва»)

- [ ] **Admin → RegistrationInvite** for manager role; note invite code

- [ ] **IntegrationSource** (`google_sheets`): spreadsheet shared with service account, `config_json` + credentials saved, first sync OK

- [ ] **Register with invite:** http://127.0.0.1:3000/register — email matches `manager_email` in sheet → auto-login → manager home

- [ ] **Pilot manager login** (if user created manually or via register): `pilot-mgr@local.test` / `pilot1234` → http://127.0.0.1:3000/manager

- [ ] **CRM sync after login:** «Клиенты к разбору» shows rows from sheet review rules

- [ ] **Agent smoke:** http://127.0.0.1:3000/manager/agent — ask «Сколько клиентов…» → answer includes **`Данные на …`** (`as_of: last_sync_at`)

- [ ] **Dashboard deals:** hero KPI `deals` visible from `CrmLead` (Sheets path; telephony KPI may stay empty — expected)

- [ ] **Stale CRM flag:** dashboard/metrics show stale indicator when `last_sync_at` is old (B1-5)

---

## A3. Manual QA-AC 001–004 (localhost)

Source: [acceptance-criteria.md](../quality/acceptance-criteria.md). Login as **pilot manager** (`pilot-mgr@local.test`) unless using demo tenant.

### QA-AC-001 — Department metrics (today / week / month)

**Criteria:** Manager with dashboard `view` sees department metrics for today, current week, and month, trends and gap vs norm.

- [ ] Login → http://127.0.0.1:3000/manager
- [ ] Confirm blocks: **сегодня**, **текущая неделя**, **текущий месяц**, динамика, отставание от нормы
- [ ] Metrics reflect connected sources (Sheets → deals/clients; telephony may be partial/empty)

### QA-AC-002 — Scope filter (workspace / employee)

**Criteria:** Manager selects workspace or employee and sees scoped metrics; out-of-scope objects denied.

- [ ] On dashboard, select **подразделение** → metrics update for that scope
- [ ] Select **сотрудник** → metrics update for employee
- [ ] Attempt to access out-of-scope data (API or UI) → access denied / not listed

### QA-AC-003 — AI summary on dashboard

**Criteria:** With sufficient data, AI summary (drops, attention zones, praise/control) visible; without data — numeric metrics only, summary hidden.

- [ ] **With data:** AI summary block visible on http://127.0.0.1:3000/manager
- [ ] **Without AI data:** summary hidden; numeric KPI blocks still render

### QA-AC-004 — Clients to review (scoped)

**Criteria:** «Клиенты к разбору» lists clients with rationale only within manager scope.

- [ ] Open http://127.0.0.1:3000/manager/clients
- [ ] List shows clients with **обоснование** from CRM/review rules
- [ ] Clients outside manager scope are **not** shown

---

## A3. Restore drill (local volume)

Uses [`scripts/restore-postgres-local.sh`](../../scripts/restore-postgres-local.sh) / [`.ps1`](../../scripts/restore-postgres-local.ps1). Full reference: [backup-and-restore.md](backup-and-restore.md).

- [ ] **1. Fresh backup**

  ```bash
  ./scripts/backup-postgres.sh
  # Windows: .\scripts\backup-postgres.ps1
  ls -lh backups/*.sql.gz | tail -1
  ```

- [ ] **2. Baseline row count (optional)**

  ```bash
  docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U ai_sales_os -d ai_sales_os -c "SELECT COUNT(*) FROM accounts_user;"
  ```

- [ ] **3. Restore** (destructive — overwrites DB)

  ```bash
  ./scripts/restore-postgres-local.sh backups/ai_sales_os_YYYYMMDD_HHMMSS.sql.gz
  ```

  ```powershell
  .\scripts\restore-postgres-local.ps1 backups\ai_sales_os_YYYYMMDD_HHMMSS.sql.gz
  ```

- [ ] **4. Verify health**

  ```bash
  docker compose -f docker-compose.prod.yml ps
  curl -sf http://127.0.0.1:3000/api/v1/health/ready/
  ```

- [ ] **5. Verify data** — row counts match baseline; known tenant/user still present

- [ ] **6. Smoke after restore** — login at http://127.0.0.1:3000/login → dashboard loads → spot-check tenant record in Admin

- [ ] **7. Document** — date, operator, backup filename, pass/fail, issues

---

## A3. Playwright pilot smoke

Optional automated smoke after A2 tenant exists (skipped in default CI).

```bash
# Stack on :3000; pilot user must exist
cd apps/web
E2E_PILOT_LOCAL=1 npm run test:e2e -- pilot-local-smoke
```

- [ ] `pilot-local-smoke.spec.ts` passes with `E2E_PILOT_LOCAL=1`

---

## User flows — Manager (localhost)

Login: `pilot-mgr@local.test` / `pilot1234` (or demo manager after `seed_demo` on dev stack).

| Step | Action | URL | Done |
|---|---|---|---|
| M1 | Login → manager home | http://127.0.0.1:3000/login | [ ] |
| M2 | Dashboard overview (FLOW-001) | http://127.0.0.1:3000/manager | [ ] |
| M3 | Clients to review | http://127.0.0.1:3000/manager/clients | [ ] |
| M4 | Create review + tasks (FLOW-002) | http://127.0.0.1:3000/manager/reviews | [ ] |
| M5 | AI analytics + canvas (FLOW-003) | http://127.0.0.1:3000/manager/analytics | [ ] |
| M6 | Manager agent + CRM question (FLOW-005) | http://127.0.0.1:3000/manager/agent | [ ] |
| M7 | Settings / criteria / KB (FLOW-004) | http://127.0.0.1:3000/manager/settings | [ ] |

---

## User flows — Employee (localhost)

Invite/register employee or use demo `employee@demo.local` / `demo1234` on dev stack.

| Step | Action | URL | Done |
|---|---|---|---|
| E1 | Register with employee invite (A2) | http://127.0.0.1:3000/register | [ ] |
| E2 | Personal dashboard + tasks (FLOW-006) | http://127.0.0.1:3000/employee | [ ] |
| E3 | Update task status | http://127.0.0.1:3000/employee | [ ] |
| E4 | Employee agent (FLOW-007) | http://127.0.0.1:3000/employee/agent | [ ] |
| E5 | Logout | — | [ ] |

---

## Gate A sign-off

**DoD Gate A:** demo tenant end-to-end on localhost/docker; all automatable tests green; QA-AC 001–004 passed manually; restore drill passed.

| Item | Pass | Date | Operator |
|---|---|---|---|
| A1 stack + smoke | [ ] | | |
| A2 demo tenant | [ ] | | |
| QA-AC 001–004 | [ ] | | |
| Restore drill | [ ] | | |
| User flows M1–M7, E1–E5 | [ ] | | |
| CI tests green | [ ] | | |

---

## Related

- [integrator-vps-pilot.md](integrator-vps-pilot.md) — tenant + Sheets setup
- [backup-and-restore.md](backup-and-restore.md) — backup schedule, managed Postgres
- [acceptance-criteria.md](../quality/acceptance-criteria.md) — QA-AC full index
- [testing-strategy.md](../quality/testing-strategy.md) — local E2E setup
