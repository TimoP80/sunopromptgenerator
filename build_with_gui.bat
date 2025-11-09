@echo off
:: ============================================================================
::      AUTOMATED BUILD SCRIPT (WITH GUI) FOR SUNO PROMPT GENERATOR
:: ============================================================================
:: This script handles dependency installation, cleanup, and building the
:: executable using a GUI-based PyInstaller wrapper.
:: ============================================================================

:: 1. Request Administrator Privileges
:: This is important for file permissions, especially when dealing with PyInstaller.
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

:: ============================================================================
::      BUILD PROCESS
:: ============================================================================

echo.
echo [STEP 1] Terminating running application instances...
taskkill /F /IM SunoPromptGenerator.exe 2>nul || echo No running instances found.
echo Waiting for process to terminate...
timeout /t 2 /nobreak >nul

echo.
echo [STEP 2] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using global Python installation.
)

echo.
echo [STEP 3] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies. Check build.log for details.
    exit /b %errorlevel%
)
echo Dependencies installed successfully.

echo.
echo [STEP 5] Cleaning up old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
echo Cleanup complete.

echo.
echo [STEP 6] Launching the GUI builder...
python gui_builder.py

echo.
echo ============================================================================
echo      BUILD PROCESS INITIATED
echo ============================================================================
echo The GUI builder has been launched. Follow the on-screen instructions.
echo.

pause
