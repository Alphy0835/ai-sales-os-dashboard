Doc ID: OPS-BACKUP-001
Status: active
Source of truth: yes
Owner: operations
Related docs: docs/operations/deployment.md, docs/operations/rollback.md, docs/operations/disaster-recovery.md
Update together with: scripts/backup-postgres.sh, scripts/backup-postgres.ps1, docker-compose.prod.yml
Update trigger: database host, backup schedule, or retention policy change
Review required: operations
Maturity: L2

# Backup and Restore

## What is backed up

| Asset | Method | Location |
|---|---|---|
| PostgreSQL (all app data) | `pg_dump` via scripts | `backups/<db>_YYYYMMDD_HHMMSS.sql.gz` |
| Redis | Not backed up | Ephemeral Celery broker; safe to rebuild |
| Uploaded media | Not automated | `apps/api/media/` — add object storage before prod scale |
| Secrets / `.env` | Out of band | Password manager or host secrets store |

**Rule:** a backup is not trusted until restore has been tested at least once per quarter.

## Backup scripts

Repo root scripts (read credentials from `.env`):

| OS | Script |
|---|---|
| macOS / Linux | [`scripts/backup-postgres.sh`](../../scripts/backup-postgres.sh) |
| Windows | [`scripts/backup-postgres.ps1`](../../scripts/backup-postgres.ps1) |

Behavior:

1. Creates `backups/` if missing (directory is gitignored)
2. Detects running Postgres: `docker-compose.prod.yml` → `docker-compose.yml` → local `pg_dump`
3. Writes compressed SQL: `backups/ai_sales_os_20260609_143000.sql.gz`

### Manual run

```bash
./scripts/backup-postgres.sh
```

```powershell
.\scripts\backup-postgres.ps1
```

### Scheduled backups (recommended)

**Linux (cron)** — daily at 02:00 UTC, from repo root:

```cron
0 2 * * * cd /opt/ai-sales-os && ./scripts/backup-postgres.sh >> /var/log/ai-sales-os-backup.log 2>&1
```

**Windows (Task Scheduler)** — run `powershell.exe -File C:\path\to\repo\scripts\backup-postgres.ps1` on a daily trigger.

Copy `backups/*.sql.gz` off-host (S3, NAS, managed backup) within 24 hours. Retain at least **30 days** for production; align with legal/compliance if recordings contain personal data.

### Pre-deploy backup

Required in [deployment.md](deployment.md) before every production deploy.

## Access control

- Backup files contain full database contents (users, tenants, conversation metadata).
- Restrict filesystem permissions on `backups/` and encrypted off-host storage.
- Only operations / on-call roles get restore access.

## Restore procedure

**Warning:** restore **overwrites** the target database. Stop application writers first.

### 1. Stop API and worker

```bash
docker compose -f docker-compose.prod.yml stop api worker web
```

### 2. Restore into Postgres container

Replace `<backup-file>` with the chosen `backups/*.sql.gz`:

```bash
# Drop and recreate database (destructive)
docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_sales_os -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ai_sales_os' AND pid <> pg_backend_pid();"

docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_sales_os -d postgres -c \
  "DROP DATABASE IF EXISTS ai_sales_os;"

docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_sales_os -d postgres -c \
  "CREATE DATABASE ai_sales_os OWNER ai_sales_os;"

# Restore
gunzip -c backups/<backup-file> | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_sales_os -d ai_sales_os
```

**Windows (PowerShell)** — decompress then pipe:

```powershell
$backup = "backups\ai_sales_os_20260609_020000.sql.gz"
$tempSql = "$env:TEMP\restore.sql"
$in = [System.IO.File]::OpenRead((Resolve-Path $backup))
$gzip = New-Object System.IO.Compression.GZipStream($in, [System.IO.Compression.CompressionMode]::Decompress)
$out = [System.IO.File]::Create($tempSql)
$gzip.CopyTo($out)
$out.Close(); $gzip.Close(); $in.Close()

Get-Content $tempSql -Raw | docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_sales_os -d ai_sales_os
```

Adjust `ai_sales_os` user/db names if your `.env` differs.

### 3. Start application

```bash
docker compose -f docker-compose.prod.yml up -d api worker web
```

### 4. Verify

```bash
docker compose -f docker-compose.prod.yml exec api python manage.py showmigrations
curl -f http://localhost:8000/api/schema/
```

Log in via web UI and spot-check tenant data.

## Restore drill (required)

At least quarterly on staging:

1. Take backup with script
2. Restore to a **separate** database or disposable compose stack
3. Run API smoke tests
4. Record date and result in ops notes

## Managed Postgres alternative

If production uses a managed provider (RDS, Cloud SQL, etc.) instead of the compose `postgres` service:

- Enable provider automated backups + PITR
- Still use `pg_dump` scripts against the provider connection string for portable copies
- Update `DATABASE_URL` in `.env`; scripts fall back to `pg_dump "$DATABASE_URL"` when no local container runs

## Related

- [rollback.md](rollback.md) — when restore is needed after a bad deploy
- [deployment.md](deployment.md) — deploy order and migrate/collectstatic
