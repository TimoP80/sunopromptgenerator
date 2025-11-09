@echo off
:: ============================================================================
::      AUTOMATED BUILD SCRIPT FOR SUNO PROMPT GENERATOR
:: ============================================================================
:: This script handles dependency installation, cleanup, and building the
:: executable using PyInstaller.
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
echo [STEP 4] Cleaning up old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
echo Cleanup complete.

echo.
echo [STEP 4] Building the executable with PyInstaller...
:: Using --clean to ensure a fresh build, and logging output to build.log
pyinstaller --clean --log-level=INFO SunoPromptGenerator.spec > build.log 2>&1

if %errorlevel% neq 0 (
    echo.
    echo ============================================================================
    echo ERROR: PyInstaller build failed.
    echo ============================================================================
    echo The build process encountered an error. See build.log for detailed output.
    echo.
    exit /b %errorlevel%
)

echo.
echo ============================================================================
echo      BUILD SUCCEEDED
echo ============================================================================
echo Your application is ready in the 'dist' folder.
echo.
echo Build script finished. Check build.log for details.
echo.

pause
