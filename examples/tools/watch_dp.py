#!/usr/bin/env python3
"""Watch a Tuya device and print only the data points that changed.

This is the tool that turns DP mapping into a ten-minute job: you flip one control
in the vendor app, and the log tells you which point moved.

Usage:
    pip install --no-deps tinytuya
    pip install requests colorama pycryptodome
    python3 -m tinytuya wizard          # writes devices.json with local keys

    python3 watch_dp.py <DEVICE_ID> [--ip 192.168.30.16] [--interval 2]
                        [--devices devices.json] [--hide 108,109]

Notes:
    * devices.json holds local keys. Never commit it, never paste it anywhere.
    * Numeric sensors drift on their own and flood the log — hide them with --hide.
    * The device may report a stale value for several seconds after a write.
"""

import argparse
import datetime
import json
import sys
import time

import tinytuya


def load_device(devices_file, device_id, ip_override):
    try:
        with open(devices_file, encoding="utf-8") as fh:
            devices = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"{devices_file} not found — run: python3 -m tinytuya wizard")

    for entry in devices:
        if entry.get("id") == device_id:
            return {
                "id": entry["id"],
                "ip": ip_override or entry.get("ip"),
                "key": entry["key"],
                "version": float(entry.get("version") or 3.3),
                "name": entry.get("name", device_id),
            }
    sys.exit(f"device {device_id} not found in {devices_file}")


def stamp():
    return datetime.datetime.now().strftime("%H:%M:%S")


def sort_key(item):
    dp = item[0]
    return (0, int(dp)) if dp.isdigit() else (1, dp)


def main():
    parser = argparse.ArgumentParser(description="Print Tuya data point changes")
    parser.add_argument("device_id")
    parser.add_argument("--ip", help="override the address from devices.json")
    parser.add_argument("--devices", default="devices.json")
    parser.add_argument("--interval", type=float, default=2.0, help="poll interval, seconds")
    parser.add_argument("--hide", default="", help="comma separated DPs to ignore, e.g. 108,109")
    args = parser.parse_args()

    hidden = {dp.strip() for dp in args.hide.split(",") if dp.strip()}
    info = load_device(args.devices, args.device_id, args.ip)

    if not info["ip"]:
        sys.exit("no address: pass --ip, the device was probably discovered without one")

    device = tinytuya.Device(info["id"], info["ip"], info["key"], version=info["version"])
    device.set_socketPersistent(True)
    device.set_socketTimeout(5)

    print(f"[{stamp()}] watching {info['name']} at {info['ip']} (protocol {info['version']})", flush=True)

    previous = None
    try:
        while True:
            try:
                status = device.status()
                points = status.get("dps") if isinstance(status, dict) else None

                if points:
                    if previous is None:
                        print(f"[{stamp()}] START: {json.dumps(points, sort_keys=True)}", flush=True)
                        previous = dict(points)
                    else:
                        changes = {
                            dp: (previous.get(dp), value)
                            for dp, value in points.items()
                            if previous.get(dp) != value and dp not in hidden
                        }
                        if changes:
                            text = " | ".join(
                                f"DP {dp}: {old} -> {new}"
                                for dp, (old, new) in sorted(changes.items(), key=sort_key)
                            )
                            print(f"[{stamp()}] {text}", flush=True)
                        # merge instead of replace: the device often answers with a partial set
                        previous.update(points)
                elif status and "Error" in str(status):
                    print(f"[{stamp()}] error: {status}", flush=True)
                    time.sleep(3)

            except Exception as exc:  # noqa: BLE001 — keep watching whatever happens
                print(f"[{stamp()}] {type(exc).__name__}: {exc}", flush=True)
                time.sleep(3)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\n[{stamp()}] stopped")


if __name__ == "__main__":
    main()
