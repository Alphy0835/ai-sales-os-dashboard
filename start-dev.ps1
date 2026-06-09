# AI Sales OS - one-file local dev launcher (Windows)
# Usage:  .\start-dev.ps1
#         .\start-dev.ps1 -DockerAll
#         .\start-dev.ps1 -RunTests
#         .\start-dev.ps1 -RequireDocker   # fail if Docker unavailable
#         .\start-dev.ps1 -InstallDocker   # try winget install (Windows)
#         .\start-dev.ps1 -NonInteractive  # no prompts, LOCAL mode if no Docker

param(
    [switch]$DockerAll,
    [switch]$RunTests,
    [switch]$RequireDocker,
    [switch]$InstallDocker,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Import-DotEnv([string]$path) {
    if (-not (Test-Path $path)) { return }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $key = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        Set-Item -Path "Env:$key" -Value $val
    }
}

function Escape-Sq([string]$Value) {
    return $Value -replace "'", "''"
}

function Wait-Postgres {
    Write-Step "Waiting for PostgreSQL..."
    $deadline = (Get-Date).AddMinutes(2)
    while ((Get-Date) -lt $deadline) {
        docker compose exec -T postgres pg_isready -U ai_sales_os 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL is ready." -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "PostgreSQL did not become ready in time. Check: docker compose logs postgres"
}

function Test-DockerReady {
    return (Get-DockerStatus).State -eq "ready"
}

. (Join-Path $Root "scripts\docker-setup.ps1")

function Set-LocalDevMode([string]$ApiDir) {
    $dbPath = (Join-Path $ApiDir "db.sqlite3") -replace "\\", "/"
    $env:DATABASE_URL = "sqlite:///$dbPath"
    $env:CELERY_TASK_ALWAYS_EAGER = "true"
}

function Ensure-PythonVenv([string]$ApiDir) {
    $venvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Step "Creating Python venv..."
        python -m venv (Join-Path $ApiDir ".venv")
    }
    return $venvPython
}

Write-Host "AI Sales OS - local test launcher" -ForegroundColor White
$platform = Get-DevPlatform
Write-Host "Platform: $platform" -ForegroundColor DarkGray

function Test-CommandExists([string]$name) {
    return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "python")) {
    throw "Python not found. Install Python 3.11+ and add it to PATH."
}

if (-not (Test-Path "$Root\.env")) {
    Write-Step "Creating .env from .env.example"
    Copy-Item "$Root\.env.example" "$Root\.env"
}
Import-DotEnv "$Root\.env"

$ApiDir = Join-Path $Root "apps\api"
$WebDir = Join-Path $Root "apps\web"
$dockerReady = Test-DockerReady
$useLocalMode = $false

Write-Step "Starting Docker services..."
if ($DockerAll) {
    if (-not $dockerReady) { throw "Docker not available. Start Docker Desktop or run without -DockerAll." }
    docker compose up --build -d
    Wait-Postgres
    Write-Host ""
    Write-Host "All services run in Docker." -ForegroundColor Green
    Write-Host "  Web:  http://localhost:3000"
    Write-Host "  API:  http://localhost:8000/api/v1/health/"
    Write-Host "  Demo: manager@demo.local / demo1234"
    Write-Host ""
    Write-Host "Logs: docker compose logs -f api web worker"
    Write-Host "Stop: docker compose down"
    exit 0
}

if (-not $dockerReady) {
    if ($RequireDocker) {
        $assist = Invoke-DockerSetupAssist -InstallDocker:$true
        if ($assist -eq "ready") { $dockerReady = $true }
        elseif ($assist -eq "quit") { exit 1 }
        else { throw "Docker is required but not available." }
    }
    elseif ($RunTests) {
        Write-Host "Docker not available - using SQLite for API tests." -ForegroundColor Yellow
        Set-LocalDevMode -ApiDir $ApiDir
    }
    else {
        $assist = Invoke-DockerSetupAssist -InstallDocker:$InstallDocker -NonInteractive:$NonInteractive
        if ($assist -eq "quit") { exit 0 }
        if ($assist -eq "ready") {
            $dockerReady = $true
        } else {
            Write-Host "Using LOCAL mode (SQLite, no Redis/Celery worker)." -ForegroundColor Yellow
            Set-LocalDevMode -ApiDir $ApiDir
            $useLocalMode = $true
        }
    }
}

if ($dockerReady) {
    docker compose up -d postgres redis
    if ($LASTEXITCODE -ne 0) {
        if ($RequireDocker) { throw "docker compose failed. Is Docker Desktop running?" }
        Write-Host "docker compose failed - falling back to LOCAL mode." -ForegroundColor Yellow
        Set-LocalDevMode -ApiDir $ApiDir
        $useLocalMode = $true
        $dockerReady = $false
    } else {
        Wait-Postgres
    }
}

$py = Ensure-PythonVenv -ApiDir $ApiDir

Write-Step "Installing API dependencies..."
& $py -m pip install -q -r (Join-Path $ApiDir "requirements.txt")

Write-Step "Migrating database and seeding demo data..."
if ($RunTests -or $useLocalMode) {
    Set-LocalDevMode -ApiDir $ApiDir
}
Push-Location $ApiDir
& $py manage.py migrate --noinput
& $py manage.py seed_demo
Pop-Location

if ($RunTests) {
    Write-Step "Running API tests..."
    Push-Location $ApiDir
    $env:CELERY_TASK_ALWAYS_EAGER = "true"
    & $py manage.py test accounts.tests integrations.tests analytics.tests -v 1
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { exit $code }
    Write-Host ""
    Write-Host "All tests passed." -ForegroundColor Green
    exit 0
}

if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
    if (-not (Test-CommandExists "npm")) {
        throw "npm not found. Install Node.js 20+ or run with -RunTests only."
    }
    Write-Step "Installing web dependencies (npm install)..."
    Push-Location $WebDir
    npm install
    Pop-Location
}

Write-Step "Starting API and Next.js (new windows)..."

$launcherDir = Join-Path $env:TEMP "ai-sales-os-launch"
New-Item -ItemType Directory -Force -Path $launcherDir | Out-Null

$dbLine = '$env:DATABASE_URL = ''' + (Escape-Sq $env:DATABASE_URL) + ''''
$redisLine = '$env:REDIS_URL = ''' + (Escape-Sq $env:REDIS_URL) + ''''
$corsLine = '$env:CORS_ALLOWED_ORIGINS = ''' + (Escape-Sq $env:CORS_ALLOWED_ORIGINS) + ''''
$publicApiLine = '$env:NEXT_PUBLIC_API_URL = ''' + (Escape-Sq $env:NEXT_PUBLIC_API_URL) + ''''
$eagerLine = '$env:CELERY_TASK_ALWAYS_EAGER = ''true'''

$apiScript = Join-Path $launcherDir "run-api.ps1"
$workerScript = Join-Path $launcherDir "run-worker.ps1"
$webScript = Join-Path $launcherDir "run-web.ps1"

$apiLines = @(
    "Set-Location '$ApiDir'"
    $dbLine
    $redisLine
    $corsLine
)
if ($useLocalMode) { $apiLines += $eagerLine }
$apiLines += @(
    "Write-Host 'Django API http://localhost:8000' -ForegroundColor Cyan"
    ('& "{0}" manage.py runserver 0.0.0.0:8000' -f $py)
)
$apiLines | Set-Content -Path $apiScript -Encoding UTF8

if (-not $useLocalMode) {
    $workerLines = @(
        "Set-Location '$ApiDir'"
        $dbLine
        $redisLine
        "Write-Host 'Celery worker' -ForegroundColor Cyan"
        ('& "{0}" -m celery -A config worker -l info' -f $py)
    )
    $workerLines | Set-Content -Path $workerScript -Encoding UTF8
}

$webLines = @(
    "Set-Location '$WebDir'"
    $publicApiLine
    "Write-Host 'Next.js http://localhost:3000' -ForegroundColor Cyan"
    "npm run dev"
)
$webLines | Set-Content -Path $webScript -Encoding UTF8

Start-Process powershell.exe -ArgumentList "-NoExit", "-File", $apiScript
Start-Sleep -Seconds 1
if (-not $useLocalMode) {
    Start-Process powershell.exe -ArgumentList "-NoExit", "-File", $workerScript
    Start-Sleep -Seconds 1
}
Start-Process powershell.exe -ArgumentList "-NoExit", "-File", $webScript

Write-Host ""
if ($useLocalMode) {
    Write-Host "Local stack started (LOCAL mode - SQLite, no Docker)." -ForegroundColor Green
} else {
    Write-Host "Local stack started (Docker Postgres + Redis)." -ForegroundColor Green
}
Write-Host "  Web:  http://localhost:3000"
Write-Host "  API:  http://localhost:8000/api/v1/health/"
Write-Host "  Docs: http://localhost:8000/api/docs/"
Write-Host ""
Write-Host "Demo logins (password: demo1234):"
Write-Host "  manager@demo.local    -> /manager"
Write-Host "  regional@demo.local   -> sub-manager"
Write-Host "  employee@demo.local   -> /employee"
Write-Host ""
if ($useLocalMode) {
    Write-Host "Mode: LOCAL (SQLite). For full stack install Docker Desktop."
} else {
    Write-Host "Infra stop: docker compose stop postgres redis"
}
Write-Host "Run tests:  test.bat"
