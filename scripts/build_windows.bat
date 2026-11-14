@echo off
setlocal
cd /d "%~dp0\.."
echo ========================================================
echo Building SecureFolder for Windows (Standalone Executable)
echo ========================================================
python -m PyInstaller --clean --noconfirm secure_folder.spec
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build SUCCESSFUL!
    echo Executable created at: dist\secure-folder-windows.exe
) else (
    echo.
    echo Build FAILED with error code %ERRORLEVEL%
)
endlocal
