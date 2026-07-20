@echo off
title Voza -- Build for Sharing
echo.
echo   +----------------------------------------------+
echo   :  Voza -- Build for Sharing                    :
echo   +----------------------------------------------+
echo.
echo   This will create a "voza-share" folder that you
echo   can zip up and send to anyone. They just double-
echo   click voza.exe -- no Python needed on their end.
echo.
echo   Prerequisites: PyInstaller (will install if missing)
echo.
echo   Press any key to start, or close this window to cancel.
pause >nul
echo.

cd /d "%~dp0"

:: Make sure PyInstaller is installed
echo   Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing PyInstaller...
    pip install pyinstaller
    echo.
)

:: Run the build
python build_exe.py

echo.
pause
