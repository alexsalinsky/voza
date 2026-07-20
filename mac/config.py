"""
Voza -- Voice-to-text dictation tool by Alex Salinsky
Configuration for macOS. Edit this to customize hotkeys, models, cleanup, and more.
"""

import os
import sys
from dotenv import load_dotenv

# When running as a PyInstaller app, look for .env next to the binary
if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(_APP_DIR, '.env'))

# --- Branding ---------------------------------------------------------------
APP_NAME = "Voza"
APP_AUTHOR = "Alex Salinsky"
APP_URL = "https://www.linkedin.com/in/alexsalinsky/"
APP_TAGLINE = "Voice to text, your way."

# --- OpenAI API --------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Hotkeys -----------------------------------------------------------------
# Uses pynput syntax for macOS.
# Modifier names: cmd, ctrl, shift, alt
# Examples: "cmd+shift+space", "f9", "ctrl+shift+d"
HOTKEY = "cmd+shift+space"
TOGGLE_CLEANUP_HOTKEY = "cmd+shift+c"
TOGGLE_TRANSCRIPTION_HOTKEY = "cmd+shift+t"
TOGGLE_LANGUAGE_HOTKEY = "cmd+shift+l"

# Simple mode: only the main dictation hotkey is active
SIMPLE_HOTKEYS = False

# --- Language ----------------------------------------------------------------
LANGUAGE = "auto"
LANGUAGE_CYCLE = ["auto", "en", "es"]

# --- Audio Recording ---------------------------------------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_TIMEOUT = 0        # 0 = disabled, manual stop only
SILENCE_THRESHOLD = 0.01
MAX_RECORDING_SECS = 600
NORMALIZE_AUDIO = True     # Boost audio to consistent level before transcribing
NORMALIZE_MAX_GAIN = 10.0  # Max amplification (10x). Helps when mic is shared with other apps

# --- Transcription -----------------------------------------------------------
TRANSCRIPTION_MODE = "api" if OPENAI_API_KEY else "local"
API_FALLBACK_TO_LOCAL = True
API_TIMEOUT_SECS = 10
WHISPER_MODEL = "whisper-1"
WHISPER_PROMPT = "Voza is a dictation app."
LOCAL_WHISPER_MODEL = "base"

# --- Cleanup / Correction ----------------------------------------------------
STRIP_FILLERS = True
ENABLE_CLEANUP = False
CLEANUP_MODEL = "gpt-4o-mini"

CLEANUP_SYSTEM_PROMPT = """You are a dictation cleanup assistant. You receive raw speech-to-text output and return a corrected version.

Rules:
- Fix punctuation and capitalization
- Fix obvious transcription errors and misheard words
- Remove filler words (um, uh, like, you know) ONLY when they are clearly speech artifacts, not intentional
- Remove false starts and repeated words that are clearly stumbles
- Preserve the speaker's original wording, tone, and meaning as closely as possible
- Do NOT rephrase, summarize, or make the text "sound better"
- Do NOT add words or ideas that were not spoken
- Do NOT change informal language to formal language
- If the input is already clean, return it unchanged
- Return ONLY the corrected text with no commentary, no quotes, no explanation"""

# --- Text Insertion ----------------------------------------------------------
INSERTION_METHOD = "clipboard"
INSERTION_DELAY = 0.05

# --- Audio Feedback ----------------------------------------------------------
MUTE_DURING_RECORDING = True
ENABLE_SOUNDS = True
# (frequency_hz, duration_ms) -- generated as tones via sounddevice on Mac
SOUND_START = (900, 200)
SOUND_STOP = (300, 400)
SOUND_ERROR = (200, 500)

# --- Debug -------------------------------------------------------------------
DEBUG = os.getenv("VOZA_DEBUG", "").lower() in ("1", "true", "yes")
