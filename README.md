# Awesome Home Assistant Recipes

Practical recipes for devices that Home Assistant does **not** support out of the box — written from
real work on real hardware, with the dead ends included.

🇷🇺 [Читать по-русски](README.ru.md)

📖 The same recipes as a website, with search: <https://serg-kovalev.github.io/awesome-home-assistant-recipes/>

## Why this exists

The vendor cloud for my heat recovery unit exposes exactly **1** data point: on/off.
The device itself has **13** — 3 fan speeds, 3 ventilation modes, a night mode,
3 humidity thresholds, and 2 sensors. Everything the app can do, the cloud API hides.

The manufacturer either didn't bother or couldn't. So I did it myself: full local control, a proper
`fan` entity with speeds and presets, and voice control through a smart speaker.

These recipes are the reusable parts of that work.

## Recipes

| # | Recipe | What you get |
|---|---|---|
| 1 | [Mapping data points of an "unsupported" Tuya device](docs/en/001-tuya-dp-mapping.md) | The full DP list when the cloud shows 1 |
| 2 | [A separate Wi-Fi segment for IoT, and how to reach it](docs/en/002-iot-network-segment.md) | Isolation that doesn't break local control |
| 3 | [A template `fan` on top of 11 boolean data points](docs/en/003-template-fan.md) | One clean entity instead of a pile of switches |
| 4 | [Exporting to Yandex Smart Home (Alice)](docs/en/004-yandex-smart-home.md) | Voice control, and what simply cannot be exported |
| 5 | [Zigbee bindings: a wireless switch that works without the hub](docs/en/005-zigbee-bindings.md) | Instant response, works while HA reboots |

## The device that started it

**Ventini HRV-60** — a through-wall heat recovery unit, Tuya/SmartLife, Wi-Fi, protocol 3.4.
Cloud category `xfj`, product name "Heat Recovery Ventilator", listed by the official Tuya integration
as **unsupported**.

Also covered: **Yandex YNDX-00535**, a two-gang wireless Zigbee switch, where the useful trick is
binding it straight to relays instead of routing every press through automations.

## Examples

- [`examples/ventini-hrv/templates/ventini_hrv.yaml`](examples/ventini-hrv/templates/ventini_hrv.yaml) —
  the template `fan` + `select`, ready to adapt
- [`examples/ventini-hrv/yandex_smart_home.yaml`](examples/ventini-hrv/yandex_smart_home.yaml) —
  export config for Alice
- [`examples/tools/watch_dp.py`](examples/tools/watch_dp.py) —
  polls a Tuya device and prints only what changed; this is what makes DP mapping a ten-minute job

## A note on secrets

Every value in this repository is a placeholder. Local keys, device IDs, cloud account IDs, MAC
addresses and real network ranges are **not** here, and the files that hold them
(`devices.json`, `tinytuya.json`, `snapshot.json`) are in `.gitignore`.

If you follow these recipes, remember that a Tuya `local_key` is a full control credential for that
device. Treat it like a password: never paste it into an issue, a forum post, or a screenshot.

## Contributing

Recipes in `docs/` were tested on hardware I own. Contributed recipes go to
[`docs/community/`](docs/community/README.md) and are marked as not verified by the maintainer — I have
no way to reproduce them.

If you want to add one, [CONTRIBUTING](CONTRIBUTING.md) explains what evidence a recipe needs. See also
the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

MIT — see [LICENSE](LICENSE).
