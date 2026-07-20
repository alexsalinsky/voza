@echo off
title Add Voza to Windows Startup
echo.
echo   This will add Voza to your Windows startup folder
echo   so it launches automatically when you log in.
echo.
echo   NOTE: It will run as administrator (required for global hotkeys).
echo.
pause

:: Create a VBS launcher that runs the script as admin silently
set "SCRIPT_DIR=%~dp0"
set "VBS_FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\voza.vbs"

(
echo Set objShell = CreateObject("Shell.Application"^)
echo objShell.ShellExecute "cmd.exe", "/c cd /d ""%SCRIPT_DIR%"" && python dictation.py", "", "runas", 0
) > "%VBS_FILE%"

echo.
echo   Added to startup: %VBS_FILE%
echo.
echo   Voza will now start automatically when you log in.
echo   To remove it, delete the file at:
echo   %VBS_FILE%
echo.
pause
