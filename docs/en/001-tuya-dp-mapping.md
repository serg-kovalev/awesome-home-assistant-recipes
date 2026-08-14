# Mapping data points of an "unsupported" Tuya device

[Русская версия](../ru/001-tuya-dp-mapping.md)

## The symptom

The official Tuya integration shows the device as `Heat Recovery Ventilator (unsupported)` and creates
no entities. The integration diagnostics explain why:

```json
"category": "xfj",
"status": [{"code": "switch", "value": false}],
"local_strategy": {
  "1": {"status_code": "switch", "config_item": {"valueType": "Boolean"}}
}
```

1 data point. Meanwhile the SmartLife app shows 3 ventilation modes, 3 fan speeds, a night
mode, 3 humidity modes and 2 sensors for the same unit.

So `unsupported` doesn't mean "broken", it means "no profile for this model". But the bigger point is
this: **the cloud schema is trimmed by the vendor**. There is nothing to discover in it — it really
does contain a single point.

If the app can do more than the cloud API, you have to go local.

## What you need

- the device `local_key`, obtained through the Tuya IoT Platform;
- [`tinytuya`](https://github.com/jasonacox/tinytuya);
- network access to the device on TCP/6668 (see [recipe 2](002-iot-network-segment.md)).

## Step 1. Get the local key

1. Create a cloud project at [iot.tuya.com](https://iot.tuya.com). **Pick the same data center as your
   account**, otherwise the device list comes back empty. You can read it off the endpoint in the Tuya
   integration diagnostics: `apigw.tuyaeu.com` means Central Europe.
2. In the project: **Devices → Link App Account**, then scan the QR code in SmartLife.
3. Copy `Access ID` and `Access Secret` from the Overview tab.

Then, in a working directory:

```bash
python3 -m venv venv
./venv/bin/pip install tinytuya
./venv/bin/python -m tinytuya wizard
```

The wizard asks for the access ID, the secret, any device ID and the region (`eu`), then writes
`devices.json` with the local keys of every device on the account.

> **If `pip install tinytuya` fails while building `cryptography`** and asks for Rust, don't install
> Rust. tinytuya works with a different crypto backend:
>
> ```bash
> ./venv/bin/pip install --no-deps tinytuya
> ./venv/bin/pip install requests colorama pycryptodome
> ```
>
> pip will still complain about the missing `cryptography` dependency. Ignore it, everything works.

Once `devices.json` exists you can delete `tinytuya.json` — it holds the access secret and is only
needed for the cloud call.

## Step 2. Get the full DP list

```bash
./venv/bin/python -m tinytuya scan
```

A plain scan listens for broadcasts. If the device sits in another subnet it will not show up, which
is expected — see [recipe 2](002-iot-network-segment.md). To probe a subnet directly:

```bash
./venv/bin/python -m tinytuya scan -force 192.168.30.0/24
```

`-force` only works when `devices.json` with keys is already there.

The result is the whole point of the exercise:

```
DPS: {'1': False, '101': False, '102': False, '103': False, '104': False,
      '105': False, '106': False, '107': False, '108': 311, '109': 331,
      '111': False, '112': False, '113': False}
```

13 points instead of 1.

## Step 3. Work out what each point does

The values tell you nothing — 11 `False` all look the same. You need an experiment: change one
control in the app, see which point moved.

Polling by hand is tedious, so use [`watch_dp.py`](https://github.com/serg-kovalev/awesome-home-assistant-recipes/blob/main/examples/tools/watch_dp.py). It polls every
2 seconds and prints **only changes**:

```
[12:02:38] START: {"1": false, "101": false, ..., "108": 309, "109": 281}
[12:03:41] DP 1: False -> True
[12:03:43] DP 113: False -> True
[12:03:45] DP 101: False -> True
```

The routine:

1. Start the watcher.
2. Change **one** thing in the app.
3. Wait 5 seconds so the state lands in its own snapshot.
4. Repeat for every control.

3 things that will save you an hour:

**The pause matters.** Polling is every 2 seconds. Without a pause 2 actions merge into one
snapshot and you can't tell which did what.

**Numeric points drift on their own.** Sensors jitter by one unit and flood the log. Filter them out
while reading, and get the scale by comparing with the app: `389` when the app says `38.9 %` means a
factor of 0.1.

**Don't trust the cloud event log.** Device Logs on iot.tuya.com show point names (`Speed one`,
`Humidity Two`, `Sleep Mode`) and it's tempting to line them up by timestamp. Don't. Between a
`Publish` event (the app's command) and a `Report` event (the device confirming) there can be a full
minute, so matching by time produces false pairs. I "proved" that way that a single point was both
speed two and humidity two.

The reliable method is to write values yourself and watch what lights up in the app. The app is your
dictionary of names:

```python
import tinytuya
dev = tinytuya.Device("<DEVICE_ID>", "192.168.30.16", "<LOCAL_KEY>", version=3.4)
dev.set_value(104, True)   # what turned on in the app?
```

## The result

| DP | Function | Type |
|---|---|---|
| 1 | power | bool |
| 101, 102, 103 | speed low / medium / high | bool, mutually exclusive |
| 104 | night mode | bool |
| 105, 106, 107 | humidity threshold low / medium / high | bool, mutually exclusive |
| 108 | humidity, ×10 | int |
| 109 | temperature, ×10 | int |
| 111, 112, 113 | supply / exhaust / recuperation | bool, mutually exclusive |

## Firmware quirks worth checking on your device

While mapping the points I hit 4 behaviours that aren't in any documentation. Look for the same
ones on your hardware — they decide how you write the integration.

**A point that ignores `False`.** Writing `105 = False` does nothing: no error, a normal reply, the
value stays `True`. The only way to switch humidity control off is to re-send the active ventilation
mode (`113 = True` while it already is `True`). A plain switch entity won't work for such a point.

**A redundant write is not a no-op.** Sending a value that is already set has a side effect — that is
exactly how humidity gets cleared. Practical rule: **don't confirm state you don't need to change**.
If the device is already on, don't send "on" again; you don't know what the firmware does with it.

**Reporting lag.** After a write the device can report the old value for 5 seconds or more. I took
that for "the command didn't work" twice and nearly threw away a working solution. Check results after
10 seconds, not 2.

**Mode commands are ignored while powered off.** The unit silently drops a mode change if
`DP 1 = False`. Your scripts have to power it on first, wait, and only then set the mode.
