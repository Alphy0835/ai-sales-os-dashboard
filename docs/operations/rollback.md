Doc ID: OPS-ROLLBACK-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/deployment.md, docs/operations/backup-and-restore.md
Update together with: deployment.md, docker-compose.prod.yml
Update trigger: deploy process or migration strategy change
Review required: operations, backend
Maturity: L2

# Rollback

Use this **before** you need it: decide rollback criteria (error rate, failed smoke tests, data corruption) and keep the previous release tag noted in the deploy ticket.

## When to rollback

- API/web crash loop after deploy
- Critical regression (auth, tenant isolation, data loss)
- Failed smoke tests on staging/production immediately after cutover

Prefer **forward fix** for minor issues; rollback when user impact is high or root cause is unclear.

## Pre-rollback checklist

1. **Stop new traffic** (maintenance page or drain at load balancer) if the release is actively harmful.
2. **Backup current DB** even if broken — aids forensics:
   ```bash
   ./scripts/backup-postgres.sh
   ```
3. Note **current git tag/commit** and **target rollback tag/commit**.

## Roll back application (code + images)

Production stack: [`docker-compose.prod.yml`](../../docker-compose.prod.yml).

```bash
# 1. Check out previous known-good release
git fetch --tags
git checkout <previous-tag-or-commit>

# 2. Rebuild and recreate app containers (keep postgres volume)
docker compose -f docker-compose.prod.yml build api worker web
docker compose -f docker-compose.prod.yml up -d api worker web

# 3. Verify
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs api --tail 50
```

If images are tagged in a registry instead of local build:

```bash
# Pin image tags in compose override or env, then:
docker compose -f docker-compose.prod.yml pull api worker web
docker compose -f docker-compose.prod.yml up -d api worker web
```

**Do not** roll back `postgres` or `redis` images unless infrastructure requires it — data lives in the `postgres_data` volume.

## Migrations — important

Django migrations are **not automatically reversed** when rolling back code.

| Scenario | Action |
|---|---|
| New deploy added migrations; rollback to **older code** | Old code may break if new migrations already ran. Options: (1) restore DB from pre-deploy backup (see below), or (2) deploy a hotfix forward instead of rollback |
| Rollback **before** migrations applied | Safe — old code matches DB schema |
| Destructive migration (drop column/table) already applied | **Restore from backup**; code rollback alone is insufficient |

**Rule:** if migrations ran in production, treat rollback as a **database decision**, not only an image swap. Coordinate with [backup-and-restore.md](backup-and-restore.md).

Manual migration status check:

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py showmigrations
```

Never run `migrate` to a random older migration in prod without a written plan (`migrate <app> <migration_name>` can drop data).

## Environment variables

- Rollback **code** does not revert `.env` changes made during deploy.
- If a bad env var caused the incident, restore the previous `.env` from your secrets store and recreate affected services:
  ```bash
  docker compose -f docker-compose.prod.yml up -d api worker web
  ```

## Database restore (last resort)

If schema/data no longer matches rolled-back code:

1. Stop writers: `docker compose -f docker-compose.prod.yml stop api worker web`
2. Restore from pre-deploy backup — full procedure in [backup-and-restore.md](backup-and-restore.md)
3. Roll back code to the release that matches that backup
4. Start stack and re-run smoke tests

## Partial operations / Celery

- In-flight Celery tasks may fail after rollback if task code/schema changed. Monitor `worker` logs; replay failed jobs manually if needed.
- No automatic undo for side effects already committed (emails, webhooks) — handle case-by-case.

## Post-rollback

- Document incident (see `postmortem-template.md`)
- Fix forward on a branch; add regression tests before re-deploy
- Update [deployment.md](deployment.md) if deploy steps contributed to the failure
