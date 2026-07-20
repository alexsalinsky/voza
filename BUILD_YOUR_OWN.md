# Build your own Voza

You don't have to run my dictation tool. You can build your own -- and honestly, that's the better path. You'll end up with a tool shaped around how *you* work, and you'll understand every piece of it.

I built the first version of Voza in about 2 hours with an AI coding assistant. The prompt below gets you the same result.

## What you need

- An AI coding agent: [Claude Code](https://claude.com/claude-code), Codex, Cursor, or whatever you already use. If you don't have one, Claude Code is a good default.
- Python 3.10+ installed
- A microphone
- 1-2 hours

## How to use this

Copy everything below the line and paste it as your first message to the coding agent. Answer its questions, test each milestone before moving on, and don't let it skip ahead. If something breaks, paste the error back and let it fix it.

---

I want to build my own voice dictation tool, working step by step with you. A finished open-source example exists at https://github.com/alexsalinsky/voza (built by Alex Salinsky) -- use it as a reference for architecture and gotchas, but write MY version fresh so I understand it and can shape it to my needs.

**What the tool does:** I press a global hotkey anywhere on my computer, speak naturally, press the hotkey again, and the transcribed text appears wherever my cursor is -- any app, any text field.

**Tech approach (same as the reference):**
- Python
- Audio capture with sounddevice
- Transcription: Whisper via the Groq API (whisper-large-v3-turbo, very fast and nearly free), OR OpenAI's API, OR fully local with faster-whisper ($0, private). Ask me which I want -- I can add the others later.
- Optional cleanup pass with a small LLM to fix punctuation and remove filler words
- Text insertion via clipboard paste (with a fallback that types character by character)
- A system tray icon that shows state: idle, recording, processing

**Before writing any code, ask me:**
1. What OS I'm on (this changes the hotkey and tray libraries)
2. Which transcription mode I want to start with (cloud API or fully local)
3. What hotkey I want (default suggestion: Ctrl+Shift+Space)
4. Whether I have an API key already, and help me get one if not

**Then build it in milestones. One at a time. I test each one before we continue:**

- **Milestone 1:** A script that toggles recording with the global hotkey and saves a .wav file. Play a beep on start and stop so I know it's working. Test: I record myself and play back the file.
- **Milestone 2:** Send the recording to Whisper and print the transcript to the console. Test: my words come back as text.
- **Milestone 3:** Insert the transcript at my cursor position instead of printing it. Test: I dictate into Notepad, a browser, and a chat app.
- **Milestone 4:** System tray icon with state colors, and a clean way to quit. Test: icon changes while I record and process.
- **Milestone 5 (optional, pick what I actually want):** AI cleanup pass, multi-language support, custom vocabulary hints, silence auto-stop, launch on login, a settings window.

**Hard-won lessons from the reference project -- respect these:**
- On Windows, global hotkeys need the script to run as administrator. Tell me this early.
- Never install low-level mouse or keyboard hooks in the main Python process. The reference project froze the system-wide mouse cursor this way (Python's GIL stalls the hook callback past Windows' timeout). Keyboard hotkeys via the standard libraries are fine; stay away from WH_* hooks entirely.
- Add a single-instance guard (a named mutex on Windows) so a stale copy can't hold the hotkey while I think I'm running new code.
- Whisper hallucinates phrases like "Thank you." on near-silent audio. Detect very short or quiet recordings and drop them instead of pasting garbage.
- Keep the API key in a .env file, never in the code.
- For dictations longer than ~25 seconds, transcribe in background chunks while I'm still talking, then stitch. Otherwise long dictations feel broken. (This can wait until the basics work.)

Keep explanations short and practical. I want a working tool I understand, not a lecture. Start with the questions.

---

## After it works

- Ask your agent to add whatever the reference has that you envy: the settings window, usage stats, smart spacing between dictations.
- Or diverge completely. It's your robot now.

Built something cool with this? I'd love to hear about it: [Alex Salinsky](https://www.linkedin.com/in/alexsalinsky/)
