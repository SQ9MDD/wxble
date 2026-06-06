#!/usr/bin/env python3

import asyncio
import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bleak import BleakScanner

BTHOME_UUID = "0000fcd2-0000-1000-8000-00805f9b34fb"

META_FIELDS = {
    "bthome_version",
    "encrypted",
    "trigger_based",
    "decode_status",
    "note",
    "decode_error",
    "unknown_object",
    "unknown_data_hex",
    "raw",
    "info",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def u8(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return data[i] * scale, i + 1


def i8(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return struct.unpack_from("<b", data, i)[0] * scale, i + 1


def u16(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return struct.unpack_from("<H", data, i)[0] * scale, i + 2


def i16(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return struct.unpack_from("<h", data, i)[0] * scale, i + 2


def u24(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    val = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16)
    return val * scale, i + 3


def i24(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    val = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16)

    if val & 0x800000:
        val -= 0x1000000

    return val * scale, i + 3


def u32(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return struct.unpack_from("<I", data, i)[0] * scale, i + 4


def i32(data: bytes, i: int, scale: float = 1) -> tuple[float, int]:
    return struct.unpack_from("<i", data, i)[0] * scale, i + 4


def safe_filename_from_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").upper() + ".json"


def clean_number(value: float, digits: int = 2) -> int | float:
    rounded = round(value, digits)

    if isinstance(rounded, float) and rounded.is_integer():
        return int(rounded)

    return rounded


def decode_event_value(event_id: int) -> str | int:
    events = {
        0x00: "none",
        0x01: "press",
        0x02: "double_press",
        0x03: "triple_press",
        0x04: "long_press",
        0x05: "long_double_press",
        0x06: "long_triple_press",
        0x80: "hold_press",
        0xFE: "hold_press",
    }

    return events.get(event_id, event_id)


def decode_bthome(payload: bytes) -> dict[str, Any] | None:
    if not payload:
        return None

    info = payload[0]

    encrypted = bool(info & 0x01)
    trigger_based = bool(info & 0x04)
    bthome_version = info >> 5

    result: dict[str, Any] = {
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
            # Packet ID
            if obj == 0x00:
                val, i = u8(payload, i)
                result["packet_id"] = int(val)

            # Battery
            elif obj == 0x01:
                val, i = u8(payload, i)
                result["battery_percent"] = int(val)

            # Temperature, sint16, factor 0.01
            elif obj == 0x02:
                val, i = i16(payload, i, 0.01)
                result["temperature_c"] = clean_number(val, 2)

            # Humidity, uint16, factor 0.01
            elif obj == 0x03:
                val, i = u16(payload, i, 0.01)
                result["humidity_percent"] = clean_number(val, 2)

            # Pressure, uint24, factor 0.01
            elif obj == 0x04:
                val, i = u24(payload, i, 0.01)
                result["pressure_hpa"] = clean_number(val, 2)

            # Illuminance, uint24, factor 0.01
            elif obj == 0x05:
                val, i = u24(payload, i, 0.01)
                result["illuminance_lux"] = clean_number(val, 2)

            # Mass, uint16, factor 0.01
            elif obj == 0x06:
                val, i = u16(payload, i, 0.01)
                result["mass_kg"] = clean_number(val, 2)

            # Mass, uint16, factor 0.01
            elif obj == 0x07:
                val, i = u16(payload, i, 0.01)
                result["mass_lb"] = clean_number(val, 2)

            # Dew point, sint16, factor 0.01
            elif obj == 0x08:
                val, i = i16(payload, i, 0.01)
                result["dewpoint_c"] = clean_number(val, 2)

            # Count, uint8
            elif obj == 0x09:
                val, i = u8(payload, i)
                result["count"] = int(val)

            # Energy, uint24, factor 0.001
            elif obj == 0x0A:
                val, i = u24(payload, i, 0.001)
                result["energy_kwh"] = clean_number(val, 3)

            # Power, uint24, factor 0.01
            elif obj == 0x0B:
                val, i = u24(payload, i, 0.01)
                result["power_w"] = clean_number(val, 2)

            # Voltage, uint16, factor 0.001
            elif obj == 0x0C:
                val, i = u16(payload, i, 0.001)
                result["voltage_v"] = clean_number(val, 3)

            # PM2.5, uint16
            elif obj == 0x0D:
                val, i = u16(payload, i)
                result["pm25_ugm3"] = int(val)

            # PM10, uint16
            elif obj == 0x0E:
                val, i = u16(payload, i)
                result["pm10_ugm3"] = int(val)

            # Binary generic
            elif obj == 0x0F:
                val, i = u8(payload, i)
                result["generic_boolean"] = bool(val)

            # Power state
            elif obj == 0x10:
                val, i = u8(payload, i)
                result["power_state"] = bool(val)

            # Opening
            elif obj == 0x11:
                val, i = u8(payload, i)
                result["opening"] = bool(val)

            # CO2
            elif obj == 0x12:
                val, i = u16(payload, i)
                result["co2_ppm"] = int(val)

            # TVOC
            elif obj == 0x13:
                val, i = u16(payload, i)
                result["tvoc_ugm3"] = int(val)

            # Moisture, uint16, factor 0.01
            elif obj == 0x14:
                val, i = u16(payload, i, 0.01)
                result["moisture_percent"] = clean_number(val, 2)

            # Battery low
            elif obj == 0x15:
                val, i = u8(payload, i)
                result["battery_low"] = bool(val)

            # Battery charging
            elif obj == 0x16:
                val, i = u8(payload, i)
                result["battery_charging"] = bool(val)

            # Carbon monoxide binary
            elif obj == 0x17:
                val, i = u8(payload, i)
                result["carbon_monoxide"] = bool(val)

            # Cold
            elif obj == 0x18:
                val, i = u8(payload, i)
                result["cold"] = bool(val)

            # Connectivity
            elif obj == 0x19:
                val, i = u8(payload, i)
                result["connectivity"] = bool(val)

            # Door
            elif obj == 0x1A:
                val, i = u8(payload, i)
                result["door_open"] = bool(val)

            # Garage door
            elif obj == 0x1B:
                val, i = u8(payload, i)
                result["garage_door_open"] = bool(val)

            # Gas
            elif obj == 0x1C:
                val, i = u8(payload, i)
                result["gas"] = bool(val)

            # Heat
            elif obj == 0x1D:
                val, i = u8(payload, i)
                result["heat"] = bool(val)

            # Light binary
            elif obj == 0x1E:
                val, i = u8(payload, i)
                result["light"] = bool(val)

            # Lock
            elif obj == 0x1F:
                val, i = u8(payload, i)
                result["lock"] = bool(val)

            # Moisture binary
            elif obj == 0x20:
                val, i = u8(payload, i)
                result["moisture"] = bool(val)

            # Motion
            elif obj == 0x21:
                val, i = u8(payload, i)
                result["motion"] = bool(val)

            # Moving
            elif obj == 0x22:
                val, i = u8(payload, i)
                result["moving"] = bool(val)

            # Occupancy
            elif obj == 0x23:
                val, i = u8(payload, i)
                result["occupancy"] = bool(val)

            # Plug
            elif obj == 0x24:
                val, i = u8(payload, i)
                result["plug"] = bool(val)

            # Presence
            elif obj == 0x25:
                val, i = u8(payload, i)
                result["presence"] = bool(val)

            # Problem
            elif obj == 0x26:
                val, i = u8(payload, i)
                result["problem"] = bool(val)

            # Running
            elif obj == 0x27:
                val, i = u8(payload, i)
                result["running"] = bool(val)

            # Safety
            elif obj == 0x28:
                val, i = u8(payload, i)
                result["safety"] = bool(val)

            # Smoke
            elif obj == 0x29:
                val, i = u8(payload, i)
                result["smoke"] = bool(val)

            # Sound
            elif obj == 0x2A:
                val, i = u8(payload, i)
                result["sound"] = bool(val)

            # Tamper
            elif obj == 0x2B:
                val, i = u8(payload, i)
                result["tamper"] = bool(val)

            # Vibration
            elif obj == 0x2C:
                val, i = u8(payload, i)
                result["vibration"] = bool(val)

            # Window
            elif obj == 0x2D:
                val, i = u8(payload, i)
                result["window_open"] = bool(val)

            # Humidity, uint8
            elif obj == 0x2E:
                val, i = u8(payload, i)
                result["humidity_percent"] = int(val)

            # Moisture, uint8
            elif obj == 0x2F:
                val, i = u8(payload, i)
                result["moisture_percent"] = int(val)

            # Event
            elif obj == 0x3A:
                val, i = u8(payload, i)
                result["button_event"] = decode_event_value(int(val))

            # Count, uint16
            elif obj == 0x3D:
                val, i = u16(payload, i)
                result["count"] = int(val)

            # Count, uint32
            elif obj == 0x3E:
                val, i = u32(payload, i)
                result["count"] = int(val)

            # Rotation, sint16, factor 0.1
            elif obj == 0x3F:
                val, i = i16(payload, i, 0.1)
                result["rotation_degrees"] = clean_number(val, 1)

            # Distance, uint16, factor 0.001
            elif obj == 0x40:
                val, i = u16(payload, i, 0.001)
                result["distance_m"] = clean_number(val, 3)

            # Distance, uint16, factor 0.1
            elif obj == 0x41:
                val, i = u16(payload, i, 0.1)
                result["distance_mm"] = clean_number(val, 1)

            # Duration, uint24, factor 0.001
            elif obj == 0x42:
                val, i = u24(payload, i, 0.001)
                result["duration_s"] = clean_number(val, 3)

            # Current, uint16, factor 0.001
            elif obj == 0x43:
                val, i = u16(payload, i, 0.001)
                result["current_a"] = clean_number(val, 3)

            # Speed, uint16, factor 0.01
            elif obj == 0x44:
                val, i = u16(payload, i, 0.01)
                result["speed_ms"] = clean_number(val, 2)

            # Temperature, sint16, factor 0.1
            elif obj == 0x45:
                val, i = i16(payload, i, 0.1)
                result["temperature_c"] = clean_number(val, 1)

            # UV index, uint8, factor 0.1
            elif obj == 0x46:
                val, i = u8(payload, i, 0.1)
                result["uv_index"] = clean_number(val, 1)

            # Volume, uint16, factor 0.1
            elif obj == 0x47:
                val, i = u16(payload, i, 0.1)
                result["volume_l"] = clean_number(val, 1)

            # Volume, uint16, factor 0.001
            elif obj == 0x48:
                val, i = u16(payload, i, 0.001)
                result["volume_m3"] = clean_number(val, 3)

            # Volume flow rate, uint16, factor 0.001
            elif obj == 0x49:
                val, i = u16(payload, i, 0.001)
                result["volume_flow_rate_m3h"] = clean_number(val, 3)

            # Voltage, uint16, factor 0.1
            elif obj == 0x4A:
                val, i = u16(payload, i, 0.1)
                result["voltage_v"] = clean_number(val, 1)

            # Gas volume, uint24, factor 0.001
            elif obj == 0x4B:
                val, i = u24(payload, i, 0.001)
                result["gas_volume_m3"] = clean_number(val, 3)

            # Gas volume, uint32, factor 0.001
            elif obj == 0x4C:
                val, i = u32(payload, i, 0.001)
                result["gas_volume_m3"] = clean_number(val, 3)

            # Energy, uint32, factor 0.001
            elif obj == 0x4D:
                val, i = u32(payload, i, 0.001)
                result["energy_kwh"] = clean_number(val, 3)

            # Volume, uint32, factor 0.001
            elif obj == 0x4E:
                val, i = u32(payload, i, 0.001)
                result["volume_m3"] = clean_number(val, 3)

            # Water, uint32, factor 0.001
            elif obj == 0x4F:
                val, i = u32(payload, i, 0.001)
                result["water_m3"] = clean_number(val, 3)

            # Timestamp, uint32
            elif obj == 0x50:
                val, i = u32(payload, i)
                result["timestamp"] = int(val)

            # Acceleration, uint16, factor 0.001
            elif obj == 0x51:
                val, i = u16(payload, i, 0.001)
                result["acceleration_ms2"] = clean_number(val, 3)

            # Gyroscope, uint16, factor 0.001
            elif obj == 0x52:
                val, i = u16(payload, i, 0.001)
                result["gyroscope_dps"] = clean_number(val, 3)

            # Text, length uint8 + bytes
            elif obj == 0x53:
                length, i = u8(payload, i)
                length = int(length)
                text_bytes = payload[i:i + length]
                i += length
                result["text"] = text_bytes.decode("utf-8", errors="replace")

            # Raw packet, length uint8 + bytes
            elif obj == 0x54:
                length, i = u8(payload, i)
                length = int(length)
                raw_packet = payload[i:i + length]
                i += length
                result["raw_packet_hex"] = raw_packet.hex(" ")

            # Volume storage, uint32, factor 0.001
            elif obj == 0x55:
                val, i = u32(payload, i, 0.001)
                result["volume_storage_m3"] = clean_number(val, 3)

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


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    tmp_path.replace(path)


def load_existing_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return {}


def extract_sensor_values(decoded: dict[str, Any]) -> dict[str, Any]:
    values = {}

    for key, value in decoded.items():
        if key in META_FIELDS:
            continue

        values[key] = value

    return values


def merge_sensor_state(
    path: Path,
    mac: str,
    name: str | None,
    rssi: int | None,
    decoded: dict[str, Any],
    raw_hex: str,
) -> None:
    current_time = now_utc()
    existing = load_existing_json(path)

    old_payload = existing.get("payload", {})
    if not isinstance(old_payload, dict):
        old_payload = {}

    old_field_updated = existing.get("field_updated_utc", {})
    if not isinstance(old_field_updated, dict):
        old_field_updated = {}

    new_values = extract_sensor_values(decoded)

    merged_payload = dict(old_payload)
    field_updated = dict(old_field_updated)

    for key, value in new_values.items():
        merged_payload[key] = value
        field_updated[key] = current_time

    output = {
        "mac": mac,
        "name": name or existing.get("name"),
        "rssi": rssi,
        "first_seen_utc": existing.get("first_seen_utc", current_time),
        "last_seen_utc": current_time,
        "last_update_utc": current_time,
        "source": "bthome_ble",
        "status": {
            "bthome_version": decoded.get("bthome_version"),
            "encrypted": decoded.get("encrypted"),
            "trigger_based": decoded.get("trigger_based"),
            "decode_status": decoded.get("decode_status"),
        },
        "payload": merged_payload,
        "field_updated_utc": field_updated,
        "last_frame": {
            "payload": new_values,
            "status": {
                "decode_status": decoded.get("decode_status"),
                "unknown_object": decoded.get("unknown_object"),
                "unknown_data_hex": decoded.get("unknown_data_hex"),
                "decode_error": decoded.get("decode_error"),
                "note": decoded.get("note"),
            },
            "raw_service_data_hex": raw_hex,
        },
        "raw": {
            "service_uuid": BTHOME_UUID,
            "service_data_hex": raw_hex,
        },
    }

    atomic_write_json(path, output)


def callback(device, adv) -> None:
    payload = adv.service_data.get(BTHOME_UUID)

    if payload is None:
        return

    decoded = decode_bthome(payload)

    if decoded is None:
        return

    mac = device.address
    name = device.name or adv.local_name or None
    rssi = adv.rssi
    raw_hex = payload.hex(" ")

    filename = safe_filename_from_mac(mac)
    path = Path.cwd() / filename

    try:
        merge_sensor_state(
            path=path,
            mac=mac,
            name=name,
            rssi=rssi,
            decoded=decoded,
            raw_hex=raw_hex,
        )
    except Exception as e:
        print(f"Write error for {mac}: {e}")


async def main() -> None:
    print("WXBLE BTHome listener started.")
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