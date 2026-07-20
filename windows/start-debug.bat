@echo off
title Voza (DEBUG)
echo.
echo   Starting Voza in DEBUG mode...
echo.
cd /d "%~dp0"
set VOZA_DEBUG=1
python dictation.py
pause
