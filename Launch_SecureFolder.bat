@echo off
title SecureFolder
cd /d "%~dp0"
echo Starting SecureFolder...
python launch_ui.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Make sure Python and pywebview are installed.
    echo Run: pip install pywebview
    pause
)
