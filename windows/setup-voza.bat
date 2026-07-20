@echo off
title Setup Voza
echo.
echo   +------------------------------------------------------+
echo   :  Setup Voza -- Global Voice to Text                   :
echo   :  by Alex Salinsky                                     :
echo   +------------------------------------------------------+
echo.
echo   This will:
echo     1. Install all dependencies
echo     2. Add Voza to your Start Menu
echo     3. Add it to Windows startup (runs automatically on login)
echo     4. Create a desktop shortcut
echo.
echo   Press any key to continue, or close this window to cancel.
pause >nul

set "SCRIPT_DIR=%~dp0"

:: --- Step 1: Install dependencies ---
echo.
echo   [1/4] Installing dependencies...
cd /d "%SCRIPT_DIR%"
pip install -r requirements.txt
echo   Done.
echo.

:: --- Step 2: Create a VBS launcher (runs as admin, no visible cmd flash) ---
echo   [2/4] Creating launcher...
set "VBS_LAUNCHER=%SCRIPT_DIR%voza-launcher.vbs"
(
echo Set objShell = CreateObject^("Shell.Application"^)
echo objShell.ShellExecute "cmd.exe", "/c cd /d ""%SCRIPT_DIR%"" && python dictation.py", "", "runas", 0
) > "%VBS_LAUNCHER%"
echo   Done.

:: --- Step 3: Add to Start Menu ---
echo   [3/4] Adding to Start Menu and startup...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: Create Start Menu shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\Voza.lnk'); $s.TargetPath = '%VBS_LAUNCHER%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'Global voice to text by Alex Salinsky'; $s.Save()"
echo   Added to Start Menu (search "Voza")

:: Create Startup shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP%\Voza.lnk'); $s.TargetPath = '%VBS_LAUNCHER%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'Global voice to text by Alex Salinsky'; $s.Save()"
echo   Added to Windows startup (launches on login)

:: --- Step 4: Desktop shortcut ---
echo   [4/4] Creating desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\Voza.lnk'); $s.TargetPath = '%VBS_LAUNCHER%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'Global voice to text by Alex Salinsky'; $s.Save()"
echo   Done.

:: --- Done ---
echo.
echo   +------------------------------------------------------+
echo   :  Setup complete!                                      :
echo   +------------------------------------------------------+
echo.
echo   You can now:
echo     - Search "Voza" in the Start Menu
echo     - Double-click the desktop shortcut
echo     - It will auto-start next time you log in
echo.
echo   How to use:
echo     Press Ctrl+Shift+Space to start dictating
echo     Press Ctrl+Shift+Space again to stop
echo     Text appears wherever your cursor is
echo.
echo   To uninstall:
echo     - Delete the desktop shortcut
echo     - Delete "Voza" from Start Menu
echo     - Delete "Voza" from:
echo       %STARTUP%
echo.
echo   Launching Voza now...
echo.
start "" "%VBS_LAUNCHER%"
