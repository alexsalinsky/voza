# Voza -- Voice to text, your way.

**Free, open-source voice dictation for Windows and Mac.** Press a hotkey, speak naturally, and your words appear at your cursor -- in any app.

By [Alex Salinsky](https://www.linkedin.com/in/alexsalinsky/)

## The story

I was paying $12/month for Wispr Flow to do voice dictation on my computer. It's a great product, but I realized the underlying tech (Whisper for transcription, a small LLM for cleanup) costs almost nothing to call directly. So I built my own version in about 2 hours, then kept improving it through months of daily use.

Voza does the same thing -- global hotkey, speak naturally, text appears wherever your cursor is -- but it's free and open-source. You can run it entirely on your local machine for $0, or connect to Groq or OpenAI for higher accuracy at well under a dollar a month.

I use it every day for emails, Slack messages, notes, and long-form writing. It works while screen recording, on video calls, in any text field in any app.

## Demo

[Watch the demo video](demo.mp4)

## Features

- **Global hotkey** -- start/stop dictation from any app (Ctrl+Shift+Space on Windows, Cmd+Shift+Space on Mac)
- **Works everywhere** -- any text field in any application
- **Fully local mode** -- $0 cost, nothing leaves your computer
- **Cloud mode** -- Groq (`whisper-large-v3-turbo`, ~200x realtime, ~$0.04/hr of audio) or OpenAI Whisper (Windows; Mac supports OpenAI)
- **Auto-fallback** -- if the API is unreachable, falls back to local transcription automatically
- **Optional AI cleanup** -- fixes punctuation, grammar, and filler words (toggle on/off)
- **Custom vocabulary** -- add names or jargon so Whisper hears them correctly
- **Smart spacing** -- inserts a space when a dictation continues a previous one
- **Background chunking** -- transcribes while you speak, so even 5-minute dictations finish processing in about a second
- **Multi-language** -- English, Spanish, auto-detect (add more in config)
- **System tray icon** -- changes color to show state (idle / recording / processing)
- **Interactive settings window** -- toggle everything from the UI, view session stats, no config files needed
- **Customizable hotkeys** -- change them from the settings window
- **Audio normalization** -- works well even when sharing your mic with Zoom/OBS/Teams
- **Auto-start** -- launches on login so it's always ready
- **Simple hotkey mode** -- disable all hotkeys except the main one if you prefer minimal shortcuts

## Cost

| Mode | Monthly cost (30 min/day) |
|------|--------------------------|
| Fully local (no API key) | **$0.00** |
| Groq transcription + AI cleanup | **~$0.35** |
| OpenAI transcription + AI cleanup | ~$2.10 |

Compare to Wispr Flow at $12/month, Otter.ai at $16/month, or Dragon at $15/month.

Groq is the recommended cloud mode on Windows: a 30-second dictation transcribes in well under a second. When a `GROQ_API_KEY` is present, Voza uses it automatically for both transcription and cleanup.

## Quick start

### Windows

1. Download the `windows/` folder
2. Double-click `setup-voza.bat`
3. Done. Press **Ctrl+Shift+Space** to dictate.

For a standalone .exe you can share with anyone (no Python needed):
- Double-click `build-for-sharing.bat`
- Send the resulting `voza-share/` folder

Not a developer? Open `windows/SETUP_PROMPT.md`, paste it into Claude or ChatGPT, and the AI walks you through setup step by step.

### Mac

1. Download the `mac/` folder
2. Double-click `setup-voza.command`
   - If macOS blocks it: right-click, choose Open, click Open again
3. Done. Press **Cmd+Shift+Space** to dictate.

Both versions auto-start on login and run in the system tray / menu bar.

### Optional: Cloud transcription

Voza works out of the box in fully local mode (free). To enable cloud transcription for better accuracy:

1. Get a Groq key at [console.groq.com/keys](https://console.groq.com/keys) (Windows, recommended) or an OpenAI key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Copy `.env.example` to `.env` and paste your key
3. Restart Voza

## How it works

```
Hotkey -> Microphone captures audio -> Whisper transcribes -> Optional cleanup -> Text pasted at cursor
```

For short dictations, the audio is sent to Whisper in one shot after you stop.

For longer dictations, Voza sends audio chunks every 25 seconds while you're still talking. By the time you press stop, most of your speech is already transcribed. A stitching pass merges the chunks and removes overlapping text. A 5-minute dictation finishes processing in about 1 second.

## Settings

Click the tray icon / menu bar icon to open the settings window. From there you can:

- Switch between local (free) and cloud transcription
- Turn AI text cleanup on/off
- Change language (English, Spanish, auto-detect)
- Add custom vocabulary words
- Mute speakers during recording
- Strip filler words (uh, um, hmm)
- Change any hotkey
- Enable simple mode (one hotkey only)

For advanced configuration, edit `config.py`.

## Tech stack

- **Python 3.10+**
- **Whisper via Groq or OpenAI**, or **faster-whisper** (local) for speech-to-text
- **llama-3.1-8b-instant** (Groq) or **GPT-4o-mini** (OpenAI) for optional text cleanup
- **sounddevice** for audio capture
- **pystray + Pillow** for system tray
- **tkinter** for settings UI
- **keyboard** (Windows) / **pynput** (Mac) for global hotkeys
- **PyInstaller** for standalone Windows .exe builds

## Troubleshooting

**Hotkey not working (Windows):** Run as administrator. The keyboard library needs elevated privileges.

**Hotkey not working (Mac):** Grant Accessibility permissions: System Settings -> Privacy & Security -> Accessibility -> add Terminal.

**Transcription quality is poor:** Make sure your mic is set as the default input device. If sharing the mic with another app (Zoom, OBS), the audio normalization should handle it -- but check that your mic volume isn't too low in system settings.

**Text not appearing in some apps:** Try changing `INSERTION_METHOD = "typewrite"` in config.py.

See `windows/README.md` for the full Windows troubleshooting guide.

## License

MIT -- do whatever you want with it.

---

Built by [Alex Salinsky](https://www.linkedin.com/in/alexsalinsky/) with Claude.
