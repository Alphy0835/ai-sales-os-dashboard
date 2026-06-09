# Code Review — AI Sales OS

Дата: 2026-06-10 (полный аудит) · Предыдущий: 2026-06-09  
Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура  
Состояние: STAGE-001…007 + **P0/P1/P2 закрыты**; CI зелёный на `master` (`06297b4`).

**Тесты:** 51 API · 12 Vitest · 1 Playwright E2E (CI) · `test.bat` гоняет 46 (без `core.tests`).

**План закрытия дыр:** локальный `plan_0.md` (не в git).

---

## 1. Целостность проекта

### Что хорошо

- Монорепо консистентно: `apps/api` (6 Django-приложений), `apps/web`, `docs/`, лаунчеры.
- **51** API-тест + **12** Vitest + E2E в CI — регрессия по STAGE-001…007.
- Multi-tenant (`tenant_id`) + manager scope + ceiling rule последовательны.
- httpOnly JWT через Next.js BFF + `CookieJWTAuthentication` + refresh blacklist на logout.
- Сквозные сценарии: клиенты → разбор → задачи → AI-аналитика → кастомные отчёты → Access UI.

### Проблемы целостности (открытые)

| # | Проблема | Где | Серьёзность |
|---|---|---|---|
| C2 | `TenantMiddleware` декоративный — изоляция на уровне views/services, не middleware/managers | `core/middleware.py`, `data-model.md` | Средняя |
| C6 | Модуль **`clients`** grantable, но API/UI проверяют только `dashboard: view` | `analytics/views.py`, `AppShell.tsx` | Средняя |
| C7 | Nav не скрывает модули с `permissions: none` — 403 вместо forbidden UX | `AppShell.tsx` | Средняя |
| C8 | `fetchMe()` failure → logout вместо forbidden для inactive/403 | `ProtectedShell.tsx` | Средняя |

### Закрытые (C1, C3–C5)

| # | Было | Статус |
|---|---|---|
| C1 | Refresh flow | ✅ cookies + `authFetch` refresh on 401 |
| C3 | JWT localStorage | ✅ httpOnly BFF cookies |
| C4 | No throttling | ✅ login 10/min, agent 30/min |
| C5 | Settings redesign uncommitted | ✅ в git |

### 1.1. Security-аудит (2026-06-09) — исправлено

| # | Уязвимость | Исправление |
|---|---|---|
| S1 | Scope leak в AI-агенте | `recordings_queryset(actor)` |
| S2 | Tenant-wide AI-отчёты | `reports_queryset(actor)` |
| S3 | Brute force login | `LoginRateThrottle`, `AgentRateThrottle` |
| S4 | Upload без валидации | 100 MB + whitelist расширений |
| S5 | 500 на bad session_id | 404 |
| S6 | 500 на `?limit=abc` | Safe parse |

Тесты: `ai/tests/test_security_scope.py` (4).

### 1.2. Полный аудит (2026-06-10) — остаточные риски

| # | Риск | Severity | Статус |
|---|---|---|---|
| R1 | Cross-tenant IDOR — код фильтрует, **нет regression-теста** | Medium | Открыт |
| R2 | Cookie refresh/logout — **1 API-тест**, нет refresh-via-cookie/blacklist suite | Medium | Открыт |
| R3 | LLM fallback не assert'ится при `LlmAdapterError` | Low | Открыт |
| R4 | Throttling не тестируется (отключён в TESTING) | Low | Открыт |
| R5 | Upload validation — код есть, **тестов нет** | Low | Открыт |
| R6 | Demo transcripts/metrics в prod — продуктовый риск | High (product) | Осознан defer |

### Проверено — CVE-класс не найден

- Межтенантная изоляция в queryset'ах · IDOR на detail-views · ORM-only · XSS (нет `dangerouslySetInnerHTML`) · ceiling + audit.

---

## 2. Backend vs документация

**Совпадает:** все STAGE endpoints, scope, permissions, KB grants (API-PERM-004), health/ready, retention, pgvector (PostgreSQL).

**Критичные расхождения docs ↔ code:**

| ID | Проблема | Файлы |
|---|---|---|
| B-H1 | Auth docs описывают Bearer/localStorage; код — **cookies primary** | `auth-and-access-control.md`, `api-contracts.md`, `frontend-docs.md` |
| B-H2 | `threat-model.md` L28 всё ещё «JWT в localStorage» | `docs/security/threat-model.md` |
| B-H3 | `api-contracts.md` index неполный (нет REV/AI/KB/AGENT/PERM-004) | `api-contracts.md` |
| B-M1 | `data-model.md` index устарел (нет Review, AI entities) | `data-model.md` |
| B-M2 | `backend-docs.md`: integrations planned, S3, wrong Celery task name | `backend-docs.md` |
| B-M3 | `roadmap.md` index: STAGE-007 «planned» vs body «done» | `roadmap.md` |
| B-M4 | Audit API только `permission_change`; в коде есть `review_create` | `accounts/views.py` |

---

## 3. Frontend vs документация

**Совпадает:** PAGE-001…009, BFF cookies, PAGE-006 (4 вкладки), основные flows.

**Критичные gaps:**

| ID | Проблема | Файлы |
|---|---|---|
| F-H1 | Permission-based nav отсутствует | `AppShell.tsx` |
| F-H2 | Forbidden/inactive → logout | `ProtectedShell.tsx`, `api.ts` |
| F-H3 | `deployment.md` советует cross-origin API URL — **ломает BFF cookies** | `deployment.md` vs `.env.example` |
| F-H4 | Cross-page links из `pages-map.md` не реализованы | `ClientsToReview`, `ManagerDashboard`, `AiAnalytics` |

**Средние:** нет Z-FILTERS (clients), Z-TREND (employee), слабые error/retry states, нет `middleware.ts`.

---

## 4. Тестирование

| Слой | Count | CI | Gaps |
|---|---|---|---|
| API | 51 | ✅ | cookie lifecycle, cross-tenant, throttle, upload validation |
| Vitest | 12 | ✅ | только `auth.ts`/`api.ts`, моки |
| Playwright | 1 | ✅ | employee flow, logout, permission denied |
| Lint | — | ❌ не в CI | `npm run lint` |

**Локально:** `test.bat` / `start-dev.ps1 -RunTests` → **46** тестов (пропускает `core.tests`).

**Docs:** `testing-strategy.md` ✅ · `test-matrix.md` пуст · `release-checklist.md` skeleton · `security-checklist.md` частично устарел vs код.

---

## 5. Документация — статус

### Заполнено (P0–P2)

`deployment.md`, `rollback.md`, `backup-and-restore.md`, `data-retention.md`, `privacy-policy-notes.md`, `data-processing-agreement.md`, `threat-model.md`, `security-checklist.md`, `incident-response.md`, `monitoring-and-alerts.md`, `testing-strategy.md`, sync `stack.md` / `data-model.md`.

### Ещё пустые / skeleton (~50 файлов)

`test-matrix.md`, `release-checklist.md`, `definition-of-done.md`, marketing/*, support/*, `environments.md` (staging TBD).

### Прочие несоответствия

- Auth/security docs отстают от httpOnly cookies (см. B-H1, B-H2).
- `data-model.md`: custom managers (C2).
- QA-AC-013/014 — **passed**.

---

## 6. Roadmap P0–P2 — статус реализации

### P0 ✅ закрыт (2026-06-09)

Token refresh → cookies · prod Django · throttling · CI · lock file · prod compose · backups.

### P1 ✅ частично (2026-06-09)

| # | Статус |
|---|---|
| 8 ASR | ⏸ отложено (demo `content_json`) |
| 9 LLM | ✅ OpenRouter adapter + fallback |
| 10 pgvector | ✅ embeddings + vector search |
| 11 Integrations | ⏸ demo sync |
| 12 Access UI | ✅ PAGE-006 + API-PERM-004 |

### P2 ✅ закрыт (2026-06-09, без Sentry)

JSON logs · `/health/ready/` · E2E + Vitest · security/legal docs · stack sync · httpOnly BFF.

### P3 — deploy + prod gaps (новый, см. `plan_0.md`)

Deploy blockers, doc sync, frontend UX, test gaps, ASR/integrations product work.

---

## 7. Готовность к продакшену

**Вердикт:** pilot/staging с ручным ops — **после P3-deploy blockers**. Unattended B2B SaaS — **рано**.

### Готово

Prod compose · prod settings · backups scripts · health/ready · rate limits · httpOnly JWT · CI · JSON logs.

### Deploy blockers (P3-D0)

| # | Блокер |
|---|---|
| D1 | `docker-compose.prod.yml`: нет `API_BACKEND_URL=http://api:8000`, `NEXT_PUBLIC_API_URL=` |
| D2 | `SECURE_SSL_REDIRECT` без `SECURE_PROXY_SSL_HEADER` → redirect loop за nginx/Caddy |
| D3 | Docker healthcheck API может получить 301 на HTTP |
| D4 | Celery Beat / cron для `purge_expired_transcripts` не настроен |
| D5 | Backups — скрипты есть, cron/off-host вручную |
| D6 | Reverse proxy + TLS + firewall (только 80/443) |
| D7 | Web: `npm run build` на каждый start — не baked image |

### Продуктовые defer (осознанно)

Demo ASR · demo integrations · agent chat retention indefinite · Sentry optional.

### VPS sizing (single-node Docker)

| Профиль | vCPU | RAM | Disk |
|---|---|---|---|
| Pilot min | 2 | 4 GB | 40 GB SSD |
| Recommended | 4 | 8 GB | 80 GB SSD |
| Growth 50+ | 4–8 | 16 GB | 160 GB+ |

LLM/STT — внешние (OpenRouter). Нагрузка: Postgres embeddings, Gunicorn, Celery, Next.

---

## 8. Рекомендуемый порядок (обновлён)

```
✅ P0–P2 roadmap: закрыт (кроме ASR, integrations, Sentry)
→ P3-D0: deploy blockers (7 пунктов) — перед VPS
→ P3-D1: doc sync + frontend UX + tests
→ P4: ASR + real integrations
→ P5: Sentry, staging env, CSP, agent retention policy
```

---

## Резюме

User Level MVP + P0/P1/P2 **реализованы и покрыты CI**. Остаётся: **deploy blockers на VPS**, **doc drift (auth)**, **frontend permission UX**, **test gaps (cookies, cross-tenant)**, **ASR/integrations** для реального продукта. Детальный план — `plan_0.md` (локально).
