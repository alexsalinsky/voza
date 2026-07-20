#!/bin/bash
clear
echo ""
echo "  +----------------------------------------------+"
echo "  :  Voza -- Setup for Mac                        :"
echo "  :  by Alex Salinsky                             :"
echo "  +----------------------------------------------+"
echo ""

VOZA_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$VOZA_DIR"

# --- Check for Python 3 and install if missing ---
if ! command -v python3 &> /dev/null; then
    echo "  Python is needed but not installed."
    echo "  Installing it now (this may take a few minutes)..."
    echo ""

    # Check if Homebrew is installed, install it if not
    if ! command -v brew &> /dev/null; then
        echo "  Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for this session (Apple Silicon vs Intel)
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        echo ""
    fi

    echo "  Installing Python..."
    brew install python3
    echo ""

    # Verify it worked
    if ! command -v python3 &> /dev/null; then
        echo "  Something went wrong installing Python."
        echo "  Try installing manually from: https://www.python.org/downloads/"
        echo ""
        read -p "  Press Enter to close." dummy
        exit 1
    fi
fi

echo "  Found Python: $(python3 --version)"
echo ""
echo "  Installing Voza dependencies..."
echo "  (this may take a minute the first time)"
echo ""
pip3 install -r requirements.txt
echo ""

# --- Make the launcher double-clickable ---
chmod +x start-voza.command

# --- Add to Login Items (auto-start on login) ---
echo "  Setting Voza to start automatically on login..."
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.alexsalinsky.voza.plist"
PYTHON_PATH="$(which python3)"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.alexsalinsky.voza</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${VOZA_DIR}/dictation.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${VOZA_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${VOZA_DIR}/voza.log</string>
    <key>StandardErrorPath</key>
    <string>${VOZA_DIR}/voza.log</string>
</dict>
</plist>
PLISTEOF

echo "  Done! Voza will start automatically when you log in."
echo ""
echo "  +----------------------------------------------+"
echo "  :  Setup complete!                              :"
echo "  +----------------------------------------------+"
echo ""
echo "  Press Cmd+Shift+Space to start talking"
echo "  Press Cmd+Shift+Space again to stop"
echo "  Your words appear wherever your cursor is"
echo ""
echo "  IMPORTANT: macOS will ask for some permissions."
echo "  Say YES to all of these:"
echo "    - Microphone access (so Voza can hear you)"
echo "    - Accessibility access (so the hotkey works everywhere)"
echo ""
echo "  If the hotkey doesn't work after setup:"
echo "    System Settings -> Privacy & Security -> Accessibility"
echo "    Find Terminal and make sure it's checked"
echo ""
echo "  To stop auto-starting on login, delete this file:"
echo "    ${PLIST_FILE}"
echo ""
echo "  Launching Voza now..."
echo ""
python3 dictation.py
