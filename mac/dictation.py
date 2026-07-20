#!/usr/bin/env python3
"""
Voza -- Voice to text, your way.
By Alex Salinsky

macOS version.

Press a hotkey -> speak -> press again -> corrected text appears at your cursor.

Run:  python3 dictation.py
Stop: Click tray icon -> Quit (or Ctrl+C in terminal)
"""

import io
import os
import sys
import time
import threading
import tempfile
import wave
import concurrent.futures
import subprocess

import numpy as np
import sounddevice as sd
import pyperclip
from pynput import keyboard as pynput_keyboard
from openai import OpenAI

import config

# --- Globals -----------------------------------------------------------------
recording = False
audio_frames = []
stream = None
lock = threading.Lock()
client = None
tray_icon = None

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Background chunking state
chunk_results = []
chunk_executor = None
chunk_frame_index = 0

# Local whisper model (loaded lazily)
local_whisper_model = None

# Session stats
session_stats = {"dictations": 0, "total_seconds": 0, "start_time": None}

# Hotkey listener reference
_hotkey_listener = None

# Status window singleton
_status_window = None
_status_window_lock = threading.Lock()


def log(msg):
    """Print only when DEBUG is enabled."""
    if config.DEBUG:
        print(f"  [DEBUG] {msg}")


# --- Audio Feedback (Mac: generate tones via sounddevice) --------------------
def _play_tone(frequency, duration_ms):
    """Play a single tone using sounddevice (cross-platform)."""
    try:
        sr = 44100
        t = np.linspace(0, duration_ms / 1000, int(sr * duration_ms / 1000), False)
        tone = 0.3 * np.sin(2 * np.pi * frequency * t)
        # Fade in/out to avoid clicks
        fade = min(len(tone) // 10, 200)
        tone[:fade] *= np.linspace(0, 1, fade)
        tone[-fade:] *= np.linspace(1, 0, fade)
        sd.play(tone.astype(np.float32), sr, blocking=True)
    except Exception:
        pass


def _play_beeps(sequence):
    """Play a sequence of (freq, duration_ms) beeps. Blocks until done."""
    for freq, dur in sequence:
        _play_tone(freq, dur)


def beep(*sequence):
    """Play beep(s) without blocking."""
    if not config.ENABLE_SOUNDS:
        return
    threading.Thread(target=_play_beeps, args=(sequence,), daemon=True).start()


# --- System Tray Icon --------------------------------------------------------
def _load_icon(name):
    """Load an .ico or .png file from the script directory."""
    try:
        from PIL import Image
        # Try .png first (more natural on Mac), then .ico
        for ext in [".png", ".ico"]:
            path = os.path.join(SCRIPT_DIR, name.replace(".ico", ext))
            if os.path.exists(path):
                return Image.open(path)
        # Try original name as-is
        path = os.path.join(SCRIPT_DIR, name)
        if os.path.exists(path):
            return Image.open(path)
    except Exception:
        pass
    return None


_icon_idle = None
_icon_recording = None
_icon_processing = None


def _init_icons():
    """Load all tray icons."""
    global _icon_idle, _icon_recording, _icon_processing
    _icon_idle = _load_icon("icon_idle.ico")
    _icon_recording = _load_icon("icon_recording.ico")
    _icon_processing = _load_icon("icon_processing.ico")

    # If no icon files found, create simple colored circles
    if _icon_idle is None:
        _icon_idle = _make_circle_icon((100, 100, 100))
    if _icon_recording is None:
        _icon_recording = _make_circle_icon((220, 50, 50))
    if _icon_processing is None:
        _icon_processing = _make_circle_icon((50, 130, 220))


def _make_circle_icon(color, size=64):
    """Create a simple colored circle icon using Pillow."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 4, size - 4], fill=color)
        return img
    except Exception:
        return None


def set_tray_state(state):
    """Update the tray icon to reflect current state."""
    if tray_icon is None:
        return
    try:
        icons = {"idle": _icon_idle, "recording": _icon_recording, "processing": _icon_processing}
        tooltips = {
            "idle": f"{config.APP_NAME} -- Ready",
            "recording": f"{config.APP_NAME} -- Recording...",
            "processing": f"{config.APP_NAME} -- Processing...",
        }
        icon = icons.get(state, _icon_idle)
        if icon:
            tray_icon.icon = icon
            tray_icon.title = tooltips.get(state, config.APP_NAME)
    except Exception:
        pass


def _quit_app(icon, item):
    """Quit from the tray menu."""
    global recording
    if recording:
        stop_recording()
    icon.stop()
    os._exit(0)


def _show_status_window(icon=None, item=None):
    """Show a small status popup (singleton -- reuses existing window)."""
    global _status_window
    with _status_window_lock:
        if _status_window is not None:
            try:
                _status_window.lift()
                _status_window.focus_force()
                return
            except Exception:
                _status_window = None
    threading.Thread(target=_build_status_window, daemon=True).start()


def _show_api_key_help(parent=None):
    """Show a popup explaining how to set up an OpenAI API key."""
    try:
        import tkinter.messagebox as mb
        mb.showinfo(
            "Cloud features need an API key",
            "To use cloud transcription or AI cleanup, you need an OpenAI API key.\n\n"
            "How to set it up:\n\n"
            "1. Go to: platform.openai.com/api-keys\n"
            "2. Create a new secret key\n"
            "3. Create a file called .env next to the app\n"
            "4. Add this line:\n"
            "   OPENAI_API_KEY=sk-your-key-here\n"
            "5. Restart Voza\n\n"
            "Without a key, Voza works great in local mode (free).",
            parent=parent,
        )
    except Exception:
        pass


def _build_status_window():
    """Build and display an interactive status window using tkinter."""
    global _status_window
    try:
        import tkinter as tk
        from tkinter import simpledialog

        win = tk.Tk()
        _status_window = win

        def on_close():
            global _status_window
            _status_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.title(config.APP_NAME)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(bg="#1e1e1e")

        # Center on screen
        w, h = 360, 580
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        # Styles
        title_font = ("Helvetica", 18, "bold")
        subtitle_font = ("Helvetica", 9)
        header_font = ("Helvetica", 10, "bold")
        label_font = ("Helvetica", 10)
        btn_font = ("Helvetica", 9)
        link_font = ("Helvetica", 8, "underline")
        fg = "#e0e0e0"
        fg_dim = "#888888"
        fg_accent = "#6cb6ff"
        fg_on = "#44cc88"
        fg_off = "#cc4444"
        bg = "#1e1e1e"
        bg_section = "#2a2a2a"
        bg_btn = "#3a3a3a"
        bg_btn_hover = "#4a4a4a"

        # --- Title & branding ---
        tk.Label(win, text=config.APP_NAME, font=title_font, fg=fg, bg=bg).pack(pady=(15, 0))
        tk.Label(win, text=config.APP_TAGLINE, font=subtitle_font, fg=fg_dim, bg=bg).pack(pady=(0, 2))
        author_label = tk.Label(win, text=f"by {config.APP_AUTHOR}", font=subtitle_font, fg=fg_accent, bg=bg, cursor="hand2")
        author_label.pack(pady=(0, 8))
        if config.APP_URL:
            def open_url(event):
                import webbrowser
                webbrowser.open(config.APP_URL)
            author_label.bind("<Button-1>", open_url)

        # Status indicator
        state_text = "Recording..." if recording else "Ready"
        state_color = "#ff4444" if recording else "#44cc44"
        tk.Label(win, text=f"* {state_text}", font=header_font, fg=state_color, bg=bg).pack(pady=(0, 8))

        # --- Helper: toggle row ---
        def make_toggle_row(parent, label_text, get_state, toggle_fn, format_fn=None):
            row = tk.Frame(parent, bg=bg_section)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label_text, font=label_font, fg=fg_dim, bg=bg_section, anchor="w").pack(side="left")

            if format_fn:
                btn_text = format_fn()
            else:
                btn_text = "ON" if get_state() else "OFF"
            btn_color = fg_on if get_state() else fg_off

            btn = tk.Label(row, text=btn_text, font=btn_font, fg=btn_color, bg=bg_btn,
                          padx=10, pady=2, cursor="hand2")
            btn.pack(side="right")

            def on_click(event):
                toggle_fn()
                if format_fn:
                    new_text = format_fn()
                    new_color = fg_accent
                else:
                    new_text = "ON" if get_state() else "OFF"
                    new_color = fg_on if get_state() else fg_off
                btn.config(text=new_text, fg=new_color)

            btn.bind("<Button-1>", on_click)
            btn.bind("<Enter>", lambda e: btn.config(bg=bg_btn_hover))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg_btn))

        # --- Settings toggles ---
        tk.Label(win, text="Settings", font=header_font, fg=fg, bg=bg).pack(pady=(5, 5))
        toggle_frame = tk.Frame(win, bg=bg_section, padx=15, pady=10)
        toggle_frame.pack(fill="x", padx=15)

        # Transcription
        def toggle_transcription_ui():
            if config.TRANSCRIPTION_MODE == "api":
                config.TRANSCRIPTION_MODE = "local"
                threading.Thread(target=_ensure_local_model, daemon=True).start()
            elif config.OPENAI_API_KEY:
                config.TRANSCRIPTION_MODE = "api"
            else:
                _show_api_key_help(win)

        make_toggle_row(toggle_frame, "Transcription",
                       lambda: config.TRANSCRIPTION_MODE == "api",
                       toggle_transcription_ui,
                       lambda: "API (cloud)" if config.TRANSCRIPTION_MODE == "api" else "Local (free)")

        # AI Cleanup
        def toggle_cleanup_ui():
            if not config.OPENAI_API_KEY and not config.ENABLE_CLEANUP:
                _show_api_key_help(win)
                return
            config.ENABLE_CLEANUP = not config.ENABLE_CLEANUP

        make_toggle_row(toggle_frame, "AI Cleanup",
                       lambda: config.ENABLE_CLEANUP, toggle_cleanup_ui)

        # Language
        def toggle_language_ui():
            cycle = config.LANGUAGE_CYCLE
            try:
                idx = cycle.index(config.LANGUAGE)
            except ValueError:
                idx = -1
            config.LANGUAGE = cycle[(idx + 1) % len(cycle)]

        make_toggle_row(toggle_frame, "Language", lambda: True, toggle_language_ui,
                       lambda: {"auto": "Auto-detect", "en": "English", "es": "Espanol"}.get(config.LANGUAGE, config.LANGUAGE))

        make_toggle_row(toggle_frame, "Mute Audio",
                       lambda: config.MUTE_DURING_RECORDING,
                       lambda: setattr(config, 'MUTE_DURING_RECORDING', not config.MUTE_DURING_RECORDING))

        make_toggle_row(toggle_frame, "Strip Fillers",
                       lambda: config.STRIP_FILLERS,
                       lambda: setattr(config, 'STRIP_FILLERS', not config.STRIP_FILLERS))

        # Simple hotkeys toggle
        def toggle_simple_mode():
            config.SIMPLE_HOTKEYS = not config.SIMPLE_HOTKEYS
            _register_hotkeys()

        make_toggle_row(toggle_frame, "Simple Hotkeys",
                       lambda: config.SIMPLE_HOTKEYS, toggle_simple_mode)

        # --- Hotkeys (clickable to change) ---
        tk.Label(win, text="Hotkeys  (click to change)", font=header_font, fg=fg, bg=bg).pack(pady=(12, 5))
        hk_frame = tk.Frame(win, bg=bg_section, padx=15, pady=10)
        hk_frame.pack(fill="x", padx=15)

        def make_hotkey_row(parent, config_attr, action_label):
            row = tk.Frame(parent, bg=bg_section)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=action_label, font=label_font, fg=fg_dim, bg=bg_section, anchor="w").pack(side="left")

            current = getattr(config, config_attr)
            hk_btn = tk.Label(row, text=current, font=("Menlo", 9), fg=fg_accent, bg=bg_btn,
                             padx=8, pady=2, cursor="hand2")
            hk_btn.pack(side="right")

            def on_change(event):
                new_key = simpledialog.askstring(
                    f"Change {action_label} Hotkey",
                    f"Enter new hotkey for {action_label}:\n\n"
                    f"Examples: cmd+shift+space, f9, ctrl+shift+d\n\n"
                    f"Current: {getattr(config, config_attr)}",
                    parent=win,
                )
                if new_key and new_key.strip():
                    new_key = new_key.strip().lower()
                    setattr(config, config_attr, new_key)
                    hk_btn.config(text=new_key)
                    _register_hotkeys()
                    print(f"  Hotkey {action_label} changed to: {new_key}")

            hk_btn.bind("<Button-1>", on_change)
            hk_btn.bind("<Enter>", lambda e: hk_btn.config(bg=bg_btn_hover))
            hk_btn.bind("<Leave>", lambda e: hk_btn.config(bg=bg_btn))

        make_hotkey_row(hk_frame, "HOTKEY", "Dictate")
        make_hotkey_row(hk_frame, "TOGGLE_CLEANUP_HOTKEY", "Cleanup")
        make_hotkey_row(hk_frame, "TOGGLE_TRANSCRIPTION_HOTKEY", "API/Local")
        make_hotkey_row(hk_frame, "TOGGLE_LANGUAGE_HOTKEY", "Language")

        # --- Session stats ---
        tk.Label(win, text="Session", font=header_font, fg=fg, bg=bg).pack(pady=(12, 5))
        stats_frame = tk.Frame(win, bg=bg_section, padx=15, pady=8)
        stats_frame.pack(fill="x", padx=15)

        uptime = ""
        if session_stats["start_time"]:
            elapsed = time.time() - session_stats["start_time"]
            mins = int(elapsed // 60)
            uptime = f"{mins}m" if mins > 0 else "<1m"

        for label, value in [
            ("Dictations", str(session_stats["dictations"])),
            ("Audio recorded", f"{session_stats['total_seconds']:.0f}s"),
            ("Uptime", uptime),
        ]:
            row = tk.Frame(stats_frame, bg=bg_section)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=label_font, fg=fg_dim, bg=bg_section, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=label_font, fg=fg_accent, bg=bg_section, anchor="e").pack(side="right")

        # --- Footer ---
        tk.Label(win, text="", bg=bg).pack(fill="x", expand=True)
        footer = tk.Label(win, text=f"{config.APP_NAME} by {config.APP_AUTHOR}", font=link_font, fg=fg_dim, bg=bg, cursor="hand2")
        footer.pack(pady=(5, 10))
        if config.APP_URL:
            footer.bind("<Button-1>", lambda e: __import__('webbrowser').open(config.APP_URL))

        win.bind("<Escape>", lambda e: on_close())
        win.mainloop()

    except Exception as e:
        _status_window = None
        log(f"Status window error: {e}")


def _start_tray():
    """Start the system tray icon."""
    global tray_icon
    try:
        import pystray
        from pystray import MenuItem as Item

        _init_icons()

        if _icon_idle is None:
            log("Could not load tray icons, skipping tray")
            return

        menu = pystray.Menu(
            Item("Status", _show_status_window, default=True),
            pystray.Menu.SEPARATOR,
            Item("Quit", _quit_app),
        )

        tray_icon = pystray.Icon(
            "voza",
            _icon_idle,
            f"{config.APP_NAME} -- Ready",
            menu,
        )

        # pystray on Mac needs to run on the main thread or via rumps
        # We run it in a thread here; on Mac it uses the AppKit backend
        threading.Thread(target=tray_icon.run, daemon=True).start()
        log("System tray icon started")

    except ImportError:
        log("pystray not installed -- no tray icon (pip3 install pystray)")
    except Exception as e:
        log(f"Could not start tray icon: {e}")


# --- System Volume Control (Mac: osascript) ----------------------------------
_volume_was_muted = False


def mute_system_audio():
    """Mute system output volume."""
    global _volume_was_muted
    if not config.MUTE_DURING_RECORDING:
        return
    try:
        # Check current mute state
        result = subprocess.run(
            ["osascript", "-e", "output muted of (get volume settings)"],
            capture_output=True, text=True, timeout=3
        )
        _volume_was_muted = result.stdout.strip() == "true"
        # Mute
        subprocess.run(
            ["osascript", "-e", "set volume output muted true"],
            capture_output=True, timeout=3
        )
        log("System audio muted (osascript)")
    except Exception as e:
        log(f"Could not mute system audio: {e}")


def unmute_system_audio():
    """Restore system volume."""
    global _volume_was_muted
    if not config.MUTE_DURING_RECORDING:
        return
    try:
        if not _volume_was_muted:
            subprocess.run(
                ["osascript", "-e", "set volume output muted false"],
                capture_output=True, timeout=3
            )
        log("System audio restored (osascript)")
    except Exception as e:
        log(f"Could not unmute system audio: {e}")


# --- Audio Helpers -----------------------------------------------------------
def _normalize_audio(audio_data):
    """Normalize audio to a consistent volume level.
    Helps when the mic signal is weak (e.g. shared with FaceTime/Zoom)."""
    if not config.NORMALIZE_AUDIO:
        return audio_data
    peak = np.max(np.abs(audio_data))
    if peak < 0.001:
        return audio_data
    target_peak = 0.9
    gain = target_peak / peak
    gain = min(gain, config.NORMALIZE_MAX_GAIN)
    if gain > 1.1:
        log(f"Normalizing audio: peak={peak:.4f}, gain={gain:.1f}x")
        audio_data = audio_data * gain
    return audio_data


def frames_to_wav(frames):
    """Convert a list of float32 audio frames to an in-memory WAV BytesIO."""
    if not frames:
        return None
    audio_data = np.concatenate(frames, axis=0)
    audio_data = _normalize_audio(audio_data)
    audio_data = np.clip(audio_data, -1.0, 1.0)
    pcm = (audio_data * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(config.SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    buf.seek(0)
    return buf


def frames_duration_secs(frames):
    """Calculate the duration in seconds of a list of audio frames."""
    if not frames:
        return 0.0
    total_samples = sum(f.shape[0] for f in frames)
    return total_samples / config.SAMPLE_RATE


# --- Audio Recording ---------------------------------------------------------
def audio_callback(indata, frames, time_info, status):
    """Called by sounddevice for each audio chunk."""
    if status and config.DEBUG:
        print(f"  [AUDIO] {status}")
    audio_frames.append(indata.copy())


def start_recording():
    """Begin capturing microphone audio."""
    global recording, audio_frames, stream, chunk_results, chunk_executor, chunk_frame_index
    with lock:
        if recording:
            return
        recording = True
        audio_frames = []
        chunk_results = []
        chunk_frame_index = 0
        chunk_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    log("Recording started")
    set_tray_state("recording")
    # Start muting in background during the beep
    mute_thread = threading.Thread(target=mute_system_audio, daemon=True)
    mute_thread.start()
    _play_beeps([config.SOUND_START])  # synchronous
    mute_thread.join(timeout=1)

    stream = sd.InputStream(
        samplerate=config.SAMPLE_RATE,
        channels=config.CHANNELS,
        dtype="float32",
        callback=audio_callback,
        blocksize=1024,
    )
    stream.start()

    threading.Thread(target=_chunk_watcher, daemon=True).start()
    if config.SILENCE_TIMEOUT > 0:
        threading.Thread(target=_silence_watcher, daemon=True).start()


def stop_recording():
    """Stop capturing."""
    global recording, stream
    with lock:
        if not recording:
            return None
        recording = False

    log("Recording stopped")
    set_tray_state("processing")
    unmute_system_audio()
    beep(config.SOUND_STOP)

    if stream is not None:
        stream.stop()
        stream.close()
        stream = None

    if not audio_frames:
        log("No audio captured")
        return None

    return True


def _silence_watcher():
    """Auto-stop recording after sustained silence."""
    silence_start = None
    while recording:
        time.sleep(0.2)
        if not audio_frames:
            continue
        recent = audio_frames[-1]
        rms = np.sqrt(np.mean(recent ** 2))
        if rms < config.SILENCE_THRESHOLD:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start >= config.SILENCE_TIMEOUT:
                log("Silence timeout -- auto-stopping")
                process_dictation()
                return
        else:
            silence_start = None


# --- Background Chunking ----------------------------------------------------
CHUNK_INTERVAL_SECS = 20
OVERLAP_SECS = 2


def _chunk_watcher():
    """Periodically send accumulated audio to Whisper in the background."""
    global chunk_frame_index

    while recording:
        time.sleep(1.0)
        current_frames = audio_frames[chunk_frame_index:]
        duration = frames_duration_secs(current_frames)

        if duration >= CHUNK_INTERVAL_SECS:
            overlap_samples = int(OVERLAP_SECS * config.SAMPLE_RATE)
            overlap_start = chunk_frame_index
            overlap_sample_count = 0

            if chunk_frame_index > 0:
                for i in range(chunk_frame_index - 1, -1, -1):
                    overlap_sample_count += audio_frames[i].shape[0]
                    overlap_start = i
                    if overlap_sample_count >= overlap_samples:
                        break

            chunk_frames = audio_frames[overlap_start:][:len(current_frames) + (chunk_frame_index - overlap_start)]
            chunk_wav = frames_to_wav(chunk_frames)

            if chunk_wav:
                chunk_num = len(chunk_results) + 1
                log(f"Sending chunk {chunk_num} ({duration:.1f}s + {OVERLAP_SECS}s overlap)")
                future = chunk_executor.submit(_transcribe_chunk, chunk_wav, chunk_num)
                chunk_results.append(future)

            chunk_frame_index = len(audio_frames)


def _transcribe_chunk(wav_buf, chunk_num):
    """Transcribe a single audio chunk."""
    try:
        text = transcribe_audio(wav_buf)
        log(f"Chunk {chunk_num} result: {text[:60]}...")
        print(f"  [chunk {chunk_num}] done")
        return text
    except Exception as e:
        log(f"Chunk {chunk_num} failed: {e}")
        print(f"  [chunk {chunk_num}] failed: {e}")
        return ""


# --- Transcription -----------------------------------------------------------
def _ensure_local_model():
    """Load the local Whisper model if not already loaded."""
    global local_whisper_model
    if local_whisper_model is None:
        print("  Loading local Whisper model (first time may take a moment)...")
        from faster_whisper import WhisperModel
        local_whisper_model = WhisperModel(
            config.LOCAL_WHISPER_MODEL, device="auto", compute_type="auto"
        )
        print(f"  Local model '{config.LOCAL_WHISPER_MODEL}' loaded")


def transcribe_audio(wav_buf):
    """Send audio to Whisper and return raw text."""
    if config.TRANSCRIPTION_MODE == "local":
        return _transcribe_local(wav_buf)

    try:
        return _transcribe_api(wav_buf)
    except Exception as e:
        if config.API_FALLBACK_TO_LOCAL:
            print(f"  Warning: API failed ({e}), falling back to local...")
            beep(config.SOUND_ERROR)
            wav_buf.seek(0)
            return _transcribe_local(wav_buf)
        else:
            raise


def _transcribe_api(wav_buf):
    """Use OpenAI Whisper API."""
    lang = config.LANGUAGE
    log(f"Transcribing via Whisper API... (language: {lang})")
    wav_buf.name = "audio.wav"
    kwargs = dict(
        model=config.WHISPER_MODEL,
        file=wav_buf,
        response_format="text",
        timeout=config.API_TIMEOUT_SECS,
    )
    if config.WHISPER_PROMPT:
        kwargs["prompt"] = config.WHISPER_PROMPT
    if lang != "auto":
        kwargs["language"] = lang
    response = client.audio.transcriptions.create(**kwargs)
    text = response.strip() if isinstance(response, str) else response.text.strip()
    log(f"Raw transcription: {text}")
    return text


def _transcribe_local(wav_buf):
    """Use local faster-whisper model."""
    _ensure_local_model()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(wav_buf.read())
    tmp.close()

    lang = config.LANGUAGE
    transcribe_kwargs = dict(beam_size=5)
    if lang != "auto":
        transcribe_kwargs["language"] = lang
    if config.WHISPER_PROMPT:
        transcribe_kwargs["initial_prompt"] = config.WHISPER_PROMPT
    segments, _ = local_whisper_model.transcribe(tmp.name, **transcribe_kwargs)
    text = " ".join(seg.text for seg in segments).strip()
    log(f"Raw transcription (local): {text}")

    os.unlink(tmp.name)
    return text


# --- Stitching ---------------------------------------------------------------
def stitch_chunks(chunk_texts):
    """Use GPT to merge overlapping chunk transcriptions."""
    if len(chunk_texts) <= 1:
        return chunk_texts[0] if chunk_texts else ""

    log(f"Stitching {len(chunk_texts)} chunks...")
    numbered = "\n".join(f"[Chunk {i+1}]: {t}" for i, t in enumerate(chunk_texts))

    response = client.chat.completions.create(
        model=config.CLEANUP_MODEL,
        messages=[
            {"role": "system", "content": STITCH_PROMPT},
            {"role": "user", "content": numbered},
        ],
        temperature=0.2,
        max_tokens=8192,
    )
    result = response.choices[0].message.content.strip()
    log(f"Stitched result: {result[:100]}...")
    return result


STITCH_PROMPT = """You are a transcription stitcher. You receive numbered chunks of speech-to-text output that were transcribed from overlapping audio segments of a single continuous recording.

Your job:
- Merge them into one continuous, clean text
- The chunks overlap by a few seconds, so the END of one chunk and the START of the next chunk contain the same words -- remove the duplicates
- Preserve every word the speaker said (do not add, remove, or rephrase anything)
- Just merge and de-duplicate -- do NOT clean up grammar, punctuation, or style
- Return ONLY the merged text with no commentary, labels, or explanation"""


# --- Filler Word Removal ----------------------------------------------------
import re

_FILLER_PATTERNS = [
    r'\b[Uu]h\b[,.]?\s*',
    r'\b[Uu]m\b[,.]?\s*',
    r'\b[Uu]mm\b[,.]?\s*',
    r'\b[Hh]mm\b[,.]?\s*',
    r'\b[Ee]r\b[,.]?\s*',
]
_FILLER_REGEX = re.compile('|'.join(_FILLER_PATTERNS))


def strip_fillers(text):
    """Remove common filler words."""
    if not config.STRIP_FILLERS:
        return text
    cleaned = _FILLER_REGEX.sub('', text)
    cleaned = re.sub(r'  +', ' ', cleaned).strip()
    cleaned = re.sub(r'^[,.\s]+', '', cleaned)
    return cleaned


# --- Cleanup with GPT -------------------------------------------------------
def cleanup_text(raw_text):
    """Send raw transcription through GPT for light cleanup."""
    raw_text = strip_fillers(raw_text)

    if not config.ENABLE_CLEANUP:
        return raw_text

    log("Cleaning up with GPT...")
    response = client.chat.completions.create(
        model=config.CLEANUP_MODEL,
        messages=[
            {"role": "system", "content": config.CLEANUP_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    cleaned = response.choices[0].message.content.strip()
    log(f"Cleaned text: {cleaned}")
    return cleaned


# --- Text Insertion (Mac: Cmd+V) ---------------------------------------------
def insert_text(text):
    """Insert text at the current cursor position."""
    if not text:
        return

    time.sleep(config.INSERTION_DELAY)

    if config.INSERTION_METHOD == "clipboard":
        _insert_via_clipboard(text)
    else:
        _insert_via_typewrite(text)


def _insert_via_clipboard(text):
    """Copy to clipboard and paste with Cmd+V."""
    old_clipboard = None
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        pass

    pyperclip.copy(text)
    time.sleep(0.02)

    # Mac: Cmd+V to paste
    from pynput.keyboard import Controller, Key
    kb = Controller()
    kb.press(Key.cmd)
    kb.press('v')
    kb.release('v')
    kb.release(Key.cmd)
    time.sleep(0.05)

    if old_clipboard is not None:
        time.sleep(0.15)
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass


def _insert_via_typewrite(text):
    """Type text character by character."""
    from pynput.keyboard import Controller
    kb = Controller()
    for char in text:
        kb.type(char)
        time.sleep(0.01)


# --- Main Processing Pipeline -----------------------------------------------
def process_dictation():
    """Stop recording -> collect chunks + final audio -> stitch -> clean -> insert."""
    global chunk_executor
    try:
        result = stop_recording()
        if result is None:
            return

        total_duration = frames_duration_secs(audio_frames)
        if total_duration < 0.3:
            log("Audio too short, ignoring")
            return

        # --- Kick off remaining audio transcription IMMEDIATELY ---
        remaining_frames = audio_frames[chunk_frame_index:]
        remaining_duration = frames_duration_secs(remaining_frames)
        remaining_future = None

        if remaining_duration > 0.3:
            overlap_samples = int(OVERLAP_SECS * config.SAMPLE_RATE)
            overlap_start = chunk_frame_index
            overlap_count = 0
            has_chunks = len(chunk_results) > 0

            if chunk_frame_index > 0 and has_chunks:
                for i in range(chunk_frame_index - 1, -1, -1):
                    overlap_count += audio_frames[i].shape[0]
                    overlap_start = i
                    if overlap_count >= overlap_samples:
                        break

            if has_chunks:
                final_frames = audio_frames[overlap_start:]
            else:
                final_frames = remaining_frames

            final_wav = frames_to_wav(final_frames)
            if final_wav:
                log("Transcribing final segment in parallel with chunk collection")
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                remaining_future = executor.submit(transcribe_audio, final_wav)

        # --- Collect already-completed background chunks ---
        completed_texts = []
        for future in chunk_results:
            try:
                text = future.result(timeout=10)
                if text and text.strip():
                    completed_texts.append(text.strip())
            except Exception as e:
                log(f"Chunk future failed: {e}")

        # --- Collect the remaining segment (was transcribing in parallel) ---
        if remaining_future is not None:
            try:
                final_text = remaining_future.result(timeout=15)
                if final_text and final_text.strip():
                    completed_texts.append(final_text.strip())
            except Exception as e:
                log(f"Final segment failed: {e}")

        if not completed_texts:
            log("No transcription results")
            return

        # Stitch chunks if multiple
        if len(completed_texts) > 1:
            print(f"  Stitching {len(completed_texts)} chunks...")
            raw_text = stitch_chunks(completed_texts)
        else:
            raw_text = completed_texts[0]

        if not raw_text or raw_text.strip() == "":
            log("Empty transcription, skipping")
            return

        # Optional cleanup
        if config.ENABLE_CLEANUP:
            print("  Cleaning up...")
        final_text = cleanup_text(raw_text)

        if not final_text:
            log("Empty after cleanup, skipping")
            return

        session_stats["dictations"] += 1
        session_stats["total_seconds"] += frames_duration_secs(audio_frames)

        print(f"  Inserting: {final_text[:80]}{'...' if len(final_text) > 80 else ''}")
        insert_text(final_text)
        print("  Done")

    except Exception as e:
        print(f"  Error: {e}")
        beep(config.SOUND_ERROR)
        if config.DEBUG:
            import traceback
            traceback.print_exc()
    finally:
        set_tray_state("idle")
        if chunk_executor:
            chunk_executor.shutdown(wait=False)
            chunk_executor = None


# --- Hotkey Registration (pynput) --------------------------------------------
def _parse_hotkey_string(hotkey_str):
    """Parse a hotkey string like 'cmd+shift+space' into a pynput HotKey-compatible set."""
    from pynput.keyboard import Key, KeyCode, HotKey

    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    keys = []

    key_map = {
        "cmd": Key.cmd, "command": Key.cmd, "super": Key.cmd,
        "ctrl": Key.ctrl, "control": Key.ctrl,
        "shift": Key.shift,
        "alt": Key.alt, "option": Key.alt, "opt": Key.alt,
        "space": Key.space,
        "tab": Key.tab,
        "enter": Key.enter, "return": Key.enter,
        "esc": Key.esc, "escape": Key.esc,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    }

    # F-keys
    for i in range(1, 21):
        key_map[f"f{i}"] = getattr(Key, f"f{i}", None)

    for part in parts:
        if part in key_map and key_map[part] is not None:
            keys.append(key_map[part])
        elif len(part) == 1:
            keys.append(KeyCode.from_char(part))
        else:
            log(f"Unknown key: {part}")

    return keys


def _register_hotkeys():
    """Register all global hotkeys using pynput."""
    global _hotkey_listener

    # Stop existing listener
    if _hotkey_listener is not None:
        try:
            _hotkey_listener.stop()
        except Exception:
            pass
        _hotkey_listener = None

    from pynput.keyboard import HotKey, Listener

    hotkeys_to_register = []

    # Always register main dictation hotkey
    hotkeys_to_register.append(
        HotKey(_parse_hotkey_string(config.HOTKEY), on_hotkey)
    )

    # Register toggle hotkeys only if not in simple mode
    if not config.SIMPLE_HOTKEYS:
        if config.OPENAI_API_KEY:
            hotkeys_to_register.append(
                HotKey(_parse_hotkey_string(config.TOGGLE_CLEANUP_HOTKEY), on_toggle_cleanup)
            )
            hotkeys_to_register.append(
                HotKey(_parse_hotkey_string(config.TOGGLE_TRANSCRIPTION_HOTKEY), on_toggle_transcription)
            )
        hotkeys_to_register.append(
            HotKey(_parse_hotkey_string(config.TOGGLE_LANGUAGE_HOTKEY), on_toggle_language)
        )

    def for_canonical(f):
        return lambda k: f(_hotkey_listener.canonical(k))

    def on_press(key):
        for hk in hotkeys_to_register:
            hk.press(_hotkey_listener.canonical(key))

    def on_release(key):
        for hk in hotkeys_to_register:
            hk.release(_hotkey_listener.canonical(key))

    _hotkey_listener = Listener(on_press=on_press, on_release=on_release)
    _hotkey_listener.start()

    mode = "Simple" if config.SIMPLE_HOTKEYS else "Full"
    log(f"Hotkeys registered ({mode} mode)")


# --- Hotkey Handlers ---------------------------------------------------------
def on_hotkey():
    """Toggle recording on/off."""
    if recording:
        threading.Thread(target=process_dictation, daemon=True).start()
    else:
        start_recording()


def on_toggle_cleanup():
    """Toggle AI cleanup on/off."""
    if not config.OPENAI_API_KEY:
        print("  AI cleanup requires an OpenAI API key. Add one to .env to enable.")
        beep(config.SOUND_ERROR)
        return
    config.ENABLE_CLEANUP = not config.ENABLE_CLEANUP
    state = "ON" if config.ENABLE_CLEANUP else "OFF"
    print(f"  AI cleanup: {state}")
    if config.ENABLE_CLEANUP:
        beep((600, 80), (700, 80), (800, 80))
    else:
        beep((300, 200))


def on_toggle_language():
    """Cycle through languages."""
    cycle = config.LANGUAGE_CYCLE
    current = config.LANGUAGE
    try:
        idx = cycle.index(current)
    except ValueError:
        idx = -1
    next_lang = cycle[(idx + 1) % len(cycle)]
    config.LANGUAGE = next_lang

    labels = {"auto": "AUTO-DETECT", "en": "ENGLISH", "es": "ESPANOL"}
    label = labels.get(next_lang, next_lang.upper())
    print(f"  Language: {label}")

    if next_lang == "auto":
        beep((500, 100), (600, 100), (700, 100))
    elif next_lang == "en":
        beep((700, 200))
    elif next_lang == "es":
        beep((500, 200), (500, 200))


def on_toggle_transcription():
    """Toggle between API and local transcription."""
    if config.TRANSCRIPTION_MODE == "api":
        config.TRANSCRIPTION_MODE = "local"
        print("  Transcription: LOCAL (free, offline)")
        threading.Thread(target=_ensure_local_model, daemon=True).start()
        beep((400, 150), (400, 150))
    else:
        if not config.OPENAI_API_KEY:
            print("  API mode requires an OpenAI API key. Add one to .env to enable.")
            beep(config.SOUND_ERROR)
            return
        config.TRANSCRIPTION_MODE = "api"
        print("  Transcription: API (cloud, faster)")
        beep((700, 150), (700, 150))


# --- Startup -----------------------------------------------------------------
def check_microphone():
    """Verify a microphone is available."""
    try:
        default_input = sd.query_devices(kind="input")
        print(f"  Microphone: {default_input['name']}")
        return True
    except Exception as e:
        print(f"  No microphone found: {e}")
        return False


def _hotkey_watchdog():
    """Background thread that checks if the pynput hotkey listener is alive.
    If it dies (e.g. after sleep/wake), automatically re-register hotkeys."""
    while True:
        time.sleep(30)
        try:
            if _hotkey_listener is not None and not _hotkey_listener.is_alive():
                log("Hotkey listener died -- re-registering hotkeys")
                _register_hotkeys()
        except Exception as e:
            log(f"Hotkey watchdog error: {e}")
            try:
                _register_hotkeys()
            except Exception:
                pass


def main():
    global client

    print()
    print(f"  {config.APP_NAME} -- {config.APP_TAGLINE}")
    print(f"  by {config.APP_AUTHOR}")
    print()

    # Set up OpenAI client if API key is available
    if config.OPENAI_API_KEY:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        print(f"  OpenAI API key loaded")
    else:
        print(f"  No API key -- running in fully local mode (free)")
        print(f"    To upgrade: add OPENAI_API_KEY=sk-... to .env file")
        config.TRANSCRIPTION_MODE = "local"
        config.ENABLE_CLEANUP = False
        config.API_FALLBACK_TO_LOCAL = False

    if not check_microphone():
        sys.exit(1)

    # Pre-load local model if starting in local mode
    if config.TRANSCRIPTION_MODE == "local":
        print("  Loading local Whisper model (first launch may take a moment)...")
        _ensure_local_model()

    # Status display
    mode = "API (cloud)" if config.TRANSCRIPTION_MODE == "api" else "LOCAL (free)"
    cleanup_state = "ON" if config.ENABLE_CLEANUP else "OFF"
    lang_labels = {"auto": "AUTO-DETECT", "en": "ENGLISH", "es": "ESPANOL"}
    lang_label = lang_labels.get(config.LANGUAGE, config.LANGUAGE.upper())

    print(f"  Transcription: {mode}")
    print(f"  AI cleanup: {cleanup_state}")
    print(f"  Language: {lang_label}")
    if config.OPENAI_API_KEY and config.API_FALLBACK_TO_LOCAL:
        print(f"  Auto-fallback to local: ON")
    print(f"  Background chunking: every {CHUNK_INTERVAL_SECS}s")
    print(f"  Hotkey mode: {'Simple' if config.SIMPLE_HOTKEYS else 'Full'}")
    print()
    print(f"  [ {config.HOTKEY} ]          -> start/stop dictation")
    if not config.SIMPLE_HOTKEYS:
        if config.OPENAI_API_KEY:
            print(f"  [ {config.TOGGLE_CLEANUP_HOTKEY} ]  -> toggle AI cleanup")
            print(f"  [ {config.TOGGLE_TRANSCRIPTION_HOTKEY} ]  -> toggle API / local")
        print(f"  [ {config.TOGGLE_LANGUAGE_HOTKEY} ]  -> cycle language (auto/EN/ES)")
    print(f"  Click menu bar icon       -> settings & status")
    print()

    # NOTE for Mac users: pynput needs Accessibility permissions
    print("  NOTE: If hotkeys don't work, grant Accessibility permissions:")
    print("    System Settings -> Privacy & Security -> Accessibility")
    print("    Add your terminal app (Terminal, iTerm2, etc.)")
    print()

    # Register global hotkeys
    _register_hotkeys()

    # Start hotkey watchdog (auto-recovers if listener dies after sleep/wake)
    threading.Thread(target=_hotkey_watchdog, daemon=True).start()

    # Track session start time
    session_stats["start_time"] = time.time()

    # Start menu bar icon
    _start_tray()

    print("  Voza is running. Press the hotkey to start dictating.")
    print("  Press Ctrl+C to quit.")
    print()

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Shutting down. Goodbye!")
        if recording:
            stop_recording()
        if tray_icon:
            tray_icon.stop()


if __name__ == "__main__":
    main()
