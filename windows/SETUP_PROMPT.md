# Voza Setup Prompt

Copy everything below the line and paste it into Claude (claude.ai) or ChatGPT. The AI will walk you through setting up Voza step by step.

---

I need help setting up Voza, a free voice dictation tool for Windows made by Alex Salinsky. Walk me through it step by step. I'm not a developer, so be patient and explain things clearly.

Here's what Voza does: I press Ctrl+Shift+Space, speak naturally, press the hotkey again, and the transcribed text appears wherever my cursor is. It works in any app.

Here's what I need to do:

**Step 1: Install Python**
- I need Python 3.10 or newer from https://www.python.org/downloads/
- IMPORTANT: During install, I must check the box that says "Add Python to PATH"
- After installing, help me verify it works by opening Command Prompt and typing: python --version

**Step 2: Get the Voza files**
- Download the code from https://github.com/alexsalinsky/voza (green "Code" button > Download ZIP), or Alex may have shared a zip with me directly
- I only need the `windows` folder from the download
- I need to extract/save it somewhere I'll remember, like C:\voza or my Documents folder

**Step 3: Install dependencies**
- Open Command Prompt
- cd into the voza folder
- Run: pip install -r requirements.txt
- If I want fully local transcription (free, no API key needed), also run: pip install -r requirements-local.txt
- Also run: pip install anthropic
- Help me troubleshoot if anything fails

**Step 4: Generate tray icons**
- In the same folder, run: python generate_icons.py
- This creates the system tray icons Voza needs

**Step 5: Set up API key (optional but recommended)**
- Best option: a Groq API key from https://console.groq.com/keys (fastest, about $0.35/month for normal use)
- Alternative: an OpenAI API key from https://platform.openai.com/api-keys (about $2/month)
- Copy the file called .env.example to .env
- Open .env in Notepad and replace the placeholder with my real key
- If I skip this step, Voza still works using local transcription (free but lower quality)

**Step 6: Run Voza**
- Right-click start.bat and select "Run as administrator" (admin is needed for global hotkeys)
- OR open Command Prompt as admin, cd to the folder, and run: python dictation.py
- A small microphone icon should appear in my system tray (bottom-right near the clock)

**Step 7: Test it**
- Click into any text field (Notepad, a browser, Slack, whatever)
- Press Ctrl+Shift+Space (I should hear a beep)
- Say something
- Press Ctrl+Shift+Space again (another beep)
- My words should appear as text after a moment

**If something goes wrong, here are common issues:**
- "Hotkey not working" = I need to run as administrator
- "No microphone found" = Check Windows Settings > Sound > Input
- "Text not appearing" = Some admin apps block pasting. Try running Voza as admin too
- "ModuleNotFoundError" = A Python package didn't install. Run pip install again for that specific package
- If I get a 429 error about quota, my API credits ran out. Add credits or switch to local mode

**Settings I can change** (in config.py, open with Notepad):
- HOTKEY = change the dictation hotkey
- ENABLE_CLEANUP = True/False to toggle AI text cleanup
- LOCAL_WHISPER_MODEL = "base" (fast) or "small" or "medium" (better quality, slower)
- LANGUAGE = "auto", "en", "es", etc.

Please walk me through these steps one at a time. Ask me what OS I'm on, whether I already have Python, and if I have a Groq or OpenAI API key. Then guide me through each step, waiting for me to confirm before moving on.
