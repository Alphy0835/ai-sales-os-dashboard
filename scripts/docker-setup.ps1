function Get-DevPlatform {
    if ($IsWindows -or ($env:OS -match "Windows")) { return "windows" }
    if ($IsMacOS) { return "macos" }
    if ($IsLinux) { return "linux" }
    return "unknown"
}

function Get-DockerStatus {
    $cmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return @{ State = "missing"; Message = "Docker CLI not found in PATH" }
    }
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        return @{ State = "ready"; Message = "Docker daemon is running" }
    }
    return @{ State = "stopped"; Message = "Docker installed but daemon is not running (start Docker Desktop)" }
}

function Show-DockerInstallGuide([string]$Platform) {
    Write-Host ""
    Write-Host "Docker setup for platform: $Platform" -ForegroundColor Cyan
    switch ($Platform) {
        "windows" {
            Write-Host "  Recommended: Docker Desktop for Windows"
            Write-Host "  Auto:   winget install -e --id Docker.DockerDesktop"
            Write-Host "  Manual: https://docs.docker.com/desktop/setup/install/windows-install/"
            Write-Host "  After install: start Docker Desktop from Start menu, wait for Running."
        }
        "macos" {
            Write-Host "  Recommended: Docker Desktop for Mac"
            Write-Host "  Auto:   brew install --cask docker"
            Write-Host "  Manual: https://docs.docker.com/desktop/setup/install/mac-install/"
        }
        "linux" {
            Write-Host "  Recommended: Docker Engine + Compose plugin"
            Write-Host "  Ubuntu:  sudo apt install docker.io docker-compose-v2"
            Write-Host "  Manual:  https://docs.docker.com/engine/install/"
        }
        default {
            Write-Host "  https://docs.docker.com/get-docker/"
        }
    }
}

function Install-DockerAuto([string]$Platform) {
    switch ($Platform) {
        "windows" {
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
                Write-Host "winget not found. Install App Installer from Microsoft Store, or use manual download." -ForegroundColor Yellow
                Start-Process "https://docs.docker.com/desktop/setup/install/windows-install/"
                return $false
            }
            Write-Host "Installing Docker Desktop via winget (may require admin approval)..." -ForegroundColor Yellow
            winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -ne 0) { return $false }
            Write-Host "Install finished. Start Docker Desktop from Start menu, then press R to retry." -ForegroundColor Green
            return $true
        }
        "macos" {
            if (Get-Command brew -ErrorAction SilentlyContinue) {
                Write-Host "Installing Docker Desktop via Homebrew..." -ForegroundColor Yellow
                brew install --cask docker
                return ($LASTEXITCODE -eq 0)
            }
            Start-Process "https://docs.docker.com/desktop/setup/install/mac-install/"
            return $false
        }
        "linux" {
            Write-Host "Auto-install on Linux is distro-specific. Opening documentation..." -ForegroundColor Yellow
            Start-Process "https://docs.docker.com/engine/install/"
            return $false
        }
        default { return $false }
    }
}

function Wait-DockerReady([int]$TimeoutSeconds = 120) {
    Write-Host "Waiting for Docker daemon (up to $TimeoutSeconds s)..." -ForegroundColor Yellow
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $status = Get-DockerStatus
        if ($status.State -eq "ready") {
            Write-Host $status.Message -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Invoke-DockerSetupAssist {
    param(
        [switch]$InstallDocker,
        [switch]$NonInteractive
    )

    $platform = Get-DevPlatform
    $status = Get-DockerStatus
    if ($status.State -eq "ready") { return "ready" }

    Write-Host ""
    Write-Host "Docker: $($status.Message)" -ForegroundColor Yellow
    Show-DockerInstallGuide -Platform $platform

    if ($InstallDocker) {
        Install-DockerAuto -Platform $platform | Out-Null
        if (Wait-DockerReady) { return "ready" }
        return "local"
    }

    if ($NonInteractive) { return "local" }

    Write-Host ""
    Write-Host "Choose:" -ForegroundColor White
    Write-Host "  [I] Install Docker automatically (winget/brew where available)"
    Write-Host "  [D] Open download page in browser"
    Write-Host "  [R] Retry (after you started Docker Desktop)"
    Write-Host "  [L] Continue in LOCAL mode (SQLite, no Postgres/Redis)"
    Write-Host "  [Q] Quit"
    $choice = Read-Host "Option"

    switch ($choice.ToUpperInvariant()) {
        "I" {
            Install-DockerAuto -Platform $platform | Out-Null
            if (Wait-DockerReady) { return "ready" }
            Write-Host "Docker still not ready. Continuing in LOCAL mode." -ForegroundColor Yellow
            return "local"
        }
        "D" {
            switch ($platform) {
                "windows" { Start-Process "https://docs.docker.com/desktop/setup/install/windows-install/" }
                "macos" { Start-Process "https://docs.docker.com/desktop/setup/install/mac-install/" }
                default { Start-Process "https://docs.docker.com/get-docker/" }
            }
            return "local"
        }
        "R" {
            if (Wait-DockerReady) { return "ready" }
            Write-Host "Docker still not ready. Continuing in LOCAL mode." -ForegroundColor Yellow
            return "local"
        }
        "Q" { return "quit" }
        default { return "local" }
    }
}
