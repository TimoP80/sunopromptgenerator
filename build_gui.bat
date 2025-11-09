@echo off
:: ============================================================================
::      LAUNCH SCRIPT FOR AI MUSIC STUDIO BUILDER GUI
:: ============================================================================
:: This script activates the virtual environment and starts the graphical
:: build tool (gui_builder.py).
:: ============================================================================

:: 1. Request Administrator Privileges
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

:: 2. Activate Virtual Environment
echo.
echo [STEP 1] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo WARNING: Virtual environment not found. Using global Python installation.
)

:: 3. Launch the GUI Builder
echo.
echo [STEP 2] Launching the GUI build tool...
python gui_builder.py

echo.
echo Script finished.
pause