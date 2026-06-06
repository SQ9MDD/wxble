#!/usr/bin/env bash
set -e

APP_DIR="/opt/wxble"
SERVICE_FILE="/etc/systemd/system/wxble.service"
REPO_RAW="${WXBLE_REPO_RAW:-https://raw.githubusercontent.com/SQ9MDD/wxble/main}"
USER_NAME="${WXBLE_USER:-${SUDO_USER:-$USER}}"

echo "Installing WXBLE..."
echo "Repository: $REPO_RAW"
echo "Install dir: $APP_DIR"
echo "Service user: $USER_NAME"

sudo mkdir -p "$APP_DIR/data"

echo "Downloading files..."
sudo curl -fsSL "$REPO_RAW/wxble.py" -o "$APP_DIR/wxble.py"
sudo curl -fsSL "$REPO_RAW/requirements.txt" -o "$APP_DIR/requirements.txt"
sudo curl -fsSL "$REPO_RAW/wxble.service" -o "$SERVICE_FILE"

echo "Creating virtual environment..."
sudo python3 -m venv "$APP_DIR/venv"

echo "Installing Python requirements..."
sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "Setting permissions..."
sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

echo "Configuring systemd..."
sudo systemctl daemon-reload
sudo systemctl enable wxble.service

echo
echo "WXBLE installed."
echo
echo "Start service:"
echo "  sudo systemctl start wxble"
echo
echo "Check status:"
echo "  systemctl status wxble --no-pager"
echo
echo "View logs:"
echo "  journalctl -u wxble -f"
echo
echo "JSON data directory:"
echo "  $APP_DIR/data/"