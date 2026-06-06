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
