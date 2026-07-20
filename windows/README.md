# Voza

**Voice to text, your way.** By [Alex Salinsky](https://github.com/alexsalinsky/voza).

A free, open-source voice dictation tool for Windows. Press a hotkey, speak naturally, and corrected text appears at your cursor — in any app.

Powered by Whisper on Groq (~200x realtime) or OpenAI, with a fully free local mode available.

## How it works

```
Ctrl+Shift+Space → speak → Ctrl+Shift+Space → text appears at cursor
```

That's it. Works in any text field on Windows — Slack, email, browser, Notepad, VS Code, anything.

## Features

- **Global hotkey** to start/stop dictation from any app
- **Smart spacing** — automatically inserts a space when a dictation continues a previous one shortly after
- **Custom vocabulary** — add names or jargon in the panel so Whisper hears them correctly (saved to `custom_vocab.json`)
- **Near-perfect transcription** via OpenAI Whisper
- **Optional AI cleanup** fixes punctuation, grammar, and speech artifacts (toggle on/off)
- **Background chunking** for long dictations — transcribes while you speak, so results appear fast even after 5+ minutes of talking
- **Multi-language** — cycle between auto-detect, English, and Spanish with a hotkey
- **Fully local mode** — run everything on your machine for $0 cost
- **Auto-fallback** — if the API is unreachable, automatically falls back to local transcription
- **System tray icon** — changes color to show state (idle/recording/processing)
- **Interactive settings window** — click the tray icon to toggle settings, change hotkeys, view session stats
- **Audio feedback** — distinct sounds for start, stop, and toggles so you always know the state
- **Simple hotkey mode** — disable all hotkeys except the main dictation key if you prefer minimal shortcuts

## Cost

| Mode | Monthly cost (30 min/day) |
|------|--------------------------|
| Groq transcription + AI cleanup | **~$0.35** |
| OpenAI transcription + AI cleanup | ~$2.10 |
| OpenAI transcription, no cleanup | ~$1.80 |
| Local transcription + AI cleanup | ~$0.30 |
| Fully local (no API at all) | **$0.00** |

Groq is the recommended cloud mode: `whisper-large-v3-turbo` transcribes at ~200x realtime (a 30-second dictation returns in well under a second) and costs about $0.04 per hour of audio. When a `GROQ_API_KEY` is present, Voza uses it automatically for both transcription and cleanup.

## Quick start

### Prerequisites

- Windows 10 or 11
- Python 3.10+ ([download](https://www.python.org/downloads/))
- A microphone
- A Groq API key ([get one here](https://console.groq.com/keys)) or OpenAI API key ([here](https://platform.openai.com/api-keys)) — optional if using fully local mode

### Install

Double-click `setup-voza.bat` — it installs dependencies, adds Voza to your Start Menu, sets it to auto-start on login, and creates a desktop shortcut.

Or install manually:

```bash
cd voza
pip install -r requirements.txt
python generate_icons.py
```

### Configure

Copy `.env.example` to `.env` and add your API key:

```
GROQ_API_KEY=gsk_your-key-here
```

(Or `OPENAI_API_KEY=sk-proj-...` — Groq is preferred when both are present.)

Or skip this step entirely to run in fully local mode (free).

### Run

**Important: Run as administrator** (required for global hotkeys).

```bash
python dictation.py
```

Or right-click `start.bat` → Run as administrator.

## Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+Space` | Start / stop dictation |
| `Ctrl+Shift+C` | Toggle AI cleanup on/off |
| `Ctrl+Shift+T` | Toggle API / local transcription |
| `Ctrl+Shift+L` | Cycle language (auto → English → Spanish) |

All hotkeys are customizable from the settings window (click the tray icon) or in `config.py`.

Enable "Simple Hotkeys" mode to only use the main dictation key — all other toggles are available from the settings window.

## Configuration

Everything is in `config.py`. Key settings:

**Change the hotkey:**
```python
HOTKEY = "ctrl+shift+space"  # default
```

**Enable AI cleanup by default:**
```python
ENABLE_CLEANUP = True
```

**Use local transcription by default (free):**
```python
TRANSCRIPTION_MODE = "local"
LOCAL_WHISPER_MODEL = "base"  # or "small", "medium" for better quality
```

**Change the cleanup behavior:**
Edit `CLEANUP_SYSTEM_PROMPT` — tell it to be more aggressive, more hands-off, or anything in between.

**Silence auto-stop:**
```python
SILENCE_TIMEOUT = 4.0  # seconds of silence before auto-stop (0 = disabled)
```

**Add more languages:**
```python
LANGUAGE_CYCLE = ["auto", "en", "es", "fr", "de", "pt"]
```

## How the background chunking works

For short dictations (under 25 seconds), audio is transcribed in one shot after you stop — fast and simple.

For longer dictations, the tool sends audio chunks to Whisper every 25 seconds while you're still talking. By the time you stop, most of your speech is already transcribed. A quick stitching pass merges the chunks and removes overlapping text. This means a 5-minute dictation finishes processing in about 1 second instead of 10+.

## Troubleshooting

**Hotkey not working:** Run as administrator. The `keyboard` library needs elevated privileges for global hotkeys on Windows.

**No microphone found:** Check Windows Settings → Sound → Input. Make sure a mic is set as default.

**Text not appearing:** Some admin-elevated apps block simulated input. Try `INSERTION_METHOD = "typewrite"` in config.py, or run Voza as admin too.

**Transcription is slow:** Check your internet connection. Or switch to local mode (`Ctrl+Shift+T`) to avoid network latency.

**Wrong language:** Press `Ctrl+Shift+L` to force a specific language instead of auto-detect.

## Building the standalone .exe

To create a single executable that doesn't require Python:

```bash
pip install pyinstaller
python build_exe.py
```

The `.exe` will be in the `dist/` folder. Users still need to create a `.env` file with their API key next to the `.exe` (or skip it for local-only mode).

## File overview

```
voza/
├── dictation.py           ← Main engine
├── config.py              ← All settings
├── generate_icons.py      ← Creates tray icons (run once)
├── .env                   ← Your API key (create from .env.example)
├── .env.example           ← Template
├── requirements.txt       ← Python dependencies
├── setup-app.bat          ← Full setup (install + Start Menu + startup + desktop shortcut)
├── start.bat              ← Quick launcher
├── start-debug.bat        ← Launcher with debug output
├── build_exe.py           ← PyInstaller build script
└── README.md              ← This file
```

## Credits

Built by Alex Salinsky with Claude (Anthropic). Uses Whisper via Groq or OpenAI, with local fallback via faster-whisper.

## License

MIT — do whatever you want with it.
