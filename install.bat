@echo off
setlocal enabledelayedexpansion
title AI Meeting Advisor - Installer

set INSTALL_DIR=C:\AltraMeetingAdvisor
set REPO_URL=https://github.com/LeoHsu625/altra-meeting-advisor.git

echo.
echo  ============================================
echo    AI Meeting Advisor - Installer
echo    Altra Tech Internal Use
echo  ============================================
echo.
echo  Install path: %INSTALL_DIR%
echo.
echo  Press any key to start...
pause > nul

REM ── Step 1: Check / Install Python ──────────────────────────────
echo.
echo  [1/5] Checking Python...
python --version > nul 2>&1
if %errorlevel% equ 0 (
    echo        Found ✓
    goto check_git
)

echo        Not found. Installing Python via winget...
winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo  [!] Auto-install failed. Please install manually:
    echo      https://www.python.org/downloads/
    echo      (Check "Add Python to PATH" during install)
    pause
    exit /b 1
)
echo        Python installed ✓

:check_git
REM ── Step 2: Check / Install Git ─────────────────────────────────
echo.
echo  [2/5] Checking Git...
git --version > nul 2>&1
if %errorlevel% equ 0 (
    echo        Found ✓
    goto clone_repo
)

echo        Not found. Installing Git via winget...
winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo  [!] Auto-install failed. Please install manually:
    echo      https://git-scm.com/download/win
    pause
    exit /b 1
)
echo        Git installed ✓
echo.
echo  [!] Please CLOSE this window, reopen Command Prompt, and run install.bat again.
pause
exit /b 0

:clone_repo
REM ── Step 3: Download code ───────────────────────────────────────
echo.
echo  [3/5] Downloading code...
if exist "%INSTALL_DIR%\.git" (
    echo        Existing install found, updating...
    cd /d "%INSTALL_DIR%"
    git pull origin main
) else (
    git clone %REPO_URL% "%INSTALL_DIR%"
)
if %errorlevel% neq 0 (
    echo  [!] Download failed. Please check your internet connection.
    pause
    exit /b 1
)
echo        Download complete ✓
cd /d "%INSTALL_DIR%"

REM ── Step 4: Install packages ─────────────────────────────────────
echo.
echo  [4/5] Installing packages (1-3 minutes)...
pip install -r requirements.txt -q
pip install openai -q
if %errorlevel% neq 0 (
    echo  [!] Package install failed. Please contact Leo.
    pause
    exit /b 1
)
echo        Packages installed ✓

REM ── Step 5: Configure API Keys ─────────────────────────────────────
echo.
echo  [5/5] Configuring API Keys...
if exist "%INSTALL_DIR%\.env" (
    echo        Config file found, skipping.
    echo        To change keys, edit: %INSTALL_DIR%\.env
    goto create_shortcut
)

echo.
echo  Please enter the API Keys (get from Leo):
echo.
set /p ANTHROPIC_KEY=  Anthropic API Key:
set /p OPENAI_KEY=     OpenAI API Key:

(
    echo ANTHROPIC_API_KEY=!ANTHROPIC_KEY!
    echo OPENAI_API_KEY=!OPENAI_KEY!
    echo WHISPER_BACKEND=openai
) > "%INSTALL_DIR%\.env"
echo        Keys saved ✓

:create_shortcut
REM ── Create desktop shortcut ────────────────────────────────────────
echo.
echo  Creating desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AI Meeting Advisor.lnk'); $s.TargetPath = '%INSTALL_DIR%\start.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.WindowStyle = 1; $s.Description = 'AI Meeting Advisor - Altra Tech'; $s.Save()"
echo        Shortcut created ✓

REM ── Done ────────────────────────────────────────────────────────
echo.
echo  ============================================
echo    Installation Complete!
echo  ============================================
echo.
echo  Start: double-click "AI Meeting Advisor" on Desktop
echo  Update: run %INSTALL_DIR%\update.bat
echo.
echo  Questions? Contact Leo.
echo.

set /p LAUNCH=  Launch now? (y/n):
if /i "!LAUNCH!"=="y" (
    start "" "%INSTALL_DIR%\start.bat"
)

endlocal
