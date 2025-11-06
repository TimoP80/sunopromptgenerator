@echo off

echo =========================================
echo      AUTOMATED BUILD SCRIPT
echo =========================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Assuming required packages are installed globally.
)

echo.
echo STEP 1: Cleaning up old build artifacts...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo Cleanup complete.

echo.
echo STEP 2: Building the executable...
REM This clears the cache (--clean) and uses the spec file.
pyinstaller --clean --log-level=DEBUG SunoPromptGenerator.spec

REM Check if the build was successful before continuing
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller build failed.
    pause
    exit /b %errorlevel%
)

echo Build complete.

echo.
echo STEP 3: Copying required files (ffmpeg, ffprobe)...
if exist "dist\SunoPromptGenerator" (
    copy /Y ffmpeg.exe "dist\SunoPromptGenerator\"
    copy /Y ffprobe.exe "dist\SunoPromptGenerator\"
    echo Files copied successfully.
) else (
    echo ERROR: The directory 'dist\SunoPromptGenerator' was not found. Cannot copy files.
    pause
    exit /b 1
)

echo.
echo =========================================
echo      BUILD SUCCEEDED
echo =========================================
echo.
echo Your application is ready in the 'dist\SunoPromptGenerator' folder.

echo.
pause
