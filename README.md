# ESP32-BLE - Health Monitor with BLE Provisioning

CircuitPython health monitoring device for YD-ESP32-S3 N16R8 with BLE WiFi provisioning.

## Features

- **BLE WiFi Provisioning** - Configure WiFi credentials via phone (no hardcoding)
- **Local Data Storage** - Buffer measurements when offline
- **Cloud Sync** - Upload data via HTTPS when WiFi available
- **Visual Feedback** - NeoPixel status indicators

## Hardware

- **Board:** [YD-ESP32-S3 N16R8](https://circuitpython.org/board/yd_esp32_s3_n16r8/)
- **CircuitPython:** 10.0.3

## Quick Start

1. **First boot:** Device enters BLE provisioning mode (NeoPixel pulses blue)
2. **Configure WiFi:** Use nRF Connect app to send SSID/password
3. **Normal operation:** Device connects to WiFi, collects and syncs data

## Re-provisioning

Hold the **BOOT button** while powering on to re-enter BLE provisioning mode.

## Documentation

See [DESIGN.md](DESIGN.md) for detailed architecture and design decisions.

## Update History

| Date | Description |
|------|-------------|
| 2026-01-12 | Initial project setup with design document |
