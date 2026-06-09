Doc ID: SECURITY-SECRETS-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/architecture/integrations.md, docs/operations/environments.md
Update together with: integrations.md, environments.md
Update trigger: новый secret, provider или rotation policy
Review required: security, backend
Maturity: L2

# Secrets Management

## Rules

- **Never** commit `.env`, API keys, tokens, or passwords to git.
- **Never** log secrets, JWT tokens, or refresh tokens.
- Integration credentials (CRM, telephony, STT) stored outside User Level API — Django Admin / secret manager post-MVP.

## Local development

Copy `.env.example` → `.env`. Demo users have fixed passwords for local only.

## Production (planned)

- `DJANGO_SECRET_KEY` — long random string via env / K8s secret
- Integration API keys — env or vault; referenced by Integration Level only
- Database/Redis URLs — env, not in repo

## Related Docs

- [integrations.md](../architecture/integrations.md)
- [environments.md](../operations/environments.md)
