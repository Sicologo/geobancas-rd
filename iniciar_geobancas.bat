@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python no esta instalado. Descargalo desde python.org y marca Add Python to PATH.
  pause
  exit /b 1
)
python -m pip install flask pandas openpyxl --quiet
start "" http://127.0.0.1:8765
python server.py
pause
