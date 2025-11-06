@echo off

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the GUI builder script
python gui_builder.py
