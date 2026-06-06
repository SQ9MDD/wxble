#!/usr/bin/env bash
set -e

APP_DIR="/opt/wxble"
SERVICE_FILE="/etc/systemd/system/wxble.service"
USER_NAME="${WXBLE_USER:-pi}"

echo "Installing WXBLE..."

sudo mkdir -p "$APP_DIR/data"

sudo cp wxble.py "$APP_DIR/"
sudo cp requirements.txt "$APP_DIR/"
sudo cp wxble.service "$SERVICE_FILE"

sudo python3 -m venv "$APP_DIR/venv"
sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

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
echo "Data:"
echo "  ls -l $APP_DIR/data/"