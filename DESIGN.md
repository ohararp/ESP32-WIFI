# ESP32-BLE Health Monitor - Design Document

## Overview

A health monitoring device that:
- Takes periodic analog measurements
- Stores data locally for offline operation
- Syncs to cloud via WiFi when available
- Uses BLE for WiFi credential provisioning (no hardcoded passwords)

## Hardware

- **Board:** [YD-ESP32-S3 N16R8](https://circuitpython.org/board/yd_esp32_s3_n16r8/)
- **Firmware:** CircuitPython 10.0.3
- **Features Used:**
  - BLE for WiFi provisioning
  - WiFi for data sync
  - NeoPixel for status indication
  - Analog inputs for health sensors
  - BOOT button (GPIO0) for provisioning trigger

## Architecture

```
┌─────────────┐     BLE      ┌─────────────┐     WiFi     ┌─────────────┐
│   iPhone    │ ──────────── │   ESP32     │ ──────────── │   Cloud     │
│   App       │  credentials │   Device    │    data      │   Service   │
└─────────────┘              └─────────────┘              └─────────────┘
                                   │
                             ┌─────┴─────┐
                             │  Sensors  │
                             │  (Analog) │
                             └───────────┘
```

## Boot Flow

```
                         BOOT
                           │
                           ▼
                ┌─────────────────────┐
                │ Check NVM byte 0    │
                │ (credentials flag)  │
                └──────────┬──────────┘
                           │
          ┌────────────────┴────────────────┐
          ▼ NO (0x00)                       ▼ YES (0x01)
┌───────────────────┐             ┌─────────────────────┐
│ BLE Provisioning  │             │ BOOT button held?   │
│ Mode              │             └──────────┬──────────┘
│ (first time)      │                  │           │
└───────────────────┘             NO ──┘           └── YES
                                   ▼                    ▼
                          ┌─────────────────┐  ┌─────────────────┐
                          │ Normal Mode     │  │ BLE Provisioning│
                          │ (WiFi + Sync)   │  │ Mode (re-config)│
                          └─────────────────┘  └─────────────────┘
```

## Data Flow

### Provisioning Mode (BLE)
```
iPhone (nRF Connect)          ESP32
       │                        │
       │──── Scan ─────────────▶│ Advertising "ESP32-Health"
       │◀─── Found ─────────────│
       │──── Connect ──────────▶│
       │──── Write SSID ───────▶│ Save to NVM
       │──── Write Password ───▶│ Save to NVM
       │                        │ Set configured flag
       │                        │──── Connect to WiFi
       │◀─── Notify "OK" ───────│
       │──── Disconnect ───────▶│
       │                        │──── Reboot to normal mode
```

### Normal Mode (WiFi)
```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN LOOP                              │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Read Sensors │───▶│ Store Local  │───▶│ Check WiFi   │  │
│  │ (periodic)   │    │ (buffer)     │    │ Available?   │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                              ┌───────────────────┴────┐     │
│                              ▼ YES                   ▼ NO   │
│                     ┌─────────────────┐      ┌──────────┐   │
│                     │ Sync to Cloud   │      │ Continue │   │
│                     │ (HTTPS POST)    │      │ Buffering│   │
│                     │ Delete on ACK   │      └──────────┘   │
│                     └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Storage Design

### Non-Volatile Memory (NVM) Layout

Using `microcontroller.nvm` (8KB available):

| Byte Offset | Size | Purpose |
|-------------|------|---------|
| 0 | 1 | Configured flag (0x01 = credentials saved) |
| 1-32 | 32 | WiFi SSID (null-terminated, padded) |
| 33-96 | 64 | WiFi Password (null-terminated, padded) |
| 97-128 | 32 | Device ID / UUID (for cloud identification) |
| 129+ | ~7KB | Reserved for future use |

### Local Data Storage

Health measurements buffered on filesystem:

```
/data/
├── 2026-01-12.csv
├── 2026-01-13.csv
└── ...

CSV Format:
timestamp,sensor1,sensor2,sensor3
1705072800,123,456,789
1705072860,124,455,790
```

## Protocol Decisions

### Why HTTPS REST (not MQTT)?

| Factor | HTTPS REST | MQTT |
|--------|------------|------|
| Simplicity | Simple request/response | Needs broker setup |
| Offline handling | Easy batch upload | More complex |
| CircuitPython support | Excellent (`adafruit_requests`) | Available but more setup |
| Security | TLS built-in | Needs MQTTS config |
| Firewall friendly | Port 443 usually open | Port 1883/8883 may be blocked |

**Decision:** Start with HTTPS REST, can add MQTT later if needed for real-time features.

### Cloud Service Options

| Service | Free Tier | Recommendation |
|---------|-----------|----------------|
| Adafruit IO | 30 pts/min | Good for prototyping |
| Custom server | Self-hosted | Full control |
| AWS IoT | 12 months free | Enterprise scale |

## BLE Service Design

### Service UUID
`12345678-1234-5678-1234-56789abcdef0` (custom)

### Characteristics

| Name | UUID | Properties | Purpose |
|------|------|------------|---------|
| SSID | `...def1` | Write | Receive WiFi network name |
| Password | `...def2` | Write | Receive WiFi password |
| Status | `...def3` | Read, Notify | Connection status feedback |
| Command | `...def4` | Write | Control commands (reset, clear, etc.) |

### Status Codes (returned via Status characteristic)

| Code | Meaning |
|------|---------|
| 0x00 | Idle, waiting for credentials |
| 0x01 | Credentials received, connecting... |
| 0x02 | WiFi connected successfully |
| 0x03 | WiFi connection failed |
| 0x04 | Credentials saved, rebooting |

## NeoPixel Status Indicators

| Pattern | Color | Meaning |
|---------|-------|---------|
| Pulsing | Blue | BLE provisioning mode |
| Pulsing | Yellow | Connecting to WiFi |
| Solid | Green | WiFi connected, normal operation |
| Brief flash | White | Data synced to cloud |
| Pulsing | Red | Error (check serial for details) |
| Rainbow | Multi | Sensor reading in progress |

## iPhone Provisioning

### Phase 1: Generic BLE App (Prototyping)
- Use **nRF Connect** (free on App Store)
- Manual entry of SSID/password
- Good for development and testing

### Phase 2: Custom App (Production)
- Native Swift app with CoreBluetooth
- Auto-detect available WiFi networks
- Branded UI, integrated health dashboard
- App Store distribution

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Credentials in NVM | Not visible as file (unlike settings.toml) |
| BLE sniffing | Pairing required, short provisioning window |
| Data in transit | HTTPS/TLS encryption |
| Device identification | Unique device ID in NVM |
| Cloud authentication | API key stored in NVM |

## File Structure

```
ESP32-BLE/
├── code.py              # Main application
├── boot.py              # Early boot config (filesystem mount)
├── lib/                 # CircuitPython libraries
│   ├── adafruit_ble/
│   ├── adafruit_requests.mpy
│   └── ...
├── data/                # Local measurement buffer
├── DESIGN.md            # This document
├── README.md            # Project overview
└── .gitignore
```

## Development Phases

### Phase 1: BLE Provisioning
- [ ] NVM read/write helper functions
- [ ] BLE service with SSID/Password characteristics
- [ ] Boot button detection
- [ ] NeoPixel status indicators
- [ ] Test with nRF Connect

### Phase 2: WiFi + Local Storage
- [ ] WiFi connection using NVM credentials
- [ ] Local CSV data storage
- [ ] Analog sensor reading
- [ ] Periodic measurement loop

### Phase 3: Cloud Sync
- [ ] HTTPS POST to cloud service
- [ ] Batch upload buffered data
- [ ] Delete local data after confirmed sync
- [ ] Error handling and retry logic

### Phase 4: Polish
- [ ] Custom iPhone app (optional)
- [ ] Power optimization
- [ ] OTA updates
- [ ] Production hardening

## References

- [CircuitPython BLE Documentation](https://learn.adafruit.com/introduction-to-bluetooth-low-energy)
- [YD-ESP32-S3 Board](https://circuitpython.org/board/yd_esp32_s3_n16r8/)
- [Adafruit IO](https://io.adafruit.com/)
- [nRF Connect App](https://apps.apple.com/app/nrf-connect-for-mobile/id1054362403)
