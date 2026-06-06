#!/usr/bin/env bash
set -e

APP_DIR="/opt/wxble"
SERVICE_FILE="/etc/systemd/system/wxble.service"

echo "Uninstalling WXBLE..."

sudo systemctl stop wxble.service || true
sudo systemctl disable wxble.service || true
sudo rm -f "$SERVICE_FILE"
sudo systemctl daemon-reload

echo
echo "WXBLE service removed."
echo
echo "Data and application files were left untouched:"
echo "  $APP_DIR"
echo
echo "To remove everything:"
echo "  sudo rm -rf $APP_DIR"