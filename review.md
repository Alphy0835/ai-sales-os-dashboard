# Code Review — AI Sales OS

Дата: 2026-06-10 · **P3 закрыт**  
Объём: backend (Django 5 + DRF), frontend (Next.js 15), docs, инфраструктура  
Состояние: STAGE-001…007 + **P0/P1/P2/P3 закрыты**; CI на `master`.

**Тесты:** **67** API · **21** Vitest · **2** Playwright E2E · lint в CI.

**План:** `plan_0.md` (локально) — P3 ✅; далее P4/P5.

---

## 1. Целостность проекта

### Что хорошо

- Монорепо консистентно: `apps/api` (6 Django-приложений), `apps/web`, `docs/`, лаунчеры.
- **67** API + **21** Vitest + **2** E2E + lint в CI.
- Multi-tenant + manager scope + ceiling rule; `clients: view` OR `dashboard: view` на `/manager/clients/`.
- httpOnly JWT через BFF + refresh blacklist; permission-aware nav + forbidden UX.
- Custom reports scoped по workspace автора; audit API с фильтром `action`.

### Закрытые проблемы (P3)

| # | Было | Статус |
|---|---|---|
| C2 | Custom managers claim | ✅ data-model: view-level isolation |
| C6 | `clients` permission unused | ✅ enforced в analytics/views |
| C7 | Nav без permission filter | ✅ AppShell скрывает `none` |
| C8 | 403 → logout | ✅ forbidden UI в ProtectedShell |
| R1–R5 | Test gaps | ✅ IDOR, cookies, throttle, LLM fallback, upload |

### Остаётся (продукт / P4+)

| # | Риск | Статус |
|---|---|---|
| R6 | Demo transcripts/metrics в prod | Осознан defer → P4 ASR |
| — | Z-FILTERS, Z-TREND UI zones | Низкий приоритет |

### Security-аудит (2026-06-09) — исправлено

S1–S6 закрыты; регрессия в `ai/tests/test_security_scope.py` + cross-tenant IDOR suite.

---

## 2. Backend vs документация

**Синхронизировано (P3-D1/D2):** auth cookies, api-contracts index, data-model entities, backend-docs Celery tasks, roadmap STAGE-007 done, audit `action` filter, clients permission.

---

## 3. Frontend vs документация

**Синхронизировано (P3-D3):** permission nav, forbidden UX, cross-links (dashboard→reviews, clients→agent), error+retry, Access tab gating, `middleware.ts`, demo login env-gated.

**Средние defer:** Z-FILTERS (clients), Z-TREND (employee).

---

## 4. Тестирование

| Слой | Count | CI | Статус |
|---|---|---|---|
| API | 67 | ✅ | cookies, IDOR, throttle, upload, LLM fallback |
| Vitest | 21 | ✅ | auth, api, dashboard, reviews |
| Playwright | 2 | ✅ | manager critical + employee flow/logout |
| Lint | — | ✅ | `.eslintrc.json` + CI web job |

**Docs:** `test-matrix.md` ✅ · `release-checklist.md` ✅ · `security-checklist.md` synced.

---

## 5. Документация — статус

### Заполнено (P0–P3)

Ops, security, legal, auth, api-contracts, data-model, test-matrix, release-checklist, deployment (BFF), feature docs Access/custom reports.

### Skeleton (~45 файлов)

marketing/*, support/*, `environments.md`, `definition-of-done.md` — P5.

---

## 6. Roadmap — статус

### P0–P2 ✅ (2026-06-09)

Deploy hardening · LLM/pgvector/Access · JSON logs · E2E · security docs · BFF cookies.

### P3 ✅ (2026-06-10)

| Фаза | Содержание |
|---|---|
| D0 | Prod compose, Beat, baked Next, TLS proxy, ops docs |
| D1 | Doc sync (auth, threat-model, api-contracts, test-matrix, release-checklist) |
| D2 | clients permission, audit filter, custom reports scope, data-model C2 |
| D3 | Permission nav, forbidden UX, cross-links, error/retry, middleware, login hygiene |
| D4 | +16 tests, lint CI, core.tests в local runner |

### P4 — следующий этап

ASR · real integrations · agent retention · PostgreSQL CI matrix.

---

## 7. Готовность к продакшену

**Вердикт:** **pilot/staging готов** после smoke на HTTPS (ручной). Unattended B2B SaaS — после P4.

### Готово

Prod compose · Beat retention · BFF cookies · permission UX · 67 API tests · reverse proxy docs · backups.

### Перед pilot (ручное)

Smoke: login → dashboard → analytics на staging URL с TLS.

### Продуктовые defer

Demo ASR · demo integrations · Sentry (P5).

---

## 8. Рекомендуемый порядок

```
✅ P0–P3: закрыт
→ P4: ASR + real integrations
→ P5: Sentry, staging env, CSP, marketing docs
```

---

## Резюме

User Level MVP + **P0–P3 полностью закрыты**. Код, docs и тесты синхронизированы. Следующий фокус — **P4** (реальный ASR и интеграции).
