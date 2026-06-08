Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:

<!-- data-processing-agreement.md — требования к DPA для B2B/enterprise и обработки персональных данных от имени клиента. Файл фиксирует роли сторон, категории данных, цели обработки, subprocessors, меры безопасности, удаление/возврат данных и правила уведомления об инцидентах. -->

# Data Processing Agreement

## Purpose

<!-- Когда продукту нужен DPA и для каких клиентов/сценариев он применяется. -->

## Parties And Roles

| Party | Role | Notes |
|---|---|---|
| Product / Company | processor / controller |  |
| Customer | controller / processor |  |
| Subprocessor | subprocessor |  |

## Data Categories

| Category | Examples | Sensitivity | Related Docs |
|---|---|---|---|
|  |  | personal / confidential / critical | docs/security/data-classification.md |

## Processing Purposes

| Purpose | Data Categories | Product Feature | Related Docs |
|---|---|---|---|
|  |  | FEAT-... |  |

## Subprocessors

| Service | Purpose | Data Shared | Region | Notes |
|---|---|---|---|---|
|  | hosting / email / payments / analytics / AI / storage |  |  | docs/architecture/integrations.md |

## Security Measures

| Measure | Implemented | Related Docs |
|---|---|---|
| Access control | yes / no | docs/security/auth-and-access-control.md |
| Secrets management | yes / no | docs/security/secrets-management.md |
| Audit logging | yes / no | docs/security/audit-logging.md |
| Backup / restore | yes / no | docs/operations/backup-and-restore.md |
| Incident response | yes / no | docs/security/incident-response.md |

## Data Return / Deletion

| Scenario | Action | Timeframe | Related Docs |
|---|---|---|---|
| Contract ends | return / delete / anonymize |  | docs/security/data-retention.md |
| Customer requests deletion | delete / anonymize |  | docs/security/data-retention.md |
| Backup retention | retain temporarily / purge |  | docs/operations/backup-and-restore.md |

## Incident Notification

| Incident Type | Notify Customer | Target Time | Related Docs |
|---|---|---|---|
| Data breach | yes / no |  | docs/operations/incident-notification.md |
| Unauthorized access | yes / no |  | docs/security/incident-response.md |

## Open Questions

| Question | Owner | Status |
|---|---|---|
|  |  | open / resolved |

## Related Docs

- docs/security/privacy-and-compliance.md
- docs/security/data-classification.md
- docs/security/data-retention.md
- docs/security/audit-logging.md
- docs/security/access-review.md
- docs/operations/incident-notification.md
- docs/architecture/integrations.md
<!-- Файл может содержать в себе не все элементы описанные сейчас, а так же может иметь и дополнения и расширения в зафисимости от специфики проекта -->