Doc ID: OPS-INTEGRATOR-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/deployment.md, docs/operations/environments.md, docs/operations/backup-and-restore.md, docs/architecture/integrations.md, docs/security/secrets-management.md, docs/legal/data-processing-agreement.md
Update together with: deployment.md, integrations.md, docker-compose.prod.yml, .env.example
Update trigger: pilot onboarding step change, Admin model change, CRM sync behavior change
Review required: operations, backend
Maturity: L2

# Runbook integrator — VPS и первый pilot-tenant

Пошаговая инструкция для integrator'а: поднять production stack на VPS, создать tenant, подключить Google Sheets CRM, включить LLM/RAG и провести первого пользователя через регистрацию.

**Аудитория:** integrator с доступом к VPS, Django Admin и Google Cloud (service account для Sheets).

**Связанные документы:** общий деплой — [deployment.md](deployment.md); архитектура CRM — [integrations.md](../architecture/integrations.md).

---

## 0. Чеклист перед стартом

- [ ] VPS с Docker Engine + Compose v2
- [ ] Домен и TLS (nginx/Caddy → `127.0.0.1:3000`)
- [ ] Репозиторий склонирован на хост
- [ ] DPA/согласие с tenant на передачу данных в OpenRouter (транскрипты, KB, промпты агента)
- [ ] Google Cloud project + service account с доступом к Sheets API (read-only)

---

## 1. Подготовка VPS

1. **Обновить ОС и установить Docker** (если ещё не установлен):

```bash
sudo apt update && sudo apt upgrade -y
# Docker Engine + Compose plugin — см. https://docs.docker.com/engine/install/
```

2. **Firewall** — только SSH, 80, 443 (см. [deployment.md — Firewall](deployment.md#firewall)):

```bash
sudo ufw default deny incoming
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

3. **Клонировать репозиторий** и перейти в корень:

```bash
git clone <repo-url> ai-sales-os
cd ai-sales-os
```

4. **Reverse proxy** — настроить nginx или Caddy по [deployment.md — Reverse proxy](deployment.md#reverse-proxy). Браузер ходит только на `https://app.example.com`; API и Admin проксируются через Next.js BFF.

5. **DNS** — A-запись домена на IP VPS до выпуска TLS.

---

## 2. Production `.env` — чеклист переменных

Скопировать [`.env.example`](../../.env.example) в `.env` в корне репозитория. **Не коммитить.**

| Переменная | Обязательно | Значение для pilot |
|---|---|---|
| `POSTGRES_PASSWORD` | **да** | Сильный пароль (≥ 20 символов) |
| `POSTGRES_DB`, `POSTGRES_USER` | да | По умолчанию `ai_sales_os` |
| `DJANGO_SECRET_KEY` | **да** | ≥ 32 случайных байт (hex/base64) |
| `DJANGO_ENV` | **да** | `production` |
| `DJANGO_DEBUG` | **да** | `false` |
| `DJANGO_ALLOWED_HOSTS` | **да** | `api,localhost,127.0.0.1,app.example.com` |
| `CORS_ALLOWED_ORIGINS` | **да** | `https://app.example.com` |
| `NEXT_PUBLIC_API_URL` | **да** | **пусто** (`""`) — same-origin cookies через BFF |
| `AI_CREDENTIALS_KEY` | **да** | Fernet-ключ для шифрования credentials в Admin |
| `FRONTEND_URL` | **да** (VPS) | Публичный origin, напр. `https://app.example.com` — для ссылок регистрации в Admin |
| `OPENROUTER_API_KEY` | рекомендуется | Ключ OpenRouter (LLM, embeddings, STT); fallback, если в Admin нет tenant API key |
| `LLM_BASE_URL`, `LLM_CHAT_MODEL`, `LLM_EMBEDDING_MODEL` | опционально | Env fallback; per-tenant tier/presets — в Admin → **Tenant AI configs** (§7.4) |
| `CRM_SYNC_INTERVAL_MINUTES` | опционально | По умолчанию `60` |
| `THROTTLE_LOGIN`, `THROTTLE_AGENT` | опционально | По умолчанию `10/min`, `30/min` |
| `TRANSCRIPT_RETENTION_DAYS` | опционально | По умолчанию `90` |

`DATABASE_URL`, `REDIS_URL`, `API_BACKEND_URL` — compose переопределяет для Docker-сети; в `.env` можно оставить значения из example.

**Не запускать** `seed_demo` в production (кроме одноразового staging sandbox).

---

## 3. Запуск production stack

Из корня репозитория:

```bash
# Бэкап перед первым деплоем (пустая БД — опционально)
./scripts/backup-postgres.sh

# Сборка и старт
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Сервисы: `postgres`, `redis`, `api`, `worker`, `beat`, `web`. Подробности — [deployment.md — Services](deployment.md#services-production-compose).

Проверить статус:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs api worker beat --tail 30
```

---

## 4. Health check

**Внутри контейнера API:**

```bash
docker compose -f docker-compose.prod.yml exec api python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ready/')"
```

**Через BFF + TLS (с хоста или ноутбука integrator'а):**

```bash
curl -sf https://app.example.com/api/v1/health/ready/
```

Ожидается HTTP 200. Readiness проверяет Postgres, Redis и доступность Celery worker.

---

## 5. Создать superuser (integrator)

```bash
docker compose -f docker-compose.prod.yml exec -it api python manage.py createsuperuser
```

Укажите email и пароль integrator'а. Для доступа в Admin пользователь должен иметь `is_staff=True` (createsuperuser выставляет автоматически).

---

## 6. Доступ в Django Admin через BFF

Next.js проксирует `/admin/` на Django (`apps/web/next.config.ts`). Integrator открывает:

```
https://app.example.com/admin/
```

Войти под superuser. **Не** открывать `:8000` снаружи — в prod compose API не проброшен на хост.

Если Admin не открывается: проверить `DJANGO_ALLOWED_HOSTS`, TLS + `X-Forwarded-Proto`, логи `web` и `api`.

---

## 7. Tenant, Workspace, RegistrationInvite

### 7.1 Tenant

Admin → **Accounts → Tenants → Add**

| Поле | Пример |
|---|---|
| Name | ООО «Пилот» |
| Slug | `pilot-co` |
| Is active | ✓ |

### 7.2 Workspace (hub)

Admin → **Accounts → Workspaces → Add**

| Поле | Пример |
|---|---|
| Name | ОП Москва |
| Tenant | pilot-co |
| Is active | ✓ |

Workspace — точка привязки для pilot: **RegistrationInvite**, **IntegrationSource** (CRM) и опционально **Workspace AI configs** (§7.4) задаются на этот workspace.

### 7.3 RegistrationInvite

Admin → **Accounts → Registration invites → Add**

| Поле | Значение |
|---|---|
| Code | Оставить пустым — сгенерируется при сохранении; или action «Generate random invite codes» |
| Expected email | Email будущего пользователя (= `manager_email` в sheet); если пусто — любой email |
| Tenant | pilot-co |
| Workspace | ОП Москва |
| Role | `manager` или `employee` |
| Expires at | +30 дней |
| Max uses | `1` (или больше для batch onboarding) |

После сохранения: readonly **Ссылка для регистрации** (`registration_url`) — `https://app.example.com/register?code=…` (зависит от `FRONTEND_URL`).

При регистрации автоматически выставляются **default permissions** по роли (manager: dashboard/clients/reviews/analytics/settings/agent; employee: dashboard + agent). Manager получает **Manager scope** на workspace из invite.

**Важно:** для привязки `CrmLead.employee` email при регистрации должен совпадать с `manager_email` в Google Sheet (используйте **Expected email**, если invite персональный).

### 7.4 Tenant / Workspace AI config

Admin → **AI → Tenant AI configs → Add** (один на tenant)

| Поле | Значение |
|---|---|
| Tenant | pilot-co |
| Is enabled | ✓ |
| Model tier | Пусто → модели из env (`LLM_*`); иначе `free` / `standard` / `premium` — preset chat/embedding |
| API key | Опционально; per-tenant OpenRouter key (шифруется). Пусто → `OPENROUTER_API_KEY` из env |
| Base URL | Опционально; override OpenRouter base |

Presets tier (см. `ai/services/model_tiers.py`): **free** → Llama 3.3 70B free; **standard** → gpt-4o-mini + text-embedding-3-small; **premium** → gpt-4o + text-embedding-3-small.

Опционально Admin → **AI → Workspace AI configs** — override tier/key для одного workspace (пустой tier → наследует tenant).

Раскрываемый блок **Advanced model override** — явные `chat_model` / `embedding_model` поверх tier preset.

---

## 8. IntegrationSource — Google Sheets

### 8.1 Подготовить Google Sheet

1. Создать таблицу по шаблону — [integrations.md — Google Sheet template](../architecture/integrations.md#google-sheet-template).
2. Заполнить строки с реальными `manager_email` (будущие пользователи).
3. Создать service account в Google Cloud, скачать JSON-ключ.
4. **Share sheet** с email service account (`client_email` из JSON) — роль **Viewer**.

### 8.2 Создать IntegrationSource в Admin

Admin → **Integrations → Integration sources → Add**

**Основные поля**

| Поле | Значение |
|---|---|
| Name | CRM Google Sheets |
| Source type | `crm` |
| Tenant | pilot-co |
| Workspace | ОП Москва |
| Is enabled | ✓ |
| Credentials JSON | Полный JSON service account (шифруется при сохранении) |

**CRM configuration** (структурированная форма; `config_json` собирается при сохранении)

| Поле | Значение |
|---|---|
| CRM-провайдер | `google_sheets` |
| ID Google Таблицы | ID из URL spreadsheet |
| Имя листа | `Leads` (или имя вкладки) |
| Заголовки колонок | По одному полю на внутреннее имя (`lead_id`, `client_name`, …) — введите **точный текст заголовка** из row 1 sheet (рус/англ) |

**Advanced JSON** (свёрнутый блок) — только `review_rules` и `crm_vocabulary`. `skip_status_stages` сохраняется из шаблона/существующей записи.

Полный пример `config_json` и шаблон — [integrations.md](../architecture/integrations.md).

Admin action **Sync CRM now** на списке sources — принудительный sync без shell (Google Sheets CRM only).

### 8.3 Первый sync

После сохранения source:

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py shell -c \
  "from integrations.tasks import sync_integration_source; sync_integration_source.delay('<SOURCE_UUID>', force=True)"
```

Или дождаться hourly Beat / выполнить sync после первого login менеджера.

Проверить в Admin: **Integrations → Integration sources** — `status=connected`, `last_sync_at` обновился; **Crm leads** — строки из sheet.

---

## 9. OPENROUTER_API_KEY и reindex_knowledge

1. Задать ключ: **env** `OPENROUTER_API_KEY` и/или per-tenant **API key** в Admin → Tenant AI configs (§7.4). Workspace key override — в Workspace AI configs.

2. Пересоздать `api` и `worker` (env-ключ читается при старте; Admin keys — из БД):

```bash
docker compose -f docker-compose.prod.yml up -d api worker
```

3. Переиндексировать базу знаний (embeddings для semantic RAG):

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py reindex_knowledge
```

Команда ставит в очередь Celery `embed_knowledge_article` для всех активных `KnowledgeArticle`. Убедиться, что `worker` запущен:

```bash
docker compose -f docker-compose.prod.yml logs worker --tail 20
```

Без `OPENROUTER_API_KEY`: UI работает, но semantic RAG и LLM-ответы агента — keyword/demo fallback.

---

## 10. Регистрация первого пользователя

1. Передать пользователю invite code и URL `https://app.example.com/register`.
2. Пользователь регистрируется с **email = `manager_email`** из sheet.
3. После регистрации — автоматический login → home по роли.

---

## 11. Проверка CRM sync и agent

### CRM sync

1. Login пользователя → фоновый CRM sync (throttled, интервал `CRM_SYNC_INTERVAL_MINUTES`).
2. UI: **Клиенты к разбору** — строки, попавшие под `review_rules`.
3. Admin: `IntegrationSource.last_sync_at`, `CrmLead` rows с `employee` = зарегистрированный user.

Принудительный sync (manager с правом `settings: edit`):

```bash
curl -X POST -b cookies.txt \
  https://app.example.com/api/v1/integrations/sources/<id>/sync/
```

### Manager agent

1. Открыть **AI-агент руководителя**.
2. Запрос: «Сколько клиентов на этапе дожатие?» (или другой фильтр по данным sheet).
3. Ожидание: ответ с числом/выборкой и **`Данные на …`** (`as_of` = `last_sync_at`).

При устаревших данных agent может вызвать on-demand `refresh_crm` (P4c).

---

## 12. Before go-live — DPA & OpenRouter

**Обязательно до первых реальных пользователей и до загрузки PII в LLM/RAG/STT.**

OpenRouter получает данные tenant'а при включённом `OPENROUTER_API_KEY`: транскрипты звонков, статьи базы знаний, промпты и ответы AI-агента, аналитические отчёты. Это **передача персональных и деловых данных третьей стороне** (OpenRouter и выбранные model providers).

| Шаг | Действие |
|---|---|
| 1 | Подписать [DPA](../legal/data-processing-agreement.md) с tenant (или включить пункт в договор) |
| 2 | Получить **письменное согласие** tenant на передачу соответствующих категорий данных в OpenRouter |
| 3 | Зафиксировать в onboarding: какие данные уходят в LLM (KB, транскрипты, CRM-контекст в agent) |
| 4 | Без DPA/согласия — **не** задавать `OPENROUTER_API_KEY`; UI работает на keyword/demo fallback |

Опционально: `SENTRY_DSN` в `.env` для error reporting API (без PII, `send_default_pii=false`). См. `.env.example`.

---

## 13. Pilot gate (кратко)

- [ ] Health ready 200 через BFF
- [ ] Admin доступен по `https://app.example.com/admin/`
- [ ] Tenant + Workspace + Invite + IntegrationSource connected; Tenant AI config (tier/key) при необходимости
- [ ] Sheet shared с service account
- [ ] Пользователь зарегистрирован, CRM sync OK
- [ ] Agent отвечает с `as_of`
- [ ] Backup cron настроен — [backup-and-restore.md](backup-and-restore.md)
- [ ] DPA подписан и согласие tenant на OpenRouter — см. §12

---

## Troubleshooting

### Ошибки CRM sync (`status=error`, `last_error`)

| Симптом | Причина | Действие |
|---|---|---|
| `403` / `permission` | Sheet не расшарен на SA | Share → `client_email` из JSON, Viewer |
| `404` spreadsheet | Неверный `spreadsheet_id` | Проверить ID в URL таблицы |
| `Invalid credentials` | Битый JSON в credentials | Пересохранить service account JSON в Admin |
| Пустой `CrmLead` | Неверный `sheet_name` / `header_map` | Сверить заголовки row 1 с `header_map` |
| `ClientToReview` пуст | Строки не попали в `review_rules` | Включить `needs_review=TRUE` или `auto_review_statuses` |

Логи:

```bash
docker compose -f docker-compose.prod.yml logs worker --tail 100 | grep -i sync
```

Ручной sync для диагностики — см. §8.3.

### Throttled login (sync не срабатывает сразу после login)

Login-triggered sync **пропускается**, если `IntegrationSource.last_sync_at` свежее `CRM_SYNC_INTERVAL_MINUTES` (по умолчанию 60 мин). Это ожидаемое поведение (P4c).

**Обход:** manual sync через API или Admin shell; agent tool `refresh_crm`; подождать следующий Beat tick.

**429 Too Many Requests** на login/agent — rate limit (`THROTTLE_LOGIN` / `THROTTLE_AGENT`). Подождать 1 мин или снизить частоту попыток.

### Пустой dashboard KPI (Sheets-only — ожидаемо)

Hero-метрики дашборда (`calls`, `quality_score`, `deals`, `revenue`) берутся из **telephony/reporting** `MetricSnapshot` или demo seeds. **Google Sheets P4c** поставляет `CrmLead` и «Клиенты к разбору», но **не** заполняет telephony KPI.

| Что видит pilot | Источник |
|---|---|
| Клиенты к разбору | Google Sheets → `ClientToReview` ✓ |
| Hero KPI (звонки, качество) | **empty / partial** без telephony demo |
| Agent CRM queries | `CrmLead` cache ✓ |

Не трактовать пустые KPI как ошибку sync — см. [review.md](../../review.md) Demo vs Real.

### Admin / static не грузится

- Проверить rewrite `/admin/` и `/static/` в Next (`next.config.ts`)
- Пересобрать `web` после смены BFF env: `docker compose -f docker-compose.prod.yml build web && … up -d web`
- `collectstatic` выполняется при старте `api` — см. [deployment.md](deployment.md)

### LLM / RAG не работает

- `OPENROUTER_API_KEY` задан и контейнеры перезапущены
- `AI_CREDENTIALS_KEY` задан (обязателен в production)
- После загрузки KB статей — `reindex_knowledge` + running worker
- Проверить Celery: `docker compose -f docker-compose.prod.yml logs worker --tail 50`

---

## Related

- [deployment.md](deployment.md) — reverse proxy, compose, health
- [backup-and-restore.md](backup-and-restore.md) — scheduled backups
- [integrations.md](../architecture/integrations.md) — sheet template, sync strategy P4b-GS + P4c
- [data-processing-agreement.md](../legal/data-processing-agreement.md) — OpenRouter / PII
- [release-checklist.md](../quality/release-checklist.md) — go/no-go перед pilot
