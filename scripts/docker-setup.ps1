function Get-DevPlatform {
    if ($IsWindows -or ($env:OS -match "Windows")) { return "windows" }
    if ($IsMacOS) { return "macos" }
    if ($IsLinux) { return "linux" }
    return "unknown"
}

function Ensure-DockerCliInPath {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return $true }

    $extraPaths = @(
        "$env:ProgramFiles\Docker\Docker\resources\bin",
        "$env:ProgramFiles\Docker\Docker\resources"
    )
    foreach ($dir in $extraPaths) {
        if (Test-Path (Join-Path $dir "docker.exe")) {
            $env:PATH = "$dir;$env:PATH"
            return $true
        }
    }
    return $false
}

function Test-DockerDesktopInstalled([string]$Platform) {
    switch ($Platform) {
        "windows" {
            $desktopExe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
            if (Test-Path $desktopExe) { return $true }
            Ensure-DockerCliInPath | Out-Null
            if (Get-Command docker -ErrorAction SilentlyContinue) { return $true }
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
            $prevErr = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            try {
                $list = winget list --id Docker.DockerDesktop -e 2>&1 | Out-String
                return ($LASTEXITCODE -eq 0 -and $list -match "Docker\.DockerDesktop")
            } finally {
                $ErrorActionPreference = $prevErr
            }
        }
        "macos" {
            return (Test-Path "/Applications/Docker.app")
        }
        "linux" {
            Ensure-DockerCliInPath | Out-Null
            return [bool](Get-Command docker -ErrorAction SilentlyContinue)
        }
        default { return $false }
    }
}

function Start-DockerDesktopApp([string]$Platform) {
    switch ($Platform) {
        "windows" {
            $desktopExe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
            if (-not (Test-Path $desktopExe)) { return $false }
            $running = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
            if (-not $running) {
                Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
                Start-Process $desktopExe | Out-Null
            } else {
                Write-Host "Docker Desktop is already starting or running." -ForegroundColor DarkGray
            }
            return $true
        }
        "macos" {
            if (-not (Test-Path "/Applications/Docker.app")) { return $false }
            Start-Process "open" -ArgumentList "-a", "Docker" | Out-Null
            return $true
        }
    }
    return $false
}

function Invoke-DockerCli {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$DockerArgs
    )
    Ensure-DockerCliInPath | Out-Null
    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        & docker @DockerArgs 2>&1 | Out-Null
        if ($null -ne $LASTEXITCODE) { return $LASTEXITCODE }
        return 0
    } catch {
        return 1
    } finally {
        $ErrorActionPreference = $prevErr
    }
}

function Get-DockerStatus {
    $platform = Get-DevPlatform
    Ensure-DockerCliInPath | Out-Null
    $cli = Get-Command docker -ErrorAction SilentlyContinue
    $installed = Test-DockerDesktopInstalled -Platform $platform

    if ($cli -and (Invoke-DockerCli "info") -eq 0) {
        return @{
            State = "ready"
            Installed = $true
            CliInPath = $true
            Message = "Docker daemon is running"
        }
    }

    if ($installed -or $cli) {
        return @{
            State = "stopped"
            Installed = $true
            CliInPath = [bool]$cli
            Message = "Docker Desktop installed but daemon not running yet (start app, wait for Running)"
        }
    }

    return @{
        State = "missing"
        Installed = $false
        CliInPath = $false
        Message = "Docker is not installed"
    }
}

function Show-DockerInstallGuide([string]$Platform, [switch]$InstalledOnly) {
    Write-Host ""
    if ($InstalledOnly) {
        Write-Host "Docker already installed - start the app and wait for Running status." -ForegroundColor Cyan
        switch ($Platform) {
            "windows" {
                Write-Host "  Start menu: Docker Desktop"
                Write-Host "  Or press [S] here - launcher will try to start it."
            }
            "macos" { Write-Host "  Open Docker.app from Applications" }
            default { Write-Host "  Start docker service / Docker Desktop" }
        }
        return
    }

    Write-Host "Docker setup for platform: $Platform" -ForegroundColor Cyan
    switch ($Platform) {
        "windows" {
            Write-Host "  Recommended: Docker Desktop for Windows"
            Write-Host "  Auto:   winget install -e --id Docker.DockerDesktop"
            Write-Host "  Manual: https://docs.docker.com/desktop/setup/install/windows-install/"
        }
        "macos" {
            Write-Host "  Auto:   brew install --cask docker"
            Write-Host "  Manual: https://docs.docker.com/desktop/setup/install/mac-install/"
        }
        "linux" {
            Write-Host "  Ubuntu: sudo apt install docker.io docker-compose-v2"
            Write-Host "  Manual: https://docs.docker.com/engine/install/"
        }
        default { Write-Host "  https://docs.docker.com/get-docker/" }
    }
}

function Install-DockerAuto([string]$Platform) {
    if (Test-DockerDesktopInstalled -Platform $Platform) {
        Write-Host "Docker Desktop already installed - starting app..." -ForegroundColor Green
        Start-DockerDesktopApp -Platform $Platform | Out-Null
        return $true
    }

    switch ($Platform) {
        "windows" {
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
                Write-Host "winget not found. Install App Installer from Microsoft Store, or use manual download." -ForegroundColor Yellow
                Start-Process "https://docs.docker.com/desktop/setup/install/windows-install/"
                return $false
            }
            Write-Host "Installing Docker Desktop via winget (may require admin approval)..." -ForegroundColor Yellow
            $prevErr = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            try {
                winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
            } finally {
                $ErrorActionPreference = $prevErr
            }
            Ensure-DockerCliInPath | Out-Null
            if (Test-DockerDesktopInstalled -Platform $Platform) {
                Start-DockerDesktopApp -Platform $Platform | Out-Null
                return $true
            }
            return $false
        }
        "macos" {
            if (Get-Command brew -ErrorAction SilentlyContinue) {
                brew install --cask docker
                Start-DockerDesktopApp -Platform $Platform | Out-Null
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

    if ($status.Installed) {
        Show-DockerInstallGuide -Platform $platform -InstalledOnly
        Write-Host ""
        Write-Host "Trying to start Docker Desktop and wait for daemon..." -ForegroundColor Cyan
        Start-DockerDesktopApp -Platform $platform | Out-Null
        if (Wait-DockerReady -TimeoutSeconds 90) { return "ready" }
    } else {
        Show-DockerInstallGuide -Platform $platform
    }

    if ($InstallDocker) {
        Install-DockerAuto -Platform $platform | Out-Null
        if (Wait-DockerReady) { return "ready" }
        return "local"
    }

    if ($NonInteractive) { return "local" }

    Write-Host ""
    Write-Host "Choose:" -ForegroundColor White
    if ($status.Installed) {
        Write-Host "  [S] Start Docker Desktop again"
        Write-Host "  [R] Retry check (daemon ready?)"
    } else {
        Write-Host "  [I] Install Docker automatically (winget/brew where available)"
        Write-Host "  [D] Open download page in browser"
        Write-Host "  [R] Retry (after install / start Docker Desktop)"
    }
    Write-Host "  [L] Continue in LOCAL mode (SQLite, no Postgres/Redis)"
    Write-Host "  [Q] Quit"
    $defaultHint = if ($status.Installed) { "S" } else { "I" }
    $choice = Read-Host "Option (default $defaultHint)"

    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = $defaultHint }

    switch ($choice.ToUpperInvariant()) {
        "S" {
            Start-DockerDesktopApp -Platform $platform | Out-Null
            if (Wait-DockerReady) { return "ready" }
            Write-Host "Docker still not ready. Continuing in LOCAL mode." -ForegroundColor Yellow
            return "local"
        }
        "I" {
            if ($status.Installed) {
                Start-DockerDesktopApp -Platform $platform | Out-Null
            } else {
                Install-DockerAuto -Platform $platform | Out-Null
            }
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
