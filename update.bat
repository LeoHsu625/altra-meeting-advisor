@echo off
REM AI 會議顧問 — Windows 更新腳本
REM 執行方式：雙擊此檔案，或在命令提示字元執行 update.bat

echo ======================================
echo   AI 會議顧問系統更新
echo ======================================

echo.
echo 拉取最新程式碼...
git pull origin main
if %errorlevel% neq 0 (
    echo 錯誤：git pull 失敗，請確認網路連線。
    pause
    exit /b 1
)

echo.
echo 安裝/更新套件...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo 錯誤：套件安裝失敗。
    pause
    exit /b 1
)

echo.
echo 更新完成！
echo.
echo 啟動系統請執行：
echo   uvicorn web_app:app --host 0.0.0.0 --port 8000
echo.
pause
