import asyncio
import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakScanner

BTHOME_UUID = "0000fcd2-0000-1000-8000-00805f9b34fb"


def u8(data, i):
    return data[i], i + 1


def i16(data, i, scale=1):
    return struct.unpack_from("<h", data, i)[0] * scale, i + 2


def u16(data, i, scale=1):
    return struct.unpack_from("<H", data, i)[0] * scale, i + 2


def u24(data, i, scale=1):
    val = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16)
    return val * scale, i + 3


def safe_filename_from_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").upper() + ".json"


def decode_bthome(payload: bytes):
    if not payload:
        return None

    info = payload[0]

    encrypted = bool(info & 0x01)
    trigger_based = bool(info & 0x04)
    bthome_version = info >> 5

    result = {
        "bthome_version": bthome_version,
        "encrypted": encrypted,
        "trigger_based": trigger_based,
    }

    if encrypted:
        result["decode_status"] = "encrypted"
        result["note"] = "Encrypted BTHome payload, cannot decode without key"
        return result

    result["decode_status"] = "ok"

    i = 1

    while i < len(payload):
        obj = payload[i]
        i += 1

        try:
            if obj == 0x00:
                val, i = u8(payload, i)
                result["packet_id"] = val

            elif obj == 0x01:
                val, i = u8(payload, i)
                result["battery_percent"] = val

            elif obj == 0x02:
                val, i = i16(payload, i, 0.01)
                result["temperature_c"] = round(val, 2)

            elif obj == 0x03:
                val, i = u16(payload, i, 0.01)
                result["humidity_percent"] = round(val, 2)

            elif obj == 0x05:
                val, i = u24(payload, i, 0.01)
                result["illuminance_lux"] = round(val, 2)

            elif obj == 0x08:
                val, i = u8(payload, i)
                result["moisture_percent"] = val

            elif obj == 0x0c:
                val, i = u16(payload, i, 0.001)
                result["voltage_v"] = round(val, 3)

            elif obj == 0x21:
                val, i = u8(payload, i)
                result["motion"] = bool(val)

            elif obj == 0x2d:
                val, i = u8(payload, i)
                result["window_or_door_open"] = bool(val)

            elif obj == 0x3a:
                val, i = u8(payload, i)
                result["button_event"] = val

            else:
                result["decode_status"] = "partial"
                result["unknown_object"] = f"0x{obj:02x}"
                result["unknown_data_hex"] = payload[i:].hex(" ")
                break

        except (IndexError, struct.error):
            result["decode_status"] = "error"
            result["decode_error"] = f"Truncated data at object 0x{obj:02x}"
            break

    return result


def atomic_write_json(path: Path, data: dict):
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    tmp_path.replace(path)


def callback(device, adv):
    payload = adv.service_data.get(BTHOME_UUID)

    if payload is None:
        return

    decoded = decode_bthome(payload)

    if decoded is None:
        return

    mac = device.address
    name = device.name or adv.local_name or None
    now = datetime.now(timezone.utc).isoformat()

    output = {
        "mac": mac,
        "name": name,
        "rssi": adv.rssi,
        "last_seen_utc": now,
        "source": "bthome_ble",
        "payload": decoded,
        "raw": {
            "service_uuid": BTHOME_UUID,
            "service_data_hex": payload.hex(" "),
        },
    }

    filename = safe_filename_from_mac(mac)
    path = Path.cwd() / filename

    try:
        atomic_write_json(path, output)
    except Exception as e:
        print(f"Write error for {mac}: {e}")


async def main():
    print("BTHome listener started.")
    print(f"Writing JSON files to: {Path.cwd()}")
    print("Press Ctrl+C to stop.")

    scanner = BleakScanner(callback)
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())