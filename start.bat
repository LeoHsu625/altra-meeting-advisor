@echo off
title AI Meeting Advisor
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ======================================
echo   AI Meeting Advisor
echo ======================================
echo.
echo Starting... browser will open automatically.
echo Close this window to stop the system.
echo.

REM Kill any previous instance on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /F /PID %%a > nul 2>&1
)

start /b uvicorn web_app:app --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak > nul
start http://localhost:8000

echo System running. Do not close this window.
echo.
pause
