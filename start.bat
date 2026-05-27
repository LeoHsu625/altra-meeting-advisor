@echo off
chcp 65001 > nul
title AI 即時會議顧問

echo ======================================
echo   AI 即時會議顧問系統
echo ======================================
echo.
echo 系統啟動中，瀏覽器將自動開啟...
echo 關閉此視窗 = 關閉系統
echo.

start /b uvicorn web_app:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak > nul
start http://localhost:8000

echo 系統運作中，請勿關閉此視窗。
echo.
pause
