@echo off
cd /d "%~dp0"

REM --- Check if Python 3 is installed ---
where python3 >nul 2>nul
if %errorlevel% neq 0 (
    echo Python 3 not found. Installing with winget...
    winget install --id Python.Python.3 --source winget --silent --accept-package-agreements --accept-source-agreements
    echo Python 3 installation complete.
)

echo Starting server...
start cmd /c python3 server.py

echo Opening browser...
start microsoft-edge:http://localhost:8000/index.html
