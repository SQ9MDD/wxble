#!/usr/bin/env bash
set -e

APP_DIR="/opt/wxble"
SERVICE_FILE="/etc/systemd/system/wxble.service"

echo "Uninstalling WXBLE..."

echo "Stopping service..."
sudo systemctl stop wxble.service || true

echo "Disabling service..."
sudo systemctl disable wxble.service || true

echo "Removing systemd service file..."
sudo rm -f "$SERVICE_FILE"

echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl reset-failed wxble.service || true

echo "Removing application directory..."
sudo rm -rf "$APP_DIR"

echo
echo "WXBLE removed completely."
echo
echo "Removed:"
echo "  $SERVICE_FILE"
echo "  $APP_DIR"