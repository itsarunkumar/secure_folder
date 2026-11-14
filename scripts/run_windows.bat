@echo off
setlocal
cd /d "%~dp0\.."
python -m secure_folder.main %*
endlocal
