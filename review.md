# Production Readiness Audit — AI Sales OS

Дата: 2026-06-10 · Коммит: `d3a91ef` (P4c)  
Сценарий: **VPS + первые pilot-пользователи** (Google Sheets CRM, invite-only, integrator в Admin)  
Метод: код + docs + 5 параллельных аудитов (backend, frontend, security, RAG/LLM, docs/PRD)

---

## Итоговая оценка

| Метрика | Балл |
|---|---:|
| **Готовность к VPS + первым пользователям** | **61 / 100** |
| **Pilot path с integrator'ом** (Admin + Sheets, без телефонии) | **68 / 100** |
| **Production-grade** (SLO, staging, полный PRD, compliance) | **45 / 100** |

**Вердикт:** к **ограниченному пилоту на VPS** можно идти **после закрытия P0** (Admin-доступ, prod secrets, LLM throttle, runbook). Полноценный prod — ещё 2–3 итерации (P5 + ops + QA sign-off).

---

## Оценка по 10 блокам

| # | Блок | /10 | /100 | Комментарий |
|---|---|---:|---:|---|
| 1 | **Backend** | 7.0 | 70 | Prod settings, Docker, Postgres, Celery, CRM query, auth — зрелые. Минус: Admin onboarding, Sheets не даёт KPI дашборда |
| 2 | **Frontend** | 7.0 | 70 | Все страницы, BFF cookies, CI build/lint/e2e. Минус: mobile, route guards, error boundaries |
| 3 | **User flow** | 6.0 | 60 | FLOW-001…007 в коде; pilot = Admin + invites + Sheets. Нет password reset, review edit, upload в агент |
| 4 | **Стабильность** | 6.0 | 60 | 103 API tests, health/ready, backup docs. Минус: нет Sentry/staging, Beat без мониторинга, LocMem throttle |
| 5 | **Документация** | 5.0 | 50 | Architecture post-P4c OK; release-checklist, PRD статусы, DoD, support — устарели/пусты |
| 6 | **Безопасность (требования)** | 6.0 | 60 | Tenant isolation, httpOnly JWT, scope, Fernet — сильно. CSP, audit gaps, LLM abuse — слабо |
| 7 | **Риски** (взлом, ключи, DDoS, prompt injection) | 5.5 | 55 | См. матрицу рисков ниже |
| 8 | **RAG + vector** | 6.0 | 60 | pgvector end-to-end в prod CI; нет index/chunking/monitoring embed failures |
| 9 | **Зрелость процесса** | 5.5 | 55 | Код L2–L3, процесс QA/Legal/Support L1 |
| 10 | **Этапы до прода** | 6.0 | 60 | Deploy docs есть; runbook integrator/tenant — нет; 8 фаз ниже |

**Среднее (равные веса): 61/100**

---

## P0 — блокеры перед VPS

| ID | Блокер | Действие |
|---|---|---|
| **P0-1** | **Django Admin недоступен через BFF** — onboarding только Admin | Проксировать `/admin/` на api **или** VPN/port-forward для integrator |
| **P0-2** | **Prod secrets** — без них Django не стартует / demo-fallback | `DJANGO_SECRET_KEY`, `AI_CREDENTIALS_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`, `CORS` |
| **P0-3** | **LLM/STT cost abuse** — нет throttle на reports/upload/custom-reports | Rate limit на LLM-heavy endpoints до первых пользователей |
| **P0-4** | **OpenRouter + PII** — транскрипты/KB в промптах | DPA/согласие с первым tenant до реальных данных |
| **P0-5** | **Integrator runbook отсутствует** | ✅ [`docs/operations/integrator-vps-pilot.md`](docs/operations/integrator-vps-pilot.md) |

---

## P1 — важно для пилота

- Throttle cache → **Redis** (сейчас LocMem × workers)
- **Beat/Redis** без healthcheck и persistence volume
- **Dashboard KPI** пустой при только Google Sheets (hero metrics = demo telephony или empty)
- **Python 3.12 (Docker) vs 3.13 (CI)** — выровнять
- **requirements.txt vs lock** в Dockerfile
- **GAP-001** cross-tenant IDOR — расширить тесты
- **Docs drift:** `release-checklist.md`, `roadmap-data-integration.md`, PRD все `draft`
- **Нет staging** — прямой deploy на VPS

---

## Матрица рисков

| Риск | L | I | Mitigation сейчас | Gap |
|---|---|---|---|---|
| **Tenant IDOR** | L | H | Scope filters + tests | GAP-001 partial |
| **Кража JWT** | L | H | httpOnly, Secure, rotation | Токены ещё в JSON body login |
| **Кража ключей (.env)** | M | H | Fernet, prod fail-fast | Ops discipline на VPS |
| **DDoS login/register** | M | M | 10/min throttle | LocMem не shared |
| **DDoS agent/LLM** | M | H | Agent 30/min | Reports/STT/upload без limit |
| **Prompt injection (agent)** | M | M | Scope RAG; weak system prompt | Нет sandbox user vs context |
| **KB poison** | L | M | ACL grants | Менеджер может залить вредный RAG |
| **XSS → session abuse** | L | H | React escape | **Нет CSP** |
| **Admin/swagger leak** | L | H | API internal in compose | Misconfigured nginx |
| **Beat down → stale CRM** | M | M | Hourly cron | Нет алертов |
| **Backup failure** | M | H | Scripts + docs | Restore drill не проведён |

---

## Demo vs Real (что увидят первые пользователи)

| Компонент | Pilot (real) | Demo / fallback |
|---|---|---|
| CRM лиды | Google Sheets → `CrmLead` | — |
| Клиенты к разбору | `review_rules` + sync | — |
| Agent CRM queries | SQL + rule-based NL | LLM parse optional |
| Dashboard KPI | **empty/partial** без demo sources | Demo: calls=8, quality=78 |
| Telephony | **wishlist** | Demo metrics |
| AI agent / analytics LLM | OpenRouter | Rule-based без ключа |
| RAG semantic search | pgvector + embed | Keyword-only без ключа |
| STT | OpenRouter Whisper | `demo_v1` transcript |

---

## RAG / Vector / LLM (сводка)

**Работает:** embed on save, pgvector CI job, ACL на статьях, agent RAG + CRM tools, 90d retention, tenant LLM keys.

**Не хватает:** HNSW index, chunking, cost accounting, alert на failed embed, `reindex_knowledge` в pilot checklist, staging smoke.

**Без API keys:** UI живой, но semantic RAG и LLM-ответы = keyword/demo.

---

## Соответствие PRD

| Область | Статус |
|---|---|
| REQ-001…014 User Level | ✅ Код + тесты |
| REQ-015 интеграции | ⚠️ CRM Sheets real; telephony/reporting demo |
| REQ-016 записи | ⚠️ Manual upload + STT; webhook wishlist |
| QA-AC формальная приёмка | ❌ Большинство `draft` |
| Integration Level UI | ❌ By design — Admin only |

---

## Зрелость (L1–L3)

| Область | Уровень |
|---|---|
| Backend / CRM P4c | **L2–L3** |
| Frontend MVP | **L2** |
| Security auth/scope | **L2** |
| Ops deploy/backup | **L2** |
| QA process / DoD | **L1** |
| Legal / support runbooks | **L1** |
| Monitoring / Sentry | **L1** |

---

## 8 этапов до первых пользователей на VPS

1. **Закрыть P0** — Admin proxy, prod `.env`, LLM throttles, DPA
2. **Runbook** — [`docs/operations/integrator-vps-pilot.md`](docs/operations/integrator-vps-pilot.md)
3. **VPS** — Docker, TLS, firewall, `docker-compose.prod.yml` (api, worker, **beat**, web, postgres, redis)
4. **Smoke** — `/api/v1/health/ready/`, backup cron, restore drill
5. **Tenant #1** — Admin: Tenant, Workspace, Invite, IntegrationSource + Sheets SA
6. **LLM** — keys + `reindex_knowledge` + smoke agent/analytics
7. **Users** — `/register` → login → CRM sync → clients + agent query
8. **Pilot gate** — manual QA-AC 001–004, мониторинг логов 48h

---

## Pilot checklist (integrator)

Полная пошаговая инструкция: **[integrator-vps-pilot.md](docs/operations/integrator-vps-pilot.md)**.

Краткий чеклист:

1. Django Admin доступен (`https://<domain>/admin/` через BFF)
2. Tenant, Workspace, `RegistrationInvite`
3. Google Sheet + `IntegrationSource` (`config_json` template pre-filled)
4. Share sheet с service account email
5. `OPENROUTER_API_KEY` + `AI_CREDENTIALS_KEY` + `reindex_knowledge`
6. Users: email = `manager_email` в sheet
7. Login → sync → «Клиенты к разбору» по `review_rules`
8. Agent: «Сколько клиентов…» → ответ с `Данные на …`

---

## Wishlist (не блокирует pilot)

| # | Задача |
|---|---|
| P4b | Telephony — **не интегрируем** до продуктового решения |
| P4b | Reporting adapters |
| P5 | Sentry, staging, CSP, Integration UI |

---

## Тесты и CI

**103** API (3 pgvector skipped on SQLite) · **23** Vitest · **2** Playwright E2E · lint · **api-postgres**

Gaps: agent throttle 429 test, prod compose smoke, cross-tenant IDOR matrix.

---

## CRM (P4b-GS + P4c)

| Компонент | Реализация |
|---|---|
| Источник | Google Sheets (`provider: google_sheets`) |
| Модель | `CrmLead` DB cache; agent не читает live Sheets |
| Sync | Hourly Beat + throttled login + on-demand (agent/manual) |
| ClientToReview | Explicit `review_rules` only |
| Manager agent | NL → SQL filters; `as_of: last_sync_at` |
| Admin | Pre-filled `config_json` template |
| amoCRM | Код есть, не pilot path |

---

## Резюме

**Pilot CRM = Google Sheets cache + on-demand agent queries**, не batch LLM и не 24/7 realtime sync.

**61/100** — честная оценка для VPS с первыми внешними пользователями: продуктовый MVP есть, ops/security/process догоняют код. С dedicated integrator и закрытием P0 — **реалистичный controlled pilot** (~68/100 по pilot path).

**План:** `plan_0.md` (локально) — P4b-GS ✅ · P4c ✅ · P4b telephony = wishlist.
