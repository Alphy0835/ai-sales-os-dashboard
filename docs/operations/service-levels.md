Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:
<!-- service-levels.md — какой уровень надежности продукт обязан держать. Он отвечает на вопросы: сколько можно лежать, сколько данных можно потерять, как быстро реагируем, какие метрики считаем здоровьем продукта. -->
# Service Levels

## Purpose

Файл фиксирует целевые уровни надежности продукта: availability, performance, recovery, incident response и допустимую потерю данных.

## Scope

| Service / Area | Included | Notes |
|---|---|---|
| Web app | yes / no | Пользовательский интерфейс |
| API | yes / no | Публичное или внутреннее API |
| Auth | yes / no | Логин, регистрация, сессии |
| Payments | yes / no | Оплата, подписки, webhooks |
| Database | yes / no | Основное хранилище данных |
| Background jobs | yes / no | Очереди, cron, async tasks |
| External integrations | yes / no | Email, AI API, CRM, storage |

## Availability Targets

| Area | Target | Measurement Window | Release Gate |
|---|---|---|---|
| Web app | 99.5% / 99.9% | monthly | beta / production |
| API | 99.5% / 99.9% | monthly | production |
| Auth | 99.9% | monthly | production |
| Payments | 99.9% | monthly | production |

## Performance Targets

| Area | Target | Notes |
|---|---|---|
| Page load | p95 < 2s | Для ключевых страниц |
| API latency | p95 < 500ms | Без учета внешних API |
| Error rate | < 1% | 5xx / failed requests |
| Background job delay | < 5 min | Для критичных задач |

## Recovery Targets

| Scenario | RTO | RPO | Notes |
|---|---|---|---|
| App deploy broke production | 30 min | 0 data loss | Rollback через deployment/rollback docs |
| Database failure | 2 h | 15 min | Зависит от backup/restore |
| External payment provider issue | 4 h | 0 payment records loss | Нужна сверка платежей |
| Full infrastructure outage | 24 h | 1 h | Только для зрелого production |

## Incident Response Targets

| Severity | Example | First Response | Workaround / Fix Target |
|---|---|---|---|
| SEV-1 Critical | Production down, data loss, payment outage | 15 min | ASAP |
| SEV-2 Major | Ключевая фича не работает у многих | 1 h | same day |
| SEV-3 Minor | Баг без блокировки основного flow | 1 business day | planned |
| SEV-4 Low | Cosmetic / rare edge case | 3 business days | backlog |

## Exclusions

Что не считается нарушением service level:
- плановое обслуживание;
- сбой внешнего сервиса вне нашего контроля;
- проблема на стороне пользователя;
- экспериментальные beta-фичи;
- force majeure.

## Measurement Rules

| Metric | Source | Owner | Review Cadence |
|---|---|---|---|
| Uptime | monitoring tool | operations | weekly / monthly |
| API latency | logs / APM | backend | weekly |
| Error rate | monitoring / logs | engineering | weekly |
| Backup restore check | backup-and-restore.md | operations | monthly / quarterly |

## Related Docs

- monitoring-and-alerts.md
- incident-levels.md
- incident-response.md
- rollback.md
- backup-and-restore.md
- deployment.md
<!-- Файл может содержать в себе не все элементы описанные сейчас, а так же может иметь и дополнения и расширения в зафисимости от специфики проекта -->