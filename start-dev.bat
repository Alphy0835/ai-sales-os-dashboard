@echo off
setlocal
cd /d "%~dp0"

title AI Sales OS - Start
echo.
echo  AI Sales OS - local dev launcher
echo  ================================
echo.
echo  Requires: Python 3.11+, Node.js 20+
echo  Docker optional - menu helps install (winget) or use LOCAL mode (SQLite)
echo  Opens API and Next.js in separate windows.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
set ERR=%ERRORLEVEL%

if %ERR% NEQ 0 (
    echo.
    echo  ERROR: launch failed ^(code %ERR%^).
    echo  Try: start-dev.bat -RunTests   ^(tests only, no Docker^)
    echo.
    pause
    exit /b %ERR%
)

echo.
echo  Launcher finished. Check the 3 PowerShell windows ^(API, Celery, Web^).
echo.
pause
exit /b 0
