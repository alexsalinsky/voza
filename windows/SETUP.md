# Voza — Setup Guide

A Windows voice dictation tool by Alex Salinsky. Press a hotkey, speak naturally, and corrected text appears at your cursor — in any app. Powered by Whisper on Groq or OpenAI, with a fully free local mode.

---

## Quick Setup (Recommended)

1. Double-click **`setup-voza.bat`** — this installs dependencies, adds Voza to your Start Menu, sets auto-start, and creates a desktop shortcut.
2. (Optional) Create a `.env` file with your Groq or OpenAI API key for cloud features. Or skip this to use fully local mode (free).
3. Run `python generate_icons.py` once to create the tray icons.
4. Search "Voza" in the Start Menu, or double-click the desktop shortcut.

---

## Manual Setup

### Prerequisites

- **Windows 10/11**
- **Python 3.10+**
- **A working microphone**
- **Groq or OpenAI API key** (optional — only needed for cloud transcription and AI cleanup)

### Step 1: Install Dependencies

```bash
cd voza
pip install -r requirements.txt
```

### Step 2: Generate Tray Icons

```bash
python generate_icons.py
```

### Step 3: Configure (Optional)

Copy `.env.example` to `.env` and add your API key (Groq recommended):
```
GROQ_API_KEY=gsk_your-actual-key
```

Skip this step to run in fully local mode (free, no API key needed).

### Step 4: Run It

**Run as administrator** (required for global hotkeys):

```bash
python dictation.py
```

Or right-click `start.bat` → Run as administrator.

---

## Usage

1. Press **Ctrl+Shift+Space** — you'll hear a beep (recording starts)
2. Speak naturally
3. Press **Ctrl+Shift+Space** again — text appears at your cursor

Click the system tray icon to access settings, change hotkeys, toggle features, and view session stats.

See `README.md` for full feature documentation, hotkey reference, configuration options, and troubleshooting.
