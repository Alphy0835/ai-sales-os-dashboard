# Restore PostgreSQL from a .sql.gz backup into docker-compose.prod.yml postgres.
# Usage (repo root): .\scripts\restore-postgres-local.ps1 backups\ai_sales_os_YYYYMMDD_HHMMSS.sql.gz
#
# Destructive: drops and recreates the application database. Stops api/worker/beat/web during restore.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BackupPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$ComposeFile = "docker-compose.prod.yml"

$ResolvedBackup = Resolve-Path -LiteralPath $BackupPath -ErrorAction Stop

$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

$PostgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "ai_sales_os" }
$PostgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "ai_sales_os" }

$PostgresRunning = docker compose -f $ComposeFile ps postgres --status running -q 2>$null
if (-not $PostgresRunning) {
    Write-Error "Postgres is not running. Start stack first: docker compose -f $ComposeFile up -d postgres"
}

Write-Host "Stopping writers (api, worker, beat, web)..."
docker compose -f $ComposeFile stop api worker beat web 2>$null

Write-Host "Recreating database $PostgresDb..."
docker compose -f $ComposeFile exec -T postgres psql -U $PostgresUser -d postgres -c `
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$PostgresDb' AND pid <> pg_backend_pid();"

docker compose -f $ComposeFile exec -T postgres psql -U $PostgresUser -d postgres -c `
    "DROP DATABASE IF EXISTS $PostgresDb;"

docker compose -f $ComposeFile exec -T postgres psql -U $PostgresUser -d postgres -c `
    "CREATE DATABASE $PostgresDb OWNER $PostgresUser;"

Write-Host "Restoring from $ResolvedBackup..."
$tempSql = Join-Path $env:TEMP "restore_$PostgresDb.sql"
try {
    $inStream = [System.IO.File]::OpenRead($ResolvedBackup)
    try {
        $gzip = New-Object System.IO.Compression.GZipStream(
            $inStream,
            [System.IO.Compression.CompressionMode]::Decompress
        )
        try {
            $outStream = [System.IO.File]::Create($tempSql)
            try {
                $gzip.CopyTo($outStream)
            } finally {
                $outStream.Dispose()
            }
        } finally {
            $gzip.Dispose()
        }
    } finally {
        $inStream.Dispose()
    }

    $containerSql = "/tmp/restore_$PostgresDb.sql"
    docker compose -f $ComposeFile cp $tempSql "postgres:$containerSql"
    docker compose -f $ComposeFile exec -T postgres psql -v ON_ERROR_STOP=1 -U $PostgresUser -d $PostgresDb -f $containerSql
    if ($LASTEXITCODE -ne 0) {
        throw "psql restore failed with exit code $LASTEXITCODE"
    }
    docker compose -f $ComposeFile exec -T postgres rm -f $containerSql 2>$null
} finally {
    if (Test-Path $tempSql) {
        Remove-Item $tempSql -Force
    }
}

Write-Host "Starting application services..."
docker compose -f $ComposeFile up -d api worker beat web

Write-Host ""
Write-Host "Restore complete. Verify:"
Write-Host "  curl -sf http://127.0.0.1:3000/api/v1/health/ready/"
Write-Host "  docker compose -f $ComposeFile exec api python manage.py showmigrations | tail -5"
Write-Host "See docs/operations/local-gate-checklist.md — A3 restore drill."
