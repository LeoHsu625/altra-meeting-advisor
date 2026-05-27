@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title AI 即時會議顧問 — 安裝程式

set INSTALL_DIR=C:\AltraMeetingAdvisor
set REPO_URL=https://github.com/LeoHsu625/altra-meeting-advisor.git

echo.
echo  ============================================
echo    AI 即時會議顧問系統 — 安裝程式
echo    Altra Tech 内部使用
echo  ============================================
echo.
echo  安裝位置：%INSTALL_DIR%
echo.
echo  按任意鍵開始安裝...
pause > nul

REM ── 步驟 1：檢查 / 安裝 Python ──────────────────────────────
echo.
echo  [1/5] 檢查 Python...
python --version > nul 2>&1
if %errorlevel% equ 0 (
    echo        已安裝 ✓
    goto check_git
)

echo        未安裝，正在透過 winget 安裝 Python...
winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo  [!] 自動安裝失敗。請手動安裝後重新執行此程式：
    echo      https://www.python.org/downloads/
    echo      （安裝時請勾選 "Add Python to PATH"）
    pause
    exit /b 1
)
echo        Python 安裝完成 ✓

:check_git
REM ── 步驟 2：檢查 / 安裝 Git ─────────────────────────────────
echo.
echo  [2/5] 檢查 Git...
git --version > nul 2>&1
if %errorlevel% equ 0 (
    echo        已安裝 ✓
    goto clone_repo
)

echo        未安裝，正在透過 winget 安裝 Git...
winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo  [!] 自動安裝失敗。請手動安裝後重新執行此程式：
    echo      https://git-scm.com/download/win
    pause
    exit /b 1
)
echo        Git 安裝完成 ✓
echo.
echo  [!] 請關閉此視窗，重新開啟命令提示字元，再執行一次 install.bat
pause
exit /b 0

:clone_repo
REM ── 步驟 3：下載程式碼 ───────────────────────────────────────
echo.
echo  [3/5] 下載程式碼...
if exist "%INSTALL_DIR%\.git" (
    echo        偵測到已安裝舊版本，執行更新...
    cd /d "%INSTALL_DIR%"
    git pull origin main
) else (
    git clone %REPO_URL% "%INSTALL_DIR%"
)
if %errorlevel% neq 0 (
    echo  [!] 下載失敗，請確認網路連線後重試。
    pause
    exit /b 1
)
echo        下載完成 ✓
cd /d "%INSTALL_DIR%"

REM ── 步驟 4：安裝套件 ─────────────────────────────────────────
echo.
echo  [4/5] 安裝套件（約需 1-3 分鐘）...
pip install -r requirements.txt -q
pip install openai -q
if %errorlevel% neq 0 (
    echo  [!] 套件安裝失敗，請截圖錯誤訊息並聯絡 Leo。
    pause
    exit /b 1
)
echo        套件安裝完成 ✓

REM ── 步驟 5：設定 API Key ─────────────────────────────────────
echo.
echo  [5/5] 設定 API Key...
if exist "%INSTALL_DIR%\.env" (
    echo        已有設定檔，略過。
    echo        如需修改請編輯：%INSTALL_DIR%\.env
    goto create_shortcut
)

echo.
echo  請向 Leo 取得以下兩組 API Key 後輸入：
echo.
set /p ANTHROPIC_KEY=  Anthropic API Key:
set /p OPENAI_KEY=     OpenAI API Key:

(
    echo ANTHROPIC_API_KEY=!ANTHROPIC_KEY!
    echo OPENAI_API_KEY=!OPENAI_KEY!
    echo WHISPER_BACKEND=openai
) > "%INSTALL_DIR%\.env"
echo        設定完成 ✓

:create_shortcut
REM ── 建立桌面捷徑 ────────────────────────────────────────────
echo.
echo  建立桌面捷徑...
powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AI 即時會議顧問.lnk');" ^
    "$s.TargetPath = '%INSTALL_DIR%\start.bat';" ^
    "$s.WorkingDirectory = '%INSTALL_DIR%';" ^
    "$s.WindowStyle = 1;" ^
    "$s.Description = 'AI 即時會議顧問系統 — Altra Tech';" ^
    "$s.Save()"
echo        桌面捷徑建立完成 ✓

REM ── 完成 ────────────────────────────────────────────────────
echo.
echo  ============================================
echo    安裝完成！
echo  ============================================
echo.
echo  開始使用：雙擊桌面上的「AI 即時會議顧問」
echo  更新程式：雙擊 %INSTALL_DIR%\update.bat
echo.
echo  有問題請聯絡 Leo。
echo.

set /p LAUNCH=  現在立即啟動系統？(y/n):
if /i "!LAUNCH!"=="y" (
    start "" "%INSTALL_DIR%\start.bat"
)

endlocal
