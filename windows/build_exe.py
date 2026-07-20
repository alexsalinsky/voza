"""
Voza -- Build a share-ready package.

Creates a 'voza-share' folder containing:
  - voza.exe          (standalone, no Python needed -- icons, config, and usage tracking are built in)
  - README.txt        (simple instructions for non-techy users)

Usage:
    python build_exe.py
"""

import subprocess
import sys
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARE_DIR = os.path.join(SCRIPT_DIR, "voza-share")


def ensure_icons():
    """Generate tray icons if they don't exist yet."""
    icons = ["icon_idle.ico", "icon_recording.ico", "icon_processing.ico"]
    missing = [i for i in icons if not os.path.exists(os.path.join(SCRIPT_DIR, i))]
    if missing:
        print("  Generating tray icons...")
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "generate_icons.py")],
            cwd=SCRIPT_DIR,
        )
        if result.returncode != 0:
            print("  Warning: could not generate icons. Continuing anyway.")


def build_exe():
    """Run PyInstaller to create the standalone exe."""
    print("  Building voza.exe with PyInstaller...")
    print()

    # Use icon_idle.ico as the exe icon if it exists
    ico_path = os.path.join(SCRIPT_DIR, "icon_idle.ico")
    icon_flag = ico_path if os.path.exists(ico_path) else "NONE"

    # UAC manifest — makes the exe auto-request admin (needed for global hotkeys)
    manifest_path = os.path.join(SCRIPT_DIR, "voza.manifest")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "voza",
        "--console",
        "--icon", icon_flag,
        # Embed UAC manifest for auto-elevation
        "--manifest", manifest_path,
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "pystray",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "pycaw",
        "--hidden-import", "pycaw.pycaw",
        "--hidden-import", "comtypes",
        "--hidden-import", "faster_whisper",
        "--hidden-import", "ctranslate2",
        "--hidden-import", "huggingface_hub",
        "--hidden-import", "dotenv",
        "--hidden-import", "winsound",
        "--hidden-import", "usage",
        "dictation.py",
    ]

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    return result.returncode == 0


def assemble_share_folder():
    """Copy everything needed into the share folder."""
    print()
    print("  Assembling share folder...")

    # Clean and create share dir
    if os.path.exists(SHARE_DIR):
        shutil.rmtree(SHARE_DIR)
    os.makedirs(SHARE_DIR)

    # Copy the exe
    exe_src = os.path.join(SCRIPT_DIR, "dist", "voza.exe")
    if not os.path.exists(exe_src):
        print(f"  Error: {exe_src} not found. Build may have failed.")
        return False
    shutil.copy2(exe_src, SHARE_DIR)

    # That's it — the exe is self-contained.
    # Icons are generated in memory, usage.py is bundled,
    # config defaults are built-in, .env is created by the app when needed.

    # Create the simple README
    readme_path = os.path.join(SHARE_DIR, "README.txt")
    with open(readme_path, "w") as f:
        f.write(README_TEXT)

    return True


README_TEXT = """\
VOZA -- Voice to text, your way.
By Alex Salinsky

================================
HOW TO USE
================================

1. Double-click voza.exe (say Yes to the admin prompt)
2. Look for the microphone icon in your system tray (bottom-right of your screen)
3. Press Ctrl+Shift+Space to start talking
4. Press Ctrl+Shift+Space again to stop
5. Your words appear wherever your cursor is -- any app, any text field

That's it! Voza runs in fully local mode by default -- free, private,
nothing leaves your computer.


================================
WANT BETTER ACCURACY? (optional)
================================

You can connect to a cloud service for faster, higher-quality transcription.
Recommended: Groq (about $0.35/month for typical use).

To set it up:
1. Go to: https://console.groq.com/keys
2. Create a free account and get an API key
3. In this folder, create a file named ".env" using Notepad
4. Put this single line in it (with your real key):
   GROQ_API_KEY=gsk_your-key-here
5. Restart voza.exe
6. Click the tray icon and toggle "Transcription" to "API (cloud)"

(OpenAI also works: get a key at platform.openai.com/api-keys and use
OPENAI_API_KEY=sk-... instead.)


================================
SETTINGS
================================

Click the microphone icon in your system tray to open settings.
From there you can:
  - Switch between local (free) and cloud transcription
  - Turn AI text cleanup on/off
  - Change the language (English, Spanish, or auto-detect)
  - Mute your speakers while recording
  - Add custom vocabulary (names, jargon)
  - Change hotkeys

Everything is configurable from that window -- no files to edit.


================================
TIPS
================================

- Voza needs admin rights to capture the global hotkey.
  Always say "Yes" when Windows asks for permission.
- If you don't hear a beep when you press the hotkey,
  try right-clicking voza.exe and choosing "Run as administrator".
- The first time you use local mode, it downloads a small AI model
  (~150 MB). This only happens once.


Source code + updates: https://github.com/alexsalinsky/voza
Learn more: https://www.linkedin.com/in/alexsalinsky/
"""


def build():
    print()
    print("  +----------------------------------------------+")
    print("  :  Voza -- Building share-ready package         :")
    print("  +----------------------------------------------+")
    print()

    # Step 1: Make sure icons exist
    ensure_icons()

    # Step 2: Build the exe
    success = build_exe()
    if not success:
        print()
        print("  Build failed. Check the errors above.")
        print("  Make sure PyInstaller is installed: pip install pyinstaller")
        sys.exit(1)

    # Step 3: Assemble the share folder
    success = assemble_share_folder()
    if not success:
        sys.exit(1)

    # Done
    print()
    print("  +----------------------------------------------+")
    print("  :  Done! Ready to share.                        :")
    print("  +----------------------------------------------+")
    print()
    print(f"  Your share-ready folder: {SHARE_DIR}")
    print()
    print("  It contains:")
    for f in sorted(os.listdir(SHARE_DIR)):
        size = os.path.getsize(os.path.join(SHARE_DIR, f))
        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.0f} KB"
        else:
            size_str = f"{size} B"
        print(f"    {f:30s} {size_str}")
    print()
    print("  To share:")
    print("    - Zip the 'voza-share' folder and send it")
    print("    - Or just send the whole folder as-is")
    print()
    print("  Your friend just double-clicks voza.exe. That's it.")
    print()


if __name__ == "__main__":
    build()
