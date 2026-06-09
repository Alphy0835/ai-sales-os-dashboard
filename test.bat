@echo off
setlocal
cd /d "%~dp0"

title AI Sales OS - Tests
echo.
echo  AI Sales OS - API tests only
echo  =============================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" -RunTests
set ERR=%ERRORLEVEL%

echo.
if %ERR% NEQ 0 (
    echo  Tests FAILED.
) else (
    echo  Tests PASSED.
)
pause
exit /b %ERR%
