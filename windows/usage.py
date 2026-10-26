"""
Voza Usage Tracker — tracks API calls and estimated costs per month.
Data is stored in usage.json next to the app, keyed by YYYY-MM.
"""

import json
import os
import threading
import time

# Pricing (USD) — updated July 2026
PRICING = {
    "whisper-1": 0.006,                   # per minute of audio (OpenAI)
    "whisper-large-v3-turbo": 0.000667,   # per minute of audio (Groq, $0.04/hr)
    "gpt-4o-mini": {
        "input": 0.000150,       # per 1K tokens
        "output": 0.000600,      # per 1K tokens
    },
    "gpt-4o": {
        "input": 0.005,          # per 1K tokens
        "output": 0.015,         # per 1K tokens
    },
    "openai/gpt-oss-20b": {
        "input": 0.000075,       # per 1K tokens (Groq)
        "output": 0.00030,       # per 1K tokens (Groq)
    },
    "llama-3.1-8b-instant": {
        "input": 0.00005,        # per 1K tokens (Groq)
        "output": 0.00008,       # per 1K tokens (Groq)
    },
}

_lock = threading.Lock()
_usage_file = None
_data = None


def _get_usage_file():
    """Find the usage.json file path (next to the running script)."""
    global _usage_file
    if _usage_file is None:
        import sys
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        _usage_file = os.path.join(app_dir, "usage.json")
    return _usage_file


def _current_month():
    """Return current month key like '2026-04'."""
    return time.strftime("%Y-%m")


def _load():
    """Load usage data from disk."""
    global _data
    if _data is not None:
        return _data

    path = _get_usage_file()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                loaded = json.load(f)
            # Migrate old flat format to monthly format
            if "total_whisper_calls" in loaded:
                _data = _migrate_old_data(loaded)
                _save()
            else:
                _data = loaded
        except (json.JSONDecodeError, IOError):
            _data = {}
    else:
        _data = {}
    return _data


def _migrate_old_data(old):
    """Migrate old flat usage.json to monthly format."""
    month = old.get("first_used", "")[:7] if old.get("first_used") else _current_month()
    if not month or len(month) < 7:
        month = _current_month()
    return {
        month: {
            "whisper_calls": old.get("total_whisper_calls", 0),
            "whisper_seconds": old.get("total_whisper_seconds", 0.0),
            "whisper_cost": old.get("total_whisper_cost", 0.0),
            "cleanup_calls": old.get("total_cleanup_calls", 0),
            "cleanup_input_tokens": old.get("total_cleanup_input_tokens", 0),
            "cleanup_output_tokens": old.get("total_cleanup_output_tokens", 0),
            "cleanup_cost": old.get("total_cleanup_cost", 0.0),
            "stitch_calls": old.get("total_stitch_calls", 0),
            "stitch_input_tokens": old.get("total_stitch_input_tokens", 0),
            "stitch_output_tokens": old.get("total_stitch_output_tokens", 0),
            "stitch_cost": old.get("total_stitch_cost", 0.0),
            "local_calls": old.get("total_local_calls", 0),
            "local_seconds": old.get("total_local_seconds", 0.0),
            "first_used": old.get("first_used"),
            "last_used": old.get("last_used"),
        }
    }


def _default_month():
    return {
        "whisper_calls": 0,
        "whisper_seconds": 0.0,
        "whisper_cost": 0.0,
        "cleanup_calls": 0,
        "cleanup_input_tokens": 0,
        "cleanup_output_tokens": 0,
        "cleanup_cost": 0.0,
        "stitch_calls": 0,
        "stitch_input_tokens": 0,
        "stitch_output_tokens": 0,
        "stitch_cost": 0.0,
        "local_calls": 0,
        "local_seconds": 0.0,
        "first_used": None,
        "last_used": None,
    }


def _get_month(month=None):
    """Get or create the data dict for a specific month."""
    data = _load()
    if month is None:
        month = _current_month()
    if month not in data:
        data[month] = _default_month()
    return data[month]


def _save():
    """Persist usage data to disk."""
    if _data is None:
        return
    path = _get_usage_file()
    try:
        with open(path, "w") as f:
            json.dump(_data, f, indent=2)
    except IOError:
        pass


def log_whisper_api_call(audio_seconds, model="whisper-1"):
    """Log a Whisper API transcription call."""
    with _lock:
        m = _get_month()
        cost = (audio_seconds / 60.0) * PRICING.get(model, 0.006)
        m["whisper_calls"] += 1
        m["whisper_seconds"] += audio_seconds
        m["whisper_cost"] += cost
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if m["first_used"] is None:
            m["first_used"] = now
        m["last_used"] = now
        _save()
        return cost


def log_local_call(audio_seconds):
    """Log a local transcription call."""
    with _lock:
        m = _get_month()
        m["local_calls"] += 1
        m["local_seconds"] += audio_seconds
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if m["first_used"] is None:
            m["first_used"] = now
        m["last_used"] = now
        _save()


def log_gpt_call(call_type, model, input_tokens=0, output_tokens=0):
    """Log a GPT call (cleanup or stitch).
    call_type: 'cleanup' or 'stitch'
    """
    with _lock:
        m = _get_month()
        pricing = PRICING.get(model, PRICING.get("gpt-4o-mini"))
        if isinstance(pricing, dict):
            cost = (input_tokens / 1000.0) * pricing["input"] + \
                   (output_tokens / 1000.0) * pricing["output"]
        else:
            cost = 0.0

        m[f"{call_type}_calls"] = m.get(f"{call_type}_calls", 0) + 1
        m[f"{call_type}_input_tokens"] = m.get(f"{call_type}_input_tokens", 0) + input_tokens
        m[f"{call_type}_output_tokens"] = m.get(f"{call_type}_output_tokens", 0) + output_tokens
        m[f"{call_type}_cost"] = m.get(f"{call_type}_cost", 0.0) + cost
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if m["first_used"] is None:
            m["first_used"] = now
        m["last_used"] = now
        _save()
        return cost


def get_summary(month=None):
    """Return a human-readable usage summary dict for a given month (default: current)."""
    with _lock:
        m = _get_month(month)

    total_api_cost = m["whisper_cost"] + m.get("cleanup_cost", 0) + m.get("stitch_cost", 0)
    whisper_minutes = m["whisper_seconds"] / 60.0
    local_minutes = m["local_seconds"] / 60.0

    return {
        "month": month or _current_month(),
        "whisper_calls": m["whisper_calls"],
        "whisper_minutes": round(whisper_minutes, 1),
        "whisper_cost": round(m["whisper_cost"], 4),
        "cleanup_calls": m.get("cleanup_calls", 0),
        "cleanup_cost": round(m.get("cleanup_cost", 0), 4),
        "stitch_calls": m.get("stitch_calls", 0),
        "stitch_cost": round(m.get("stitch_cost", 0), 4),
        "local_calls": m["local_calls"],
        "local_minutes": round(local_minutes, 1),
        "total_api_cost": round(total_api_cost, 4),
        "total_api_cost_display": f"${total_api_cost:.4f}",
        "first_used": m["first_used"],
        "last_used": m["last_used"],
    }


def get_months():
    """Return list of month keys sorted descending (newest first)."""
    with _lock:
        data = _load()
    return sorted(data.keys(), reverse=True)


def get_cost_display(month=None):
    """Return a short cost string for the status window."""
    s = get_summary(month)
    if s["whisper_calls"] == 0 and s["cleanup_calls"] == 0:
        return "No API calls yet"
    return f"${s['total_api_cost']:.4f} ({s['whisper_calls']} transcriptions, {s['whisper_minutes']}min)"
