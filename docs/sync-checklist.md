Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:
# Sync Checklist

<!--
sync-checklist.md — карта обязательной синхронизации между документации. Файл хранит только глобальные междоменные связи

Назначение:
Файл описывает, какие документы нужно проверять и обновлять вместе, если меняется один из связанных документов.

Правило использования:
1. Перед редактированием любого файла в docs нужно проверить его строку в этом чеклисте.
2. После редактирования файла нужно открыть связанные документы из колонки "Проверить вместе с".
3. Если связанный документ не требует изменений, это не нужно отдельно фиксировать.
4. Если изменение влияет на требования, фичи, API, данные, безопасность, качество или релиз, связанные документы должны быть обновлены в рамках той же задачи.
5. Если создается новый документ, его связи нужно добавить в этот чеклист и в паспорт самого документа.
6. Если документ становится source of truth для темы, все дублирующие описания в других файлах должны быть заменены краткой ссылкой на него.
-->

## Core Rule

Если документ изменяет смысл продукта, поведение фичи, структуру системы, данные, доступы, API, релиз или проверку качества, изменение не считается завершенным, пока не проверены связанные документы.

## Sync Map

| Если редактируется | Проверить вместе с | Что именно проверить |
|---|---|---|
| `project-idea.md` | `docs/project/product-requirements.md`, `docs/project/user-flow.md`, `docs/marketing/gtm-manifesto.md` | Не изменились ли идея продукта, целевая аудитория, ценность, основной flow и требования |
| `docs/project/product-requirements.md` | `docs/project/roadmap.md`, `docs/features/*`, `docs/quality/acceptance-criteria.md`, `docs/architecture/system-overview.md` | Не появились ли новые требования, ограничения, критерии приемки, архитектурные последствия |
| `docs/project/roadmap.md` | `docs/project/product-requirements.md`, `docs/features/*`, `docs/quality/release-checklist.md`, `docs/security/security-checklist.md`, `docs/quality/definition-of-done.md` | Не изменились ли этапы, статус, критерии готовности, security/QA/release-проверки |
| `docs/project/user-flow.md` | `docs/features/*`, `docs/project/design-guide/pages-map.md`, `docs/frontend/*`, `docs/quality/acceptance-criteria.md` | Не изменились ли сценарии, страницы, frontend-логика, критерии приемки |
| `docs/project/user-roles.md` | `docs/security/auth-and-access-control.md`, `docs/features/*`, `docs/security/audit-logging.md` | Не изменились ли роли, permissions, доступы, аудит действий |
| `docs/project/terminology.md` | Все документы, где используется термин | Не появились ли новые термины, конфликтующие названия или разные определения одного понятия |
| `docs/features/*` | `docs/project/product-requirements.md`, `docs/project/user-flow.md`, `docs/architecture/api-contracts.md`, `docs/architecture/data-model.md`, `docs/backend/*`, `docs/frontend/*`, `docs/security/*`, `docs/quality/*`, `docs/operations/*` | Не изменилась ли фича, требования, API, данные, UI, доступы, тесты, релиз или откат |
| `docs/architecture/system-overview.md` | `docs/backend/*`, `docs/frontend/*`, `docs/architecture/data-model.md`, `docs/architecture/integrations.md`, `docs/operations/*` | Не изменились ли модули, границы системы, связи, внешние сервисы, эксплуатационные последствия |
| `docs/architecture/data-model.md` | `docs/backend/*`, `docs/architecture/api-contracts.md`, `docs/security/data-classification.md`, `docs/operations/backup-and-restore.md` | Не изменились ли сущности, поля, связи, хранение, удаление, backup/restore |
| `docs/architecture/api-contracts.md` | `docs/backend/*`, `docs/frontend/*`, `docs/security/auth-and-access-control.md`, `docs/features/*` | Не изменились ли endpoints, request/response, ошибки, авторизация, webhooks |
| `docs/architecture/integrations.md` | `docs/security/secrets-management.md`, `docs/operations/environments.md`, `docs/operations/monitoring-and-alerts.md`, `docs/operations/rollback.md`, `docs/architecture/api-contracts.md` | Не изменились ли внешние сервисы, ключи, лимиты, webhooks, мониторинг, откат |
| `docs/backend/*` | `docs/architecture/api-contracts.md`, `docs/architecture/data-model.md`, `docs/security/auth-and-access-control.md`, `docs/architecture/integrations.md`, `docs/operations/*` | Не изменились ли backend-модули, API, данные, авторизация, интеграции, деплой |
| `docs/frontend/*` | `docs/project/design-guide/*`, `docs/project/design-guide/pages-map.md`, `docs/architecture/api-contracts.md`, `docs/project/user-flow.md`, `docs/features/*` | Не изменились ли UI, страницы, flow, API usage, состояние и ошибки |
| `docs/security/security-overview.md` | `docs/security/threat-model.md`, `docs/security/data-classification.md`, `docs/security/auth-and-access-control.md`, `docs/security/secrets-management.md`, `docs/security/audit-logging.md` | Не изменились ли главные security-принципы, риски, данные, доступы, секреты, аудит |
| `docs/security/threat-model.md` | `docs/features/*`, `docs/architecture/integrations.md`, `docs/security/auth-and-access-control.md`, `docs/security/data-classification.md`, `docs/security/security-checklist.md` | Не появились ли новые угрозы, риски, меры защиты, проверки перед релизом |
| `docs/security/auth-and-access-control.md` | `docs/project/user-roles.md`, `docs/backend/*`, `docs/frontend/*`, `docs/architecture/api-contracts.md`, `docs/security/audit-logging.md` | Не изменились ли роли, permissions, login/session/JWT/OAuth, audit events |
| `docs/security/data-classification.md` | `docs/architecture/data-model.md`, `docs/operations/backup-and-restore.md`, `docs/security/audit-logging.md`, `docs/security/security-checklist.md` | Не изменились ли типы данных, чувствительность, хранение, доступ, логирование |
| `docs/security/secrets-management.md` | `docs/architecture/integrations.md`, `docs/operations/environments.md`, `docs/operations/deployment.md` | Не изменились ли API keys, `.env`, токены, ротация, доступы, запреты |
| `docs/security/audit-logging.md` | `docs/security/auth-and-access-control.md`, `docs/project/user-roles.md`, `docs/security/incident-response.md`, `docs/operations/monitoring-and-alerts.md` | Не изменились ли события аудита, контекст логов, запрет на логирование секретов |
| `docs/security/security-checklist.md` | `docs/quality/release-checklist.md`, `docs/features/*`, `docs/security/auth-and-access-control.md`, `docs/security/secrets-management.md`, `docs/security/audit-logging.md` | Не изменились ли проверки безопасности перед релизом |
| `docs/security/incident-response.md` | `docs/operations/monitoring-and-alerts.md`, `docs/operations/rollback.md`, `docs/operations/backup-and-restore.md`, `docs/security/audit-logging.md` | Не изменились ли сценарии аварий, откат, восстановление, уведомления, аудит |
| `docs/quality/testing-strategy.md` | `docs/features/*`, `docs/quality/acceptance-criteria.md`, `docs/quality/release-checklist.md`, `docs/quality/definition-of-done.md` | Не изменились ли типы тестов, обязательные проверки, критерии готовности |
| `docs/quality/acceptance-criteria.md` | `docs/project/product-requirements.md`, `docs/features/*`, `docs/project/user-flow.md`, `docs/quality/definition-of-done.md` | Не изменились ли проверяемые условия приемки фич и этапов |
| `docs/quality/release-checklist.md` | `docs/project/roadmap.md`, `docs/security/security-checklist.md`, `docs/operations/deployment.md`, `docs/operations/rollback.md`, `docs/quality/definition-of-done.md` | Не изменились ли условия релиза, security gate, deploy, rollback, готовность |
| `docs/quality/definition-of-done.md` | `docs/features/*`, `docs/project/roadmap.md`, `docs/quality/acceptance-criteria.md`, `docs/quality/release-checklist.md` | Не изменилось ли определение завершенной работы |
| `docs/quality/bug-report-template.md` | `docs/quality/testing-strategy.md`, `docs/operations/monitoring-and-alerts.md`, `docs/security/incident-response.md` | Не изменился ли формат описания багов, алертов, инцидентов |
| `docs/operations/environments.md` | `docs/operations/deployment.md`, `docs/security/secrets-management.md`, `docs/backend/*`, `docs/architecture/integrations.md` | Не изменились ли окружения, env, домены, базы, доступы |
| `docs/operations/deployment.md` | `docs/operations/environments.md`, `docs/quality/release-checklist.md`, `docs/operations/rollback.md`, `docs/security/secrets-management.md` | Не изменился ли процесс сборки, выкладки, миграций, env, rollback |
| `docs/operations/monitoring-and-alerts.md` | `docs/security/incident-response.md`, `docs/security/audit-logging.md`, `docs/operations/rollback.md` | Не изменились ли алерты, критичные метрики, действия при сбоях |
| `docs/operations/backup-and-restore.md` | `docs/architecture/data-model.md`, `docs/security/data-classification.md`, `docs/security/incident-response.md` | Не изменились ли данные, частота бэкапов, доступы, восстановление |
| `docs/operations/rollback.md` | `docs/operations/deployment.md`, `docs/quality/release-checklist.md`, `docs/architecture/data-model.md`, `docs/architecture/integrations.md` | Не изменились ли правила отката кода, миграций, данных, интеграций |
| `docs/project/design-guide/design-system-format/*.md` | `docs/frontend/*`, `docs/project/design-guide/pages-map.md`, `docs/features/*` | Не изменились ли UI-правила, компоненты, страницы, frontend-реализация |
| `docs/project/design-guide/design-system-preview/*.html` | Соответствующий `.md` в design-system-preview или design-system-format | Проверить, что HTML остается только визуализацией, а `.md` остается source of truth |
| `docs/README.md` | `docs/work-rules-docs.md`, `docs/maturity-levels.md`, `docs/sync-checklist.md` | Не изменилась ли общая структура docs, правила работы с файлами, уровни зрелости и карта синхронизации |
| `docs/work-rules-docs.md` | `docs/README.md`, `docs/maturity-levels.md`, `docs/sync-checklist.md`, все `work-rules-*.md` | Не изменились ли общие правила ведения документации, паспорт документа, принципы ссылок и синхронизации |
| `docs/maturity-levels.md` | `docs/README.md`, `docs/work-rules-docs.md`, `docs/sync-checklist.md`, все `work-rules-*.md` | Не изменились ли правила включения документов на разных стадиях проекта |
| `docs/*/work-rules-*.md` | `docs/README.md`, `docs/work-rules-docs.md`, `docs/sync-checklist.md`, файлы внутри соответствующей папки | Не изменилась ли структура раздела, назначение файлов и правила их заполнения |
| `docs/project/work-rules-project.md` | `docs/project/product-requirements.md`, `docs/project/roadmap.md`, `docs/project/user-flow.md`, `docs/project/user-roles.md`, `docs/project/terminology.md` | Не изменились ли правила описания проектной части продукта |
| `docs/legal/legal-readiness.md` | `docs/legal/privacy-policy-notes.md`, `docs/legal/terms-notes.md`, `docs/legal/data-processing-agreement.md`, `docs/product/pricing-and-packaging.md`, `docs/security/privacy-and-compliance.md`, `docs/security/data-retention.md` | Не изменились ли юридические требования, privacy/terms/DPA, pricing/refund rules, обработка и удаление данных |
| `docs/legal/privacy-policy-notes.md` | `docs/security/data-classification.md`, `docs/security/data-retention.md`, `docs/security/privacy-and-compliance.md`, `docs/architecture/integrations.md` | Не изменились ли персональные данные, цели обработки, сроки хранения, внешние сервисы и права пользователя |
| `docs/legal/terms-notes.md` | `docs/product/pricing-and-packaging.md`, `docs/security/abuse-and-fraud.md`, `docs/security/auth-and-access-control.md`, `docs/support/support-runbook.md` | Не изменились ли правила использования, платежи, refunds, блокировки аккаунтов, abuse и поддержка пользователей |
| `docs/legal/data-processing-agreement.md` | `docs/security/data-classification.md`, `docs/security/access-review.md`, `docs/security/audit-logging.md`, `docs/operations/incident-notification.md`, `docs/architecture/integrations.md` | Не изменились ли категории данных, subprocessors, меры безопасности, аудит, доступы и уведомления об инцидентах |
| `docs/marketing/acquisition-channels.md` | `docs/marketing/gtm-manifesto.md`, `docs/marketing/icp-profile.md`, `docs/marketing/positioning.md`, `docs/product/metrics-and-analytics.md` | Не изменились ли каналы привлечения, целевая аудитория, позиционирование, conversion/activation метрики |