#!/usr/bin/env bash
set -e

echo "Uninstalling WXBLE..."

sudo systemctl stop wxble.service || true
sudo systemctl disable wxble.service || true
sudo rm -f /etc/systemd/system/wxble.service
sudo systemctl daemon-reload

echo
echo "WXBLE service removed."
echo "Data directory was left untouched:"
echo "  /opt/wxble"
echo
echo "To remove all files:"
echo "  sudo rm -rf /opt/wxble"