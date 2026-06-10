# Smoke test for local production-like stack (docker-compose.prod.yml).
# Run from repo root: .\scripts\local-prod-smoke.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$ComposeFile = "docker-compose.prod.yml"
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { "3000" }
$DemoEmail = if ($env:SMOKE_DEMO_EMAIL) { $env:SMOKE_DEMO_EMAIL } else { "manager@demo.local" }
$DemoPassword = if ($env:SMOKE_DEMO_PASSWORD) { $env:SMOKE_DEMO_PASSWORD } else { "demo1234" }

$Failures = 0

function Write-Ok([string]$Message) { Write-Host "OK: $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "WARN: $Message" -ForegroundColor Yellow }
function Write-Fail([string]$Message) {
    Write-Host "FAIL: $Message" -ForegroundColor Red
    $script:Failures++
}

function Import-EnvFile {
    $envPath = Join-Path $Root ".env"
    if (-not (Test-Path $envPath)) { return }
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "Env:$name" -Value $value
        }
    }
    if ($env:WEB_PORT) { $script:WebPort = $env:WEB_PORT }
}

function Test-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Fail "docker CLI not found — install Docker Desktop"
        return $false
    }
    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Docker daemon not running — start Docker Desktop and retry"
            return $false
        }
    } finally {
        $ErrorActionPreference = $prevErr
    }
    return $true
}

function Test-ComposeRunning {
    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $running = docker compose -f $ComposeFile ps --status running --services 2>&1
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($running)) {
            Write-Fail "docker-compose.prod.yml stack is not running"
            Write-Host ""
            Write-Host "Start the stack:"
            Write-Host "  Copy-Item .env.local-prod.example .env   # if you have no .env yet"
            Write-Host "  docker compose -f docker-compose.prod.yml up -d --build"
            Write-Host ""
            Write-Host "Optional demo users for login smoke:"
            Write-Host "  docker compose -f docker-compose.prod.yml exec api python manage.py seed_demo"
            return $false
        }
        $services = ($running -split "`n" | Where-Object { $_ }) -join ", "
        Write-Ok "compose services running: $services"
        return $true
    } finally {
        $ErrorActionPreference = $prevErr
    }
}

function Test-HttpHealth([string]$Url, [string]$Label) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
        if ($response.StatusCode -eq 200) {
            Write-Ok "$Label — HTTP 200 ($Url)"
            return $true
        }
        Write-Fail "$Label — HTTP $($response.StatusCode) ($Url)"
        return $false
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        Write-Fail "$Label — HTTP $code ($Url)"
        return $false
    }
}

function Test-DirectApiHealth {
    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $apiRunning = docker compose -f $ComposeFile ps --status running api 2>&1
        if ($LASTEXITCODE -ne 0 -or $apiRunning -notmatch "api") {
            Write-Warn "api service not running — skipped direct API health"
            return
        }
        docker compose -f $ComposeFile exec -T api python -c `
            "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/v1/health/ready/'); exit(0 if r.status == 200 else 1)" `
            2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Direct API health (in-container :8000)"
        } else {
            Write-Fail "Direct API health (in-container :8000)"
        }
    } finally {
        $ErrorActionPreference = $prevErr
    }
}

function Test-LoginSmoke {
    if ($env:SKIP_LOGIN_SMOKE -eq "1") {
        Write-Warn "login smoke skipped (SKIP_LOGIN_SMOKE=1)"
        return
    }

    $bffBase = "http://127.0.0.1:${WebPort}/api/v1"
    $loginUrl = "$bffBase/auth/login/"
    $body = @{ email = $DemoEmail; password = $DemoPassword } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest -Uri $loginUrl -Method POST -Body $body `
            -ContentType "application/json" -UseBasicParsing -TimeoutSec 15
        if ($response.StatusCode -eq 200) {
            Write-Ok "Login smoke ($DemoEmail) — HTTP 200"
            return
        }
        Write-Fail "Login smoke — HTTP $($response.StatusCode)"
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($code -eq 401 -or $code -eq 400) {
            Write-Warn "Login smoke skipped — demo user not seeded (HTTP $code). Run: docker compose -f $ComposeFile exec api python manage.py seed_demo"
            return
        }
        Write-Fail "Login smoke — HTTP $code"
    }
}

Write-Host "=== Local prod smoke (Gate A1) ==="
Import-EnvFile

if (-not (Test-DockerReady)) { exit 1 }
if (-not (Test-ComposeRunning)) { exit 1 }

$healthUrl = "http://127.0.0.1:${WebPort}/api/v1/health/ready/"
Test-HttpHealth -Url $healthUrl -Label "BFF health (web → api)" | Out-Null
Test-DirectApiHealth
Test-LoginSmoke

Write-Host ""
if ($Failures -gt 0) {
    Write-Host "Smoke finished with $Failures failure(s)."
    exit 1
}
Write-Host "Smoke passed."
