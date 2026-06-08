Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:
<!-- maturity-levels.md — описание стадиц разработки и что конкретно необходимо на каждом этапе -->
# Maturity Levels

## MVP Required
<!--Минимум, без которого нельзя начинать разработку. -->

## Beta Required
<!--Документы, нужные перед первыми пользователями. -->

## Production Required
<!--Документы, нужные перед стабильным публичным использованием. -->

## Enterprise / Regulated Required
<!--Документы для B2B, персональных данных, compliance, высокой ответственности. -->

| File | MVP | Beta | Production | Enterprise / Regulated |
|---|---:|---:|---:|---:|
| `project-idea.md` | required | required | required | required |
| `docs/project/product-requirements.md` | required | required | required | required |
| `docs/project/roadmap.md` | required | required | required | required |
| `docs/project/user-flow.md` | required | required | required | required |
| `docs/project/user-roles.md` | optional | required | required | required |
| `docs/project/terminology.md` | optional | required | required | required |
| `docs/product/assumptions-and-validation.md` | required | required | required | required |
| `docs/product/metrics-and-analytics.md` | optional | required | required | required |
| `docs/product/pricing-and-packaging.md` | optional | optional | required | required |
| `docs/product/launch-readiness.md` | optional | required | required | required |
| `docs/product/feedback-and-insights.md` | optional | required | required | required |
| `docs/marketing/gtm-manifesto.md` | optional | required | required | required |
| `docs/marketing/icp-profile.md` | optional | required | required | required |
| `docs/marketing/competitive-landscape.md` | optional | required | required | required |
| `docs/marketing/positioning.md` | optional | required | required | required |
| `docs/marketing/acquisition-channels.md` | optional | required | required | required |
| `docs/features/feature-template.md` | required | required | required | required |
| `docs/architecture/system-overview.md` | required | required | required | required |
| `docs/architecture/data-model.md` | required | required | required | required |
| `docs/architecture/api-contracts.md` | required | required | required | required |
| `docs/architecture/integrations.md` | optional | required if integrations | required | required |
| `docs/architecture/architecture-decisions/*` | optional | required for major decisions | required | required |
| `docs/frontend/*` | optional | required if frontend | required if frontend | required if frontend |
| `docs/backend/*` | optional | required if backend | required if backend | required if backend |
| `docs/project/design-guide/pages-map.md` | optional | required if frontend | required if frontend | required if frontend |
| `docs/project/design-guide/design-system-format/*` | optional | optional | required if UI-heavy | required if UI-heavy |
| `docs/quality/acceptance-criteria.md` | required | required | required | required |
| `docs/quality/definition-of-done.md` | required | required | required | required |
| `docs/quality/testing-strategy.md` | optional | required | required | required |
| `docs/quality/release-checklist.md` | optional | required | required | required |
| `docs/quality/test-matrix.md` | optional | optional | required if many features | required |
| `docs/quality/severity-matrix.md` | optional | optional | required | required |
| `docs/quality/performance-requirements.md` | optional | optional | required if load matters | required |
| `docs/quality/accessibility-checklist.md` | optional | required if public frontend | required if public frontend | required |
| `docs/security/security-overview.md` | optional | required | required | required |
| `docs/security/security-checklist.md` | optional | required | required | required |
| `docs/security/auth-and-access-control.md` | required if auth | required if auth | required if auth | required |
| `docs/security/data-classification.md` | optional | required if user data | required | required |
| `docs/security/secrets-management.md` | required | required | required | required |
| `docs/security/threat-model.md` | optional | required if sensitive data/payments | required | required |
| `docs/security/audit-logging.md` | optional | optional | required if admin/data actions | required |
| `docs/security/risk-register.md` | optional | optional | required | required |
| `docs/security/privacy-and-compliance.md` | optional | optional | required if personal data/payments | required |
| `docs/security/data-retention.md` | optional | optional | required if user data | required |
| `docs/security/abuse-and-fraud.md` | optional | optional | required if public signup/payments/API | required |
| `docs/security/access-review.md` | optional | optional | optional | required |
| `docs/security/compliance-controls.md` | optional | optional | optional | required |
| `docs/security/vulnerability-management.md` | optional | optional | required for public production | required |
| `docs/operations/environments.md` | optional | required | required | required |
| `docs/operations/deployment.md` | optional | required | required | required |
| `docs/operations/monitoring-and-alerts.md` | optional | optional | required | required |
| `docs/operations/rollback.md` | optional | required | required | required |
| `docs/operations/backup-and-restore.md` | optional | optional | required if data stored | required |
| `docs/operations/service-levels.md` | optional | optional | required | required |
| `docs/operations/incident-levels.md` | optional | optional | required | required |
| `docs/operations/incident-response.md` | optional | optional | required | required |
| `docs/operations/incident-notification.md` | optional | optional | optional | required |
| `docs/operations/postmortem-template.md` | optional | optional | required after real incidents | required |
| `docs/operations/disaster-recovery.md` | optional | optional | optional | required |
| `docs/support/support-runbook.md` | optional | optional | required | required |
| `docs/support/common-issues.md` | optional | optional | required if users exist | required |
| `docs/support/escalation-rules.md` | optional | optional | required if support/team exists | required |
| `docs/legal/legal-readiness.md` | optional | optional | required | required |
| `docs/legal/privacy-policy-notes.md` | optional | optional | required if personal data | required |
| `docs/legal/terms-notes.md` | optional | optional | required if public product | required |
| `docs/legal/data-processing-agreement.md` | optional | optional | optional | required if B2B/personal data |