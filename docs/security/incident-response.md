Doc ID: SECURITY-IR-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/operations/backup-and-restore.md, docs/operations/rollback.md, docs/operations/incident-notification.md, docs/security/threat-model.md, docs/security/data-retention.md
Update together with: backup-and-restore.md, rollback.md, threat-model.md
Update trigger: новый incident type, изменение backup/rollback/purge процедур
Review required: security, operations
Maturity: L2

# Incident Response

Пошаговый runbook для AI Sales OS (solo/small team). Принцип: **обнаружить → изолировать → исправить → восстановить → уведомить → разобрать**.

## Severity

| Level | Examples | Response time (target) |
|---|---|---|
| SEV-1 | Cross-tenant data leak; DB compromise; mass auth bypass | Immediate — stop traffic, preserve evidence |
| SEV-2 | Scope bypass in prod; stolen LLM/DB secret; prolonged outage | < 1 hour |
| SEV-3 | Login brute-force spike; single-tenant data bug; failed deploy | < 4 hours |
| SEV-4 | Non-security bug, degraded AI fallback | Next business day |

## Roles (MVP)

| Role | Responsibility |
|---|---|
| On-call / owner | Triage, execute runbook, communicate |
| Backend | API fixes, migrations, purge/retention |
| Ops | Backups, rollback, compose/host |

## General Flow

```
Detect → Triage (SEV) → Contain → Eradicate/Fix → Recover → Notify → Postmortem
```

---

## Scenario 1 — Suspected cross-tenant or scope leak (SEV-1/2)

**Triggers:** Customer report, failed `test_security_scope`, abnormal audit `scope_denied` spike.

1. **Confirm** — reproduce on staging with affected user IDs; check `AuditLog` for `scope_denied`.
2. **Contain** — if active exploit: disable affected endpoint via hotfix or maintenance mode; do **not** delete audit rows.
3. **Fix** — patch view/queryset filters (`recordings_queryset`, `reports_queryset`, tenant_id); add regression test.
4. **Recover** — deploy forward fix per [deployment.md](../operations/deployment.md); run full API test suite.
5. **Notify** — enterprise customers if their data was exposed; see [incident-notification.md](../operations/incident-notification.md) (template TBD).
6. **Postmortem** — [postmortem-template.md](../operations/postmortem-template.md); update [threat-model.md](threat-model.md).

---

## Scenario 2 — Stolen JWT / compromised user account (SEV-2)

**Triggers:** User report, suspicious `permission_change` audit entries from unknown IP.

1. **Contain** — deactivate user (`is_active=false`) in Django Admin; rotate tenant LLM keys if agent was abused.
2. **Eradicate** — force password reset (Admin); user clears browser storage / re-login.
3. **Note** — no server-side refresh blacklist yet; stolen refresh token valid until expiry — prioritize httpOnly BFF (threat-model T1).
4. **Review** — audit log for that actor; check for out-of-scope API access patterns.

---

## Scenario 3 — Leaked secret (DJANGO_SECRET_KEY, DB URL, OpenRouter key) (SEV-1/2)

1. **Rotate immediately** — new secret in env/secrets store; recreate `api` + `worker` containers.
2. **OpenRouter** — rotate key in provider dashboard; update Fernet-encrypted tenant/workspace keys in Admin.
3. **DB credentials** — rotate Postgres password; update `.env`; restart stack.
4. **Assess** — if `SECRET_KEY` leaked, treat all JWTs as compromised; users must re-login after deploy.

---

## Scenario 4 — Bad deploy / outage (SEV-2/3)

Follow [rollback.md](../operations/rollback.md):

1. **Backup current DB** (even if broken): `./scripts/backup-postgres.sh`
2. **Rollback code** — checkout previous tag; rebuild `api`, `worker`, `web` via `docker-compose.prod.yml`
3. **Migrations** — if new migrations already applied, code rollback alone may be insufficient → restore DB from pre-deploy backup ([backup-and-restore.md](../operations/backup-and-restore.md))
4. **Verify** — `showmigrations`, schema curl, login smoke test
5. **Postmortem** — document; fix forward with tests before re-deploy

---

## Scenario 5 — Data corruption or accidental mass delete (SEV-1/2)

1. **Stop writers** — `docker compose -f docker-compose.prod.yml stop api worker web`
2. **Identify scope** — tenant, tables, time window
3. **Restore** — full or point-in-time from latest good backup ([backup-and-restore.md](../operations/backup-and-restore.md))
4. **Align code** — rolled-back release must match backup schema ([rollback.md](../operations/rollback.md))
5. **Verify** — spot-check tenant transcripts, users, permissions

---

## Scenario 6 — Retention / purge misconfiguration (SEV-3)

**Triggers:** Transcripts deleted too early/late; `purge_transcripts` run without `--dry-run`.

| Control | Location |
|---|---|
| Setting | `TRANSCRIPT_RETENTION_DAYS` (default **90**) |
| Celery task | `integrations.purge_expired_transcripts` |
| Manual ops | `python manage.py purge_transcripts --dry-run` |

**Response:**

1. **Stop scheduled purge** — disable Celery beat entry or task until config verified.
2. **Dry-run** — `manage.py purge_transcripts --dry-run` to preview counts.
3. **Fix config** — correct env; redeploy worker.
4. **If wrongful delete** — restore PostgreSQL from backup taken before purge (see Scenario 5). Purge is **hard delete** — no soft-delete recovery without backup.

Policy reference: [data-retention.md](data-retention.md).

---

## Scenario 7 — Brute-force / API abuse (SEV-3)

1. **Verify throttles active** — `THROTTLE_LOGIN=10/min`, `THROTTLE_AGENT=30/min` in prod `.env`
2. **Block at edge** — WAF / firewall rate limit if sustained attack
3. **Review logs** — login 429 responses; affected accounts
4. **No action needed** if throttles working — document in postmortem if novel pattern

---

## Evidence Preservation

- Take DB backup before destructive recovery: `./scripts/backup-postgres.sh`
- Export relevant `AuditLog` rows and application logs with timestamps
- Note git commit, deploy ticket, env diff

## Communication

| Audience | When | Channel |
|---|---|---|
| Affected tenant admins | Confirmed data impact | Email (see incident-notification TBD) |
| Internal | All SEV-1/2 | Owner notes + postmortem |
| Regulators | If legally required | Legal review — not automated in MVP |

## Recovery Verification Checklist

- [ ] API tests pass (`python manage.py test`)
- [ ] Login + refresh work; throttles not breaking legitimate traffic
- [ ] Sample manager sees only scoped workspaces
- [ ] `GET /api/v1/audit/permissions/` loads with valid `limit`
- [ ] Celery worker healthy; purge dry-run expected counts
- [ ] Web build succeeds (`npm run build`)

## Related Docs

- [backup-and-restore.md](../operations/backup-and-restore.md)
- [rollback.md](../operations/rollback.md)
- [deployment.md](../operations/deployment.md)
- [data-retention.md](data-retention.md)
- [threat-model.md](threat-model.md)
- [postmortem-template.md](../operations/postmortem-template.md)
