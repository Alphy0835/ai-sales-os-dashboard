Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:
<!-- security-checklist.md — проверка безопасности перед релизом. Что размещается: checklist по auth, ролям, валидации, CORS, rate limit, secrets, logs, backups, permissions. Правило: использовать перед каждым важным релизом или запуском новой критичной фичи. -->


<!-- Файл может содержать в себе не все элементы описанные сейчас, а так же может иметь и дополнения и расширения в зафисимости от специфики проекта -->
# Security Checklist

## Auth / Access
- [ ] Roles and permissions checked
- [ ] Admin actions protected
- [ ] Unauthorized access denied

## Data
- [ ] Sensitive data identified
- [ ] Secrets are not stored in code
- [ ] Logs do not contain passwords, tokens or unnecessary personal data

## API / Integration
- [ ] Input validation checked
- [ ] Rate limits considered if needed
- [ ] External service keys documented in secrets-management

## Release
- [ ] Security-impacting features reviewed
- [ ] Known risks added to risk-register
- [ ] Incident/rollback docs checked if needed