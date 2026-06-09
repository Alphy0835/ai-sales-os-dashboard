# Code Review — AI Sales OS

Дата: 2026-06-10 · **P4c закрыт** (`88cdb32`)  
Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура  
Состояние: STAGE-001…007 + **P0–P4 + P4b-GS + P4c**; CI на `master`.

**Тесты:** **103** API (3 pgvector skipped) · **23** Vitest · **2** Playwright E2E · lint · **api-postgres**.

**План:** `plan_0.md` (локально) — P4b-GS ✅ · P4c ✅; далее P4b telephony / P5.

---

## CRM (P4b-GS + P4c)

| Компонент | Реализация |
|---|---|
| Источник | **Google Sheets** (`provider: google_sheets` в Admin) |
| Модель данных | **`CrmLead` = DB cache** (PostgreSQL); User Level и agent не читают live Sheets |
| `ClientToReview` | Только **explicit rules** (`needs_review` / `review_rules`) — не все open leads |
| Sync | **Hourly Beat** (`CRM_SYNC_INTERVAL_MINUTES`, default 60) + **on-demand** (agent refresh, manual POST sync) + login (**throttled**) |
| Не делаем | 24/7 realtime sync; batch LLM triage всех CRM comments |
| Manager agent | NL → structured filters → scoped `CrmLead` query; ответ с `as_of: last_sync_at` |
| Vocabulary | `crm_vocabulary` в `config_json` (дожатие, назначен → sheet values) |
| Настройка | **Django Admin only** (без отдельного Integration UI) |
| Регистрация | `RegistrationInvite` + `/register` + `POST /auth/register/` |
| amoCRM | Код сохранён, **не pilot path** |

### Колонки Google Sheet → Django

`lead_id`, `client_name`, `phone`, `city`, `communication_comment`, `manager_email`, `supervisor_email`, `pipeline_stage`, `status_stage`, `recording_url`, optional `needs_review` — шаблон в `docs/architecture/integrations.md`.

---

## Продуктовые defer

| # | Задача |
|---|---|
| P4b | Telephony webhook, reporting adapters |
| P5 | Sentry, staging, CSP, custom Integration UI (только при масштабе) |

---

## Pilot checklist

1. Django Admin: Tenant, Workspace, `RegistrationInvite` (код для первого manager)
2. `/register` — регистрация по коду
3. Google Sheet + service account в `IntegrationSource`
4. Share таблицы с service account email
5. Сотрудники в системе с email = `manager_email` в таблице
6. Login → sync (если не throttled) → «Клиенты к разбору» только по `review_rules`
7. Manager agent: CRM вопрос → ответ с `as_of`; при необходимости on-demand refresh

---

## Резюме

Pilot CRM = **Google Sheets DB cache + on-demand agent queries**, не batch LLM и не 24/7 sync. Admin: pre-filled `config_json` template при создании source.
