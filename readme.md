# WXBLE

WXBLE is a lightweight BTHome BLE listener for Raspberry Pi and Linux systems.

It listens for BTHome Bluetooth Low Energy advertising packets and writes decoded sensor data into per-device JSON files.

Each detected sensor is saved as:

```text
/opt/wxble/data/AABBCCDDEEFF.json