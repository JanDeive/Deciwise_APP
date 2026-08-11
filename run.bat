@echo off
echo =============================================
echo   DeciWise - Family Planning Quiz Game
echo   Capstone Edition
echo =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check pygame
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [INFO] pygame not found. Installing now...
    pip install pygame==2.6.1
    if errorlevel 1 (
        echo [ERROR] Failed to install pygame.
        echo Try manually: pip install pygame==2.6.1
        pause
        exit /b 1
    )
    echo [OK] pygame installed.
)

echo [OK] All dependencies satisfied.
echo Starting game...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] The game exited with an error. See message above.
    pause
)
