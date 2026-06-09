# Code Review — AI Sales OS

Дата: 2026-06-09 · Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура
Состояние: STAGE-001…007 реализованы, 41 API-тест проходит, `npm run build` зелёный.

---

## 1. Целостность проекта

### Что хорошо

- Монорепо консистентно: `apps/api` (6 Django-приложений), `apps/web`, `docs/`, лаунчеры.
- Все 37 API-тестов проходят, покрыты все стейджи (auth, integrations, dashboard, reviews, ai 005/006/007).
- Multi-tenant фильтрация (`tenant_id`) применяется во всех queryset'ах последовательно.
- Права (`ModulePermission`) проверяются в каждой view; есть scope-иерархия руководителей и аудит-лог.
- Сквозные сценарии работают: очередь клиентов → разбор → задачи сотрудника → AI-аналитика → кастомные отчёты.

### Проблемы целостности

| # | Проблема | Где | Серьёзность |
|---|---|---|---|
| C1 | Refresh-токен сохраняется в localStorage, но **flow обновления не реализован** — через 60 минут сессия молча умирает, все запросы падают | `apps/web/src/lib/auth.ts`, `api.ts` | Высокая |
| C2 | `TenantMiddleware` ставит `request.tenant`, но views используют `user.tenant_id` напрямую — middleware фактически декоративный. `data-model.md` утверждает «enforced via middleware + custom managers», что не соответствует коду | `apps/api/core/middleware.py` | Средняя |
| C3 | JWT в localStorage — уязвимо к XSS. Для MVP приемлемо, для прода нужен httpOnly cookie или хотя бы осознанное решение в threat-model | `apps/web/src/lib/auth.ts` | Средняя |
| C4 | ~~Нет rate limiting / throttling на `/auth/login/`~~ — **исправлено** (см. §1.1) | DRF settings | — |
| C5 | Незакоммичены изменения редизайна настроек (5 файлов + `SettingsPanelShell.tsx`) | git status | Низкая |

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
| PostgreSQL 16 + **pgvector** | pgvector-образ в compose есть, но embeddings нигде не используются; RAG — keyword-поиск по `tags`/`content` | Несоответствие доков; для прод-RAG нужны embeddings |
| AI Adapter → **OpenAI** | Нет ни одного вызова LLM: транскрипция — demo-заглушка (`tasks.py`), агент и отчёты — rule-based | Ядро продукта (REQ-007…012) работает на симуляции |
| **S3-compatible storage** | Не подключено; `ConversationRecording` не хранит реальные файлы | Записи разговоров негде хранить |
| Транскрипция | `transcribe_recording_task` генерирует фиктивный текст | Без реального ASR прод невозможен |

Это осознанные MVP-срезы (помечены в roadmap-доках как «Not in this slice»), но в `stack.md` стоит явно пометить статус «planned», иначе документация вводит в заблуждение.

### Инфраструктурные несоответствия

- `docker-compose.yml`: API запускается с `gunicorn --reload` и `seed_demo` **при каждом старте** — это dev-конфигурация. Прод-компоуза нет.
- `requirements.txt` — только диапазоны версий, нет lock-файла (pip-tools / uv) → невоспроизводимые сборки.
- **CI отсутствует** (нет `.github/workflows`) — тесты и сборка не гоняются автоматически.
- `SECRET_KEY` имеет insecure-дефолт, `DEBUG=true` по умолчанию; короткий ключ вызывает `InsecureKeyLengthWarning` в JWT (HMAC < 32 байт).
- Нет prod-настроек безопасности: `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`.
- Статика: `STATIC_ROOT` есть, но whitenoise/CDN не настроены.

---

## 3. Дыры в документации

### Хорошо синхронизировано (source of truth актуален)

`roadmap.md` + 7 implementation-доков, `product-requirements.md`, `api-contracts.md` (включая STAGE-007), `data-model.md`, `acceptance-criteria.md` (QA-AC-001…012 passed), все 7 feature-доков, `user-flow.md`, design-guide.

### Пустые шаблоны (заголовок не заполнен) — ~60 файлов

Критичные для прода:

| Документ | Почему критичен |
|---|---|
| `operations/deployment.md` | Процесс деплоя не описан вообще |
| `operations/rollback.md` | Roadmap ссылается на него в каждом стейдже — файл пуст |
| `operations/backup-and-restore.md` | Стратегии бэкапа Postgres нет |
| `operations/monitoring-and-alerts.md` | Мониторинга нет ни в коде, ни в доке |
| `security/security-checklist.md` | Roadmap ссылается на «Auth / Access» секцию — файл пуст |
| `security/threat-model.md`, `incident-response.md` | Для SaaS с записями разговоров — обязательны |
| `quality/testing-strategy.md`, `release-checklist.md` | Definition of Done ссылается в никуда |
| `legal/privacy-policy-notes.md`, `data-processing-agreement.md` | Записи разговоров = персональные данные, нужна проработка до прода |

Менее срочные: marketing/*, support/*, product/* — можно заполнять по мере выхода на рынок.

### Прочие несоответствия

- `data-model.md`: заявляет custom managers для tenant-фильтрации (см. C2).
- QA-AC-013/014 (управление правами через UI) — `draft`, функциональность не реализована (REQ-013/014).

---

## 4. План докрутки до прод-реализации

### P0 — блокеры прода (безопасность и живучесть)

1. **Token refresh flow** на фронте: interceptor на 401 → `/auth/refresh/` → повтор запроса; logout при невалидном refresh.
2. **Прод-конфиг Django**: `SECRET_KEY` обязателен (fail-fast без дефолта), `DEBUG=false` по умолчанию, HSTS/secure-cookies/SSL-redirect под флагом окружения, длинный ключ ≥ 32 байт.
3. ~~**Throttling**~~ — **сделано** (S3 в §1.1): login 10/min, агент 30/min, конфиг через env.
4. **CI (GitHub Actions)**: тесты API + `npm run build` + lint на каждый PR/push; проверка непримененных миграций.
5. **Lock-файл зависимостей** (pip-tools или uv) + Dependabot/Renovate.
6. **Прод-compose / деплой-конфиг**: gunicorn без `--reload`, без авто-seed, whitenoise для статики, отдельный `docker-compose.prod.yml`; заполнить `deployment.md` и `rollback.md`.
7. **Бэкапы Postgres** (pg_dump расписание или managed DB) + заполнить `backup-and-restore.md`.

### P1 — реальная функциональность вместо заглушек

8. **ASR-транскрипция**: адаптер (Whisper API / Deepgram / GigaAM) вместо demo-текста в `transcribe_recording_task`; S3-хранилище для аудио.
9. **LLM-адаптер**: единый сервис (OpenAI-совместимый, vendor-pluggable как в stack.md) для: агент-чата, структурирования кастомных отчётов, саммари аналитики. Rule-based оставить как fallback.
10. **Embeddings + pgvector** для RAG базы знаний (сейчас keyword-поиск): миграция на `VectorField`, индексация статей при сохранении.
11. **Реальные коннекторы интеграций** (CRM/телефония) или хотя бы API импорта записей/метрик — сейчас только `run_source_sync` с генерацией демо-метрик.
12. **REQ-013/014**: UI управления правами сотрудников с проверкой «потолка» руководителя (бэкенд-валидация уже частично есть в scope-сервисах).

### P2 — наблюдаемость, качество, документация

13. **Sentry** (API + web) + structured logging (JSON) + расширенный healthcheck (DB, Redis, Celery).
14. **E2E-тесты** (Playwright): login → дашборд → разбор → AI-отчёт; unit-тесты фронта для критичных lib-модулей.
15. **Заполнить security-доки**: threat-model (JWT в localStorage, XSS, мульти-тенант изоляция), security-checklist, incident-response.
16. **Legal**: privacy policy / DPA — записи разговоров сотрудников и клиентов требуют правового основания обработки.
17. **Синхронизировать stack.md и data-model.md** с фактическим состоянием (pgvector/S3/OpenAI → planned; tenant-фильтрация — на уровне views).
18. **httpOnly cookies для JWT** (или зафиксировать решение об localStorage в threat-model с компенсирующими мерами CSP).

### Рекомендуемый порядок

```
Спринт 1 (P0): пп. 1–5            → безопасный деплой возможен
Спринт 2 (P0/P1): пп. 6–9         → прод-инфра + реальный AI-контур
Спринт 3 (P1): пп. 10–12          → RAG, интеграции, права
Спринт 4 (P2): пп. 13–18          → наблюдаемость, E2E, доки, legal
```

---

## Резюме

Кодовая база целостная и дисциплинированная: тесты зелёные, tenant-изоляция и права применяются последовательно, документация по фичам синхронизирована — для MVP-стадии состояние хорошее. Главные разрывы до прода: (1) AI-контур работает на заглушках при том, что это ядро ценности продукта; (2) отсутствуют CI, прод-конфигурация и операционные доки (deploy/rollback/backup пустые); (3) дыры безопасности — нет refresh flow, throttling и прод-настроек Django. P0-список закрывается за один короткий спринт и не требует архитектурных изменений.
