@echo off
echo ============================================
echo Activating FramePack-Studio Virtual Environment
echo ============================================
echo.

REM Check if venv exists
if not exist "%cd%\venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run install_40xx_50xx.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

echo Virtual environment activated.
echo You can now run Python commands within this environment.
echo.
echo To deactivate, type: deactivate
echo To run FramePack-Studio, type: python studio.py
echo.

REM Activate and keep command prompt open
cmd /k "%cd%\venv\Scripts\activate.bat"
