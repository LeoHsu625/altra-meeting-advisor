@echo off
REM AI 會議顧問 — Windows 啟動腳本
REM 執行方式：雙擊此檔案

echo ======================================
echo   AI 即時會議顧問系統
echo ======================================
echo.
echo 系統啟動中，請稍候...
echo 啟動後請用瀏覽器開啟：http://localhost:8000
echo.
echo 關閉此視窗 = 關閉系統
echo ======================================
echo.

uvicorn web_app:app --host 0.0.0.0 --port 8000

pause
