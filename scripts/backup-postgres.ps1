# Dump PostgreSQL to backups\<db>_<timestamp>.sql.gz
# Run from repo root: .\scripts\backup-postgres.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

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
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Root "backups"
$Output = Join-Path $OutDir "${PostgresDb}_${Timestamp}.sql.gz"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Invoke-ComposeDump {
    param([string]$ComposeFile)
    docker compose -f $ComposeFile exec -T postgres `
        pg_dump -U $PostgresUser --no-owner --no-acl $PostgresDb
}

function Write-GzipFile {
    param([byte[]]$Bytes, [string]$Path)
    $outStream = [System.IO.File]::Create($Path)
    try {
        $gzip = New-Object System.IO.Compression.GZipStream(
            $outStream,
            [System.IO.Compression.CompressionMode]::Compress
        )
        try {
            $gzip.Write($Bytes, 0, $Bytes.Length)
        } finally {
            $gzip.Dispose()
        }
    } finally {
        $outStream.Dispose()
    }
}

$ProdRunning = docker compose -f docker-compose.prod.yml ps postgres --status running -q 2>$null
$DevRunning = docker compose ps postgres --status running -q 2>$null

if ($ProdRunning) {
    $dump = Invoke-ComposeDump "docker-compose.prod.yml"
}
elseif ($DevRunning) {
    $dump = Invoke-ComposeDump "docker-compose.yml"
}
elseif (Get-Command pg_dump -ErrorAction SilentlyContinue) {
    $DatabaseUrl = if ($env:DATABASE_URL) {
        $env:DATABASE_URL
    } else {
        "postgres://${PostgresUser}:$($env:POSTGRES_PASSWORD)@localhost:5432/${PostgresDb}"
    }
    $dump = pg_dump $DatabaseUrl --no-owner --no-acl
}
else {
    Write-Error "No running postgres container and pg_dump not found."
}

$bytes = [System.Text.Encoding]::UTF8.GetBytes($dump)
Write-GzipFile -Bytes $bytes -Path $Output
Write-Host "Backup written to $Output"
