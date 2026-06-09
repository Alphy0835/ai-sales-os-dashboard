# Code Review — AI Sales OS

Дата: 2026-06-09 · Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура
Состояние: STAGE-001…007 + **P0/P1/P2 закрыты** (2026-06-09), **51** API-тестов, **12** Vitest, Playwright E2E в CI.

---

## 1. Целостность проекта

### Что хорошо

- Монорепо консистентно: `apps/api` (6 Django-приложений), `apps/web`, `docs/`, лаунчеры.
- Все **45** API-тестов проходят (включая knowledge grants, security scope).
- Multi-tenant фильтрация (`tenant_id`) применяется во всех queryset'ах последовательно.
- Права (`ModulePermission`) проверяются в каждой view; есть scope-иерархия руководителей и аудит-лог.
- Сквозные сценарии работают: очередь клиентов → разбор → задачи сотрудника → AI-аналитика → кастомные отчёты.

### Проблемы целостности

| # | Проблема | Где | Серьёзность |
|---|---|---|---|
| C1 | ~~Refresh-токен без flow обновления~~ — **исправлено**: центральный `authFetch` с refresh на 401 | `apps/web/src/lib/api.ts` | — |
| C2 | `TenantMiddleware` ставит `request.tenant`, но views используют `user.tenant_id` напрямую — middleware фактически декоративный. `data-model.md` утверждает «enforced via middleware + custom managers», что не соответствует коду | `apps/api/core/middleware.py` | Средняя |
| C3 | ~~JWT в localStorage~~ — **исправлено**: httpOnly cookies через Next.js BFF proxy + `CookieJWTAuthentication` | `apps/web/next.config.ts`, `accounts/cookies.py` | — |
| C4 | ~~Нет rate limiting / throttling на `/auth/login/`~~ — **исправлено** (см. §1.1) | DRF settings | — |
| C5 | ~~Незакоммичены изменения редизайна настроек~~ — **исправлено** | — | — |

### 1.1. Security-аудит кода (2026-06-09) — найдено и исправлено

Углублённая проверка авторизации, межтенантной изоляции и обработки ввода.

| # | Уязвимость | Было | Исправление |
|---|---|---|---|
| S1 | **Утечка scope через AI-агента**: `_recording_context` фильтровал записи только по `tenant_id` — региональный менеджер мог получить контекст транскрипций чужих подразделений через имя клиента | `ai/services/agent.py` | Используется `recordings_queryset(actor)` с полной scope-фильтрацией |
| S2 | **Список AI-отчётов tenant-wide**: менеджер с `analytics: view` видел отчёты (summary, canvas) всех подразделений тенанта вне своего scope | `ai/views.py` | Новый `reports_queryset(actor)` — фильтр по workspace из scope менеджера |
| S3 | **Brute force на логин**: throttling отсутствовал | `accounts/views.py`, settings | `LoginRateThrottle` 10/min на login/refresh (env `THROTTLE_LOGIN`), `AgentRateThrottle` 30/min на агент-чаты (env `THROTTLE_AGENT`); в тестах отключено |
| S4 | **Загрузка файлов без валидации**: `audio_file` принимал любой тип и размер | `integrations/serializers.py` | Лимит 100 MB + whitelist расширений (mp3/wav/ogg/m4a/flac/webm), `duration_seconds >= 0` |
| S5 | 500 вместо 404: несуществующий/чужой `session_id` в агент-чате ронял запрос | `ai/services/agent.py`, `ai/views.py` | Обработка `DoesNotExist` → 404 |
| S6 | 500 на `?limit=abc` в аудите прав | `accounts/views.py` | Безопасный парсинг с fallback 50 |

Регрессионные тесты: `ai/tests/test_security_scope.py` (4 теста — изоляция scope для отчётов и контекста агента, 404 на неизвестную сессию).

### Проверено — уязвимостей не найдено

- **Межтенантная изоляция**: все queryset'ы фильтруют `tenant_id`, межтенантных дыр нет.
- **IDOR**: detail-views проверяют tenant + scope (`can_access_recording`, `resolve_client`, `_get_target`).
- **SQL-инъекции**: только ORM, raw SQL отсутствует.
- **XSS**: `dangerouslySetInnerHTML` не используется, React экранирует вывод.
- **Эскалация прав**: ceiling-проверка в `grant_permissions` + аудит отказов scope.

---

## 2. Корректность стека (заявленное vs реальное)

`docs/architecture/stack.md` заявляет компоненты, которые **не используются в коде**:

| Заявлено | Фактически | Риск |
|---|---|---|
| PostgreSQL 16 + **pgvector** | **Реализовано** (PostgreSQL): `VectorField` на `KnowledgeArticle`, Celery embed, vector search с keyword fallback | SQLite dev — keyword only |
| AI Adapter → **OpenRouter** | **Реализовано**: `llm_adapter.py` + tenant/workspace keys (Django Admin, Fernet); fallback rule-based | Без ключа — rule-based |
| **S3-compatible storage** | **Не используется по решению**: аудио не хранится; только транскрипты 90 дней | Осознанный отказ от S3 |
| Транскрипция | Demo-текст в `content_json`; **ASR отложен** — pluggable STT, transient audio | Следующий спринт |

Это осознанные MVP-срезы (помечены в roadmap-доках как «Not in this slice»), но в `stack.md` стоит явно пометить статус «planned», иначе документация вводит в заблуждение.

### Инфраструктурные несоответствия

- ~~Прод-компоуза нет~~ — **исправлено**: `docker-compose.prod.yml` (gunicorn без reload, без seed, migrate + collectstatic).
- ~~Lock-файл и CI~~ — **исправлено**: `requirements.lock.txt`, `.github/workflows/ci.yml`, Dependabot.
- ~~Prod Django settings~~ — **исправлено**: fail-fast SECRET_KEY ≥32, DEBUG=false, HSTS/secure-cookies, WhiteNoise.
- Dev `docker-compose.yml` по-прежнему с `--reload` и `seed_demo` — нормально для локальной разработки.

---

## 3. Дыры в документации

### Хорошо синхронизировано (source of truth актуален)

`roadmap.md` + 7 implementation-доков, `product-requirements.md`, `api-contracts.md`, `data-model.md`, `acceptance-criteria.md`, feature-docs, `user-flow.md`, design-guide, **`operations/deployment.md`**, **`operations/rollback.md`**, **`operations/backup-and-restore.md`** (заполнены в P0).

### Пустые шаблоны — ~57 файлов

Критичные для прода (ещё не заполнены):

| Документ | Почему критичен |
|---|---|
| ~~`operations/deployment.md`~~ | **заполнен** |
| ~~`operations/rollback.md`~~ | **заполнен** |
| ~~`operations/backup-and-restore.md`~~ | **заполнен** |
| `operations/monitoring-and-alerts.md` | Мониторинга нет ни в коде, ни в доке |
| `security/security-checklist.md` | Roadmap ссылается на «Auth / Access» секцию — файл пуст |
| `security/threat-model.md`, `incident-response.md` | Для SaaS с записями разговоров — обязательны |
| `quality/testing-strategy.md`, `release-checklist.md` | Definition of Done ссылается в никуда |
| ~~`legal/privacy-policy-notes.md`~~ | **заполнен** (MVP) |
| ~~`security/data-retention.md`~~ | **заполнен** (90d transcripts) |

Менее срочные: marketing/*, support/*, product/* — можно заполнять по мере выхода на рынок.

### Прочие несоответствия

- `data-model.md`: заявляет custom managers для tenant-фильтрации (см. C2).
- ~~QA-AC-013/014~~ — **passed**: вкладка Access в PAGE-006, API-PERM-004 knowledge grants.

---

## 4. План докрутки до прод-реализации

### P0 — блокеры прода ✅ **закрыт** (2026-06-09)

1. ~~**Token refresh flow**~~ — `authFetch()` + `refreshAccessToken()` в `apps/web/src/lib/api.ts`.
2. ~~**Прод-конфиг Django**~~ — `IS_PRODUCTION`, fail-fast SECRET_KEY, HSTS/secure-cookies, WhiteNoise.
3. ~~**Throttling**~~ — login 10/min, agent 30/min.
4. ~~**CI**~~ — `.github/workflows/ci.yml` (41 tests + migration check + web build).
5. ~~**Lock-файл + Dependabot**~~ — `requirements.lock.txt`, `.github/dependabot.yml`.
6. ~~**Прод-compose + deploy docs**~~ — `docker-compose.prod.yml`, `deployment.md`, `rollback.md`.
7. ~~**Бэкапы Postgres**~~ — `scripts/backup-postgres.sh/.ps1`, `backup-and-restore.md`.

### P1 — реальная функциональность ✅ **частично закрыт** (2026-06-09)

8. **ASR-транскрипция** — **отложено**; demo + `content_json`, аудио не персистится; STT adapter — следующий этап.
9. ~~**LLM-адаптер**~~ — OpenRouter-compatible, tenant→workspace keys, agent/custom reports/analytics summary + fallback.
10. ~~**Embeddings + pgvector**~~ — `VectorField`, Celery embed, vector search + keyword fallback.
11. **Интеграции** — **пропущено** по решению (demo sync остаётся).
12. ~~**REQ-013/014 UI**~~ — PAGE-006 Access: модули + audit + KB grants (API-PERM-004).

**Дополнительно:** retention 90d (`purge_expired_transcripts`), legal/data-retention docs.

### P2 — наблюдаемость, качество, документация ✅ **закрыт** (2026-06-09)

13. ~~**JSON logging + healthcheck**~~ — `/health/ready/` (DB/Redis/Celery), JSON stdout logs; **Sentry пропущен** по решению.
14. ~~**E2E + unit**~~ — Playwright `manager-critical-flow`, Vitest `auth.ts`/`api.ts`, CI job `e2e`.
15. ~~**Security docs**~~ — `threat-model.md`, `security-checklist.md`, `incident-response.md`.
16. ~~**Legal DPA**~~ — `data-processing-agreement.md` из privacy/retention notes.
17. ~~**stack.md + data-model.md**~~ — синхронизированы с кодом.
18. ~~**httpOnly JWT**~~ — BFF proxy + cookie auth + token blacklist logout.

### Рекомендуемый порядок

```
✅ Спринт 1 (P0): закрыт
✅ Спринт 2–3 (P1): LLM + pgvector + Access UI — закрыт; ASR + интеграции — отложены
✅ Спринт 4 (P2): закрыт (без Sentry)
Следующее: ASR, реальные интеграции, Sentry (опционально)
```

---

## Резюме

User Level MVP + **P0/P1/P2** реализованы. **ASR** и **реальные интеграции** — следующий этап. Опционально: Sentry, monitoring alerts automation.
