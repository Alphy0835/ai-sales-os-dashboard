#!/usr/bin/env bash
# Docker detection and install assist (macOS / Linux). Sourced by start-dev.sh

_log() { echo "$@" >&2; }

detect_platform() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux) echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) echo "unknown" ;;
  esac
}

docker_status() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "missing"
    return
  fi
  if docker info >/dev/null 2>&1; then
    echo "ready"
  else
    echo "stopped"
  fi
}

show_docker_guide() {
  local platform="$1"
  _log ""
  _log "Docker setup for platform: $platform"
  case "$platform" in
    macos)
      _log "  Auto:   brew install --cask docker"
      _log "  Manual: https://docs.docker.com/desktop/setup/install/mac-install/"
      ;;
    linux)
      _log "  Ubuntu: sudo apt install docker.io docker-compose-v2"
      _log "  Manual: https://docs.docker.com/engine/install/"
      ;;
    *)
      _log "  https://docs.docker.com/get-docker/"
      ;;
  esac
}

install_docker_auto() {
  local platform="$1"
  case "$platform" in
    macos)
      if command -v brew >/dev/null 2>&1; then
        _log "Installing Docker Desktop via Homebrew..."
        brew install --cask docker
        return $?
      fi
      open "https://docs.docker.com/desktop/setup/install/mac-install/" 2>/dev/null || true
      return 1
      ;;
    linux)
      if command -v apt-get >/dev/null 2>&1; then
        _log "Run: sudo apt update && sudo apt install -y docker.io docker-compose-v2"
        _log "Then: sudo usermod -aG docker \$USER  (re-login required)"
      fi
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "https://docs.docker.com/engine/install/" 2>/dev/null || true
      fi
      return 1
      ;;
  esac
}

wait_docker_ready() {
  local timeout="${1:-120}"
  local i=0
  _log "Waiting for Docker daemon (up to ${timeout}s)..."
  while [ "$i" -lt "$timeout" ]; do
    if [ "$(docker_status)" = "ready" ]; then
      _log "Docker daemon is running"
      return 0
    fi
    sleep 3
    i=$((i + 3))
  done
  return 1
}

# Prints only the result to stdout: ready | local | quit
docker_setup_assist() {
  local platform
  platform="$(detect_platform)"
  local status
  status="$(docker_status)"

  if [ "$status" = "ready" ]; then
    echo "ready"
    return 0
  fi

  _log ""
  _log "Docker: ${status} on ${platform}"
  show_docker_guide "$platform"

  if [ "${INSTALL_DOCKER:-0}" = "1" ]; then
    install_docker_auto "$platform" || true
    wait_docker_ready && { echo "ready"; return 0; }
    echo "local"
    return 0
  fi

  if [ "${NONINTERACTIVE:-0}" = "1" ]; then
    echo "local"
    return 0
  fi

  _log ""
  _log "Choose: [I] Install  [D] Download page  [R] Retry  [L] LOCAL mode  [Q] Quit"
  read -r choice
  case "$(echo "$choice" | tr '[:lower:]' '[:upper:]')" in
    I)
      install_docker_auto "$platform" || true
      wait_docker_ready && { echo "ready"; return 0; }
      _log "Docker still not ready. Continuing in LOCAL mode."
      echo "local"
      ;;
    D)
      case "$platform" in
        macos) open "https://docs.docker.com/desktop/setup/install/mac-install/" 2>/dev/null || true ;;
        *) xdg-open "https://docs.docker.com/get-docker/" 2>/dev/null || true ;;
      esac
      echo "local"
      ;;
    R)
      wait_docker_ready && { echo "ready"; return 0; }
      _log "Docker still not ready. Continuing in LOCAL mode."
      echo "local"
      ;;
    Q) echo "quit" ;;
    *) echo "local" ;;
  esac
}
