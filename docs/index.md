# Awesome Home Assistant Recipes

Recipes for devices that Home Assistant does not support out of the box. Written from real work on
real hardware, dead ends included.

The vendor cloud for my heat recovery unit exposes 1 data point: on/off. The device itself has
13. Everything the phone app can do, the cloud API hides. The manufacturer either didn't bother
or couldn't, so I did it myself — full local control, a proper `fan` entity with speeds and presets,
and voice control through a smart speaker.

## English

1. [Mapping data points of an "unsupported" Tuya device](en/001-tuya-dp-mapping.md)
2. [A separate Wi-Fi segment for IoT, and how to reach it](en/002-iot-network-segment.md)
3. [A template fan on top of 11 boolean data points](en/003-template-fan.md)
4. [Exporting to Yandex Smart Home](en/004-yandex-smart-home.md)
5. [Zigbee bindings: a wireless switch that works without the hub](en/005-zigbee-bindings.md)
6. [Alerts that keep nagging until you acknowledge them](en/006-alerts.md)

## Русский

1. [Карта точек данных «неподдерживаемого» Tuya-устройства](ru/001-tuya-dp-mapping.md)
2. [Отдельный Wi-Fi-сегмент для IoT и как до него дотянуться](ru/002-iot-network-segment.md)
3. [Шаблонный fan поверх 11 булевых точек](ru/003-template-fan.md)
4. [Экспорт в Умный дом Яндекса](ru/004-yandex-smart-home.md)
5. [Zigbee-биндинги: выключатель, который работает без хаба](ru/005-zigbee-bindings.md)
6. [Тревоги, которые повторяются, пока их не подтвердишь](ru/006-alerts.md)

Contributed recipes live in [Community](community/README.md) and are marked as not verified.

## Hardware covered

**Ventini HRV-60** — through-wall heat recovery unit, Tuya/SmartLife, Wi-Fi, protocol 3.4, cloud
category `xfj`, listed as unsupported by the official Tuya integration.

**Yandex YNDX-00535** — two-gang wireless Zigbee switch, bound directly to relays instead of going
through automations.

**Zigbee smoke detectors** — battery powered, report once every few hours at best, which is what the
alerting recipe had to be built around.

## Secrets

Every value here is a placeholder. Local keys, device IDs, account IDs, MAC addresses and real network
ranges are not in this repository. A Tuya `local_key` is a full control credential — treat it like a
password.
