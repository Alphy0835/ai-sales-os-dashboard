# Code Review — AI Sales OS

Дата: 2026-06-10 · **P4 закрыт**  
Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура  
Состояние: STAGE-001…007 + **P0–P4 закрыты**; CI на `master`.

**Тесты:** **78** API (3 pgvector skipped on SQLite) · **21** Vitest · **2** Playwright E2E · lint · **api-postgres** CI job.

**План:** `plan_0.md` (локально) — P4 ✅; далее P5.

---

## 1. Целостность проекта

### Что хорошо

- OpenRouter STT (`stt_adapter`) + transient audio; demo fallback без ключа.
- amoCRM read-only sync → `MetricSnapshot`; demo fallback без credentials.
- Agent chat retention 90d (`purge_expired_agent_chats` + Beat 04:00 UTC).
- PostgreSQL/pgvector CI job + vector search tests.
- **78** API + **21** Vitest + **2** E2E + lint в CI.

### Продуктовые defer (P4b / P5)

| # | Задача | Статус |
|---|---|---|
| — | Telephony webhook + real telephony metrics | P4b |
| — | Reporting adapter | P4b |
| — | Sentry, staging, CSP | P5 |

---

## 6. Roadmap — статус

### P4 ✅ (2026-06-10)

| # | Содержание |
|---|---|
| P4-1 | OpenRouter STT, upload fix, transient audio |
| P4-2 | amoCRM connector, credentials, Beat sync, manual sync API |
| P4-3 | Agent chat 90d purge + legal docs |
| P4-4 | api-postgres CI + pgvector tests |

---

## 7. Готовность к продакшену

**Вердикт:** **pilot-ready** (real CRM metrics + real STT + retention). Staging smoke — ручной шаг.

### Перед pilot (ручное)

- Smoke: login → dashboard → analytics на staging HTTPS
- Настроить amoCRM token + subdomain в Django Admin
- `OPENROUTER_API_KEY` для STT

---

## 8. Рекомендуемый порядок

```
✅ P0–P4: закрыт
→ P4b: telephony webhook + reporting adapters
→ P5: Sentry, staging env, CSP, marketing docs
```

---

## Резюме

User Level MVP + **P0–P4 полностью закрыты**. Продукт готов к pilot с amoCRM + OpenRouter STT. Следующий фокус — **P5** или **P4b** (telephony/reporting).
