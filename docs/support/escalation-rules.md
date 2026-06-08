Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:
<!-- escalation-rules.md — это правила: когда проблема больше не решается обычной поддержкой и кого надо подключать выше. -->
# Escalation Rules

## Levels

### L1 — Support
Обычные вопросы, простые баги, помощь пользователю.

### L2 — Product / Engineering
Баги, которые требуют проверки логов, базы, API, платежей или кода.

### L3 — Critical / Incident
Потеря данных, падение production, security incident, массовая проблема, VIP/B2B impact.

## When To Escalate

| Trigger | Escalate To | Max Time | Related Docs |
|---|---|---|---|
| Payment charged but access not granted | engineering + product | immediately | billing docs, incident-response |
| User data missing | engineering + security | immediately | backup-and-restore, audit-logging |
| Suspected account takeover | security | immediately | incident-response |
| Same issue affects many users | engineering + operations | 15 min | monitoring-and-alerts |
| Enterprise client blocked | product owner + engineering | immediately | SLA / support contract |

## Required Context

Перед escalation нужно собрать:
- user/account ID
- что произошло
- когда произошло
- steps to reproduce
- screenshots/logs/error messages
- affected plan/client
- impact: один пользователь или много
- что уже пробовали

## Communication Rules

- Пользователю не обещать сроки, если их не подтвердил ответственный.
- Не писать про внутренние причины до проверки.
- Если есть риск данных/security, не обсуждать детали в открытых каналах.