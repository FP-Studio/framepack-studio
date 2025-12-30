@echo off
echo ============================================
echo FramePack-Studio Launcher
echo ============================================
echo.

REM Check if venv exists
if not exist "%cd%\venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run install_40xx_50xx.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Check if studio.py exists
if not exist "%cd%\studio.py" (
    echo Error: studio.py not found in current directory.
    echo Make sure you're running this script from the FramePack-Studio directory.
    echo.
    pause
    exit /b 1
)

echo Starting FramePack-Studio...
echo Using virtual environment at: %cd%\venv
echo.

REM Activate venv and run studio.py
call "%cd%\venv\Scripts\activate.bat"
python studio.py

REM Deactivate when done (this line is reached when studio.py exits)
deactivate

echo.
echo FramePack-Studio closed.
pause
