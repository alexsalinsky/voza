VOZA -- Voice to text, your way.
By Alex Salinsky
macOS version

================================
SETUP (one time)
================================

1. Double-click "setup-voza.command"
2. If macOS says it can't be opened, right-click it and choose Open
3. It will install everything automatically
4. Say YES when macOS asks for Microphone and Accessibility permissions


================================
HOW TO USE
================================

1. Double-click "start-voza.command" to launch

2. Press Cmd+Shift+Space to start talking

3. Press Cmd+Shift+Space again to stop

4. Your words appear wherever your cursor is

That's it! Voza runs in fully local mode by default -- free, private,
nothing leaves your computer.


================================
WANT BETTER ACCURACY? (optional)
================================

You can connect to OpenAI's cloud service for better transcription.
Costs about $0.006 per minute of speech (~$2/month typical use).

1. Go to: https://platform.openai.com/api-keys
2. Create an account and get an API key
3. In this folder, copy .env.example to .env
4. Open .env in TextEdit and replace the placeholder with your key
5. Restart Voza
6. Click the menu bar icon and toggle "Transcription" to "API (cloud)"


================================
SETTINGS
================================

Click the Voza icon in the menu bar to open settings.
From there you can toggle transcription mode, AI cleanup,
language, mute audio, and change hotkeys.

For advanced settings, edit config.py in any text editor.


Learn more: https://www.linkedin.com/in/alexsalinsky/
