#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${WXBLE_APP_DIR:-/opt/wxble}"
SERVICE_FILE="/etc/systemd/system/wxble.service"
REPO_RAW="${WXBLE_REPO_RAW:-https://raw.githubusercontent.com/SQ9MDD/wxble/main}"

# Determine target service user.
# Priority:
# 1. WXBLE_USER explicitly provided by the installer caller
# 2. SUDO_USER when install.sh is run with sudo
# 3. logname as fallback
# 4. current USER as last fallback
USER_NAME="${WXBLE_USER:-${SUDO_USER:-$(logname 2>/dev/null || echo "${USER:-}")}}"

if [ -z "$USER_NAME" ] || [ "$USER_NAME" = "root" ]; then
    echo "ERROR: Cannot determine non-root service user."
    echo "Run installer with sudo from the target user account, for example:"
    echo "  sudo ./install.sh"
    echo
    echo "Or specify user explicitly:"
    echo "  sudo WXBLE_USER=rysiek ./install.sh"
    exit 1
fi

if ! id "$USER_NAME" >/dev/null 2>&1; then
    echo "ERROR: User '$USER_NAME' does not exist."
    echo "Specify existing user with WXBLE_USER, for example:"
    echo "  sudo WXBLE_USER=rysiek ./install.sh"
    exit 1
fi

echo "Installing WXBLE..."
echo "Repository: $REPO_RAW"
echo "Install dir: $APP_DIR"
echo "Service user: $USER_NAME"

echo "Creating directories..."
sudo mkdir -p "$APP_DIR/data"

echo "Downloading files..."
sudo curl -fsSL "$REPO_RAW/wxble.py" -o "$APP_DIR/wxble.py"
sudo curl -fsSL "$REPO_RAW/requirements.txt" -o "$APP_DIR/requirements.txt"

echo "Creating virtual environment..."
sudo python3 -m venv "$APP_DIR/venv"

echo "Installing Python requirements..."
sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "Setting permissions..."
sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

echo "Configuring systemd..."
sudo tee "$SERVICE_FILE" >/dev/null <<EOF_SERVICE
[Unit]
Description=WXBLE BTHome listener
After=bluetooth.service dbus.service
Requires=bluetooth.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/wxble.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF_SERVICE

sudo systemctl daemon-reload
sudo systemctl enable wxble.service

echo
echo "WXBLE installed."
echo
echo "Start:"
echo "  sudo systemctl start wxble"
echo
echo "Status:"
echo "  systemctl status wxble --no-pager"
echo
echo "Logs:"
echo "  journalctl -u wxble -f"
echo
echo "Data:"
echo "  ls -l $APP_DIR/data/"
echo
echo "Service user:"
echo "  $USER_NAME"
