@echo off
title Voza -- Installer
echo.
echo   +------------------------------------------+
echo   :        Voza -- Dependency Setup            :
echo   +------------------------------------------+
echo.
echo   Installing Python dependencies...
echo.
cd /d "%~dp0"
pip install -r requirements.txt
echo.
echo   Done. Dependencies installed.
echo.
echo   NEXT STEPS:
echo   1. Create a file called .env in this folder
echo   2. Add this line:  OPENAI_API_KEY=sk-your-key-here
echo      (or skip for fully local mode)
echo   3. Run start.bat to launch Voza
echo.
pause
