# Code Review — AI Sales OS

Дата: 2026-06-10 · **P4b-GS закрыт**  
Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура  
Состояние: STAGE-001…007 + **P0–P4 + P4b-GS**; CI на `master`.

**Тесты:** **87** API (3 pgvector skipped) · **23** Vitest · **2** Playwright E2E · lint · **api-postgres**.

**План:** `plan_0.md` (локально) — P4b-GS ✅; далее P4b telephony / P5.

---

## CRM (P4b-GS)

| Компонент | Реализация |
|---|---|
| Источник | **Google Sheets** (`provider: google_sheets` в Admin) |
| Данные | `CrmLead` → очередь `ClientToReview` |
| Sync | Beat 01:00 + **при login** + manual API |
| Настройка | **Django Admin only** (без отдельного Integration UI) |
| Регистрация | `RegistrationInvite` + `/register` + `POST /auth/register/` |
| amoCRM | Код сохранён, **не pilot path** |

### Колонки Google Sheet → Django

`lead_id`, `client_name`, `phone`, `city`, `communication_comment`, `manager_email`, `supervisor_email`, `pipeline_stage`, `status_stage`, `recording_url` — шаблон в `docs/architecture/integrations.md`.

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
6. Login → sync → «Клиенты к разбору»

---

## Резюме

Pilot CRM = **Google Sheets**, не amoCRM. Отдельный Admin UI **не строим** — Admin + runbook достаточно.
