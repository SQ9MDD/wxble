# WXBLE

WXBLE is a small Linux service that listens for BTHome Bluetooth Low Energy sensor advertisements and writes decoded sensor data to local JSON files.

It is designed for simple file-based integrations. Instead of using a database, MQTT broker or web API, WXBLE keeps the latest decoded state of each detected sensor in a separate JSON file.

Example output path:

```text
/opt/wxble/data/AABBCCDDEEFF.json
```

Each file is named after the sensor MAC address and contains the most recent decoded payload, signal strength, timestamp and raw BTHome service data.

## What it does

WXBLE:

* passively scans for Bluetooth Low Energy advertisements
* detects BTHome service data using UUID `0xFCD2`
* decodes common BTHome sensor values such as temperature, humidity, battery level, voltage, motion and contact state
* writes one JSON file per detected sensor
* updates files atomically, so other applications can safely read them
* runs as a lightweight `systemd` service
* works well on Raspberry Pi and other Linux systems with Bluetooth LE support

## What it does not do

WXBLE intentionally does not provide:

* a web interface
* a database
* an MQTT broker/client
* device pairing
* active polling of sensors
* cloud connectivity

It only listens for BLE advertisements and writes the latest decoded data to files.

## Example JSON output

```json
{
  "mac": "10:B4:1D:1A:6C:22",
  "name": "AHT10",
  "rssi": -92,
  "first_seen_utc": "2026-06-06T21:36:52.395804+00:00",
  "last_seen_utc": "2026-06-07T05:16:30.664575+00:00",
  "last_update_utc": "2026-06-07T05:16:30.664575+00:00",
  "source": "bthome_ble",
  "status": {
    "bthome_version": 2,
    "encrypted": false,
    "trigger_based": false,
    "decode_status": "ok"
  },
  "payload": {
    "battery_percent": 22,
    "temperature_c": 20.68,
    "voltage_v": 3.532,
    "humidity_percent": 56,
    "count": 618603
  },
  "field_updated_utc": {
    "battery_percent": "2026-06-07T05:16:30.664575+00:00",
    "temperature_c": "2026-06-07T05:16:30.664575+00:00",
    "voltage_v": "2026-06-07T05:16:30.664575+00:00",
    "humidity_percent": "2026-06-07T05:16:30.664575+00:00",
    "count": "2026-06-07T05:16:30.664575+00:00"
  },
  "last_frame": {
    "payload": {
      "battery_percent": 22,
      "temperature_c": 20.68,
      "voltage_v": 3.532,
      "humidity_percent": 56,
      "count": 618603
    },
    "status": {
      "decode_status": "ok",
      "unknown_object": null,
      "unknown_data_hex": null,
      "decode_error": null,
      "note": null
    },
    "raw_service_data_hex": "40 01 16 02 14 08 0c cc 0d 2e 38 3e 6b 70 09 00"
  },
  "raw": {
    "service_uuid": "0000fcd2-0000-1000-8000-00805f9b34fb",
    "service_data_hex": "40 01 16 02 14 08 0c cc 0d 2e 38 3e 6b 70 09 00"
  }
}
```


## Installation

Install WXBLE directly from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/SQ9MDD/wxble/main/install.sh | bash
```

The installer will:

* create `/opt/wxble`
* create `/opt/wxble/data`
* download `wxble.py`, `requirements.txt` and `wxble.service`
* create a Python virtual environment
* install required Python packages
* install and enable the systemd service

Start the service:

```bash
sudo systemctl start wxble
```

Check service status:

```bash
systemctl status wxble --no-pager
```

Watch logs:

```bash
journalctl -u wxble -f
```

Check generated JSON files:

```bash
ls -l /opt/wxble/data/
```

Each detected BTHome sensor will be written as a separate JSON file:

```text
/opt/wxble/data/AABBCCDDEEFF.json
```

## Install with a custom service user

By default, the installer uses the current user or `pi`, depending on the install script configuration.

To force a specific service user:

```bash
curl -fsSL https://raw.githubusercontent.com/SQ9MDD/wxble/main/install.sh | WXBLE_USER=pi bash
```

Example with another user:

```bash
curl -fsSL https://raw.githubusercontent.com/SQ9MDD/wxble/main/install.sh | WXBLE_USER=aprsbox bash
```

## Uninstallation

Remove WXBLE completely:

```bash
curl -fsSL https://raw.githubusercontent.com/SQ9MDD/wxble/main/uninstall.sh | bash
```

The uninstall script removes:

```text
/etc/systemd/system/wxble.service
/opt/wxble
```

This also removes the generated JSON data files.

## Manual verification

After installation, you can verify that the Python environment sees `bleak`:

```bash
/opt/wxble/venv/bin/python -c "import bleak; print(bleak.__version__)"
```

You can also run WXBLE manually for testing:

```bash
cd /opt/wxble/data
/opt/wxble/venv/bin/python /opt/wxble/wxble.py
```

## License

WXBLE is released under the MIT License.