# ESP32-WIFI Development Session Notes

## Session Date: 2026-01-13

## Summary
Developed WiFi provisioning for ESP32-S3 Health Monitor device.

## What We Tried

### 1. BLE Provisioning (abandoned)
- Attempted using `adafruit_ble` with custom UUIDs
- Tried Nordic UART Service UUIDs
- **Problem:** LightBlue and nRF Connect apps only showed hex input, not text
- **Conclusion:** BLE provisioning too complex for simple credential entry

### 2. WiFi AP Captive Portal (abandoned)
- Created AP mode with web form at 192.168.4.1
- **Problem:** Phone wouldn't route HTTP traffic to the AP (iOS/Android aggressively avoid no-internet WiFi)
- **Conclusion:** Captive portal unreliable on modern phones

### 3. settings.toml (current solution)
- Simple file-based configuration via USB
- User edits `settings.toml` on CIRCUITPY drive
- **Works perfectly** - no app required, universal compatibility

## Current Implementation

### WiFi Configuration
Edit `settings.toml` on CIRCUITPY drive:
```toml
WIFI_SSID = "YourNetwork"
WIFI_PASSWORD = "YourPassword"
```

### Features
- **Robust WiFi connection** with exponential backoff (5s → 120s)
- **Auto-reconnect** on disconnect
- **Auto-reset** after 15 minutes offline
- **LED state machine** (non-blocking blinks)

### LED Status Guide
| Pattern | Color | Meaning |
|---------|-------|---------|
| Slow blink | GREEN | Connected, normal operation |
| Slow blink | BLUE | Connecting to WiFi |
| Slow blink | YELLOW | Disconnected, retrying |
| Fast blink | RED | Error (check settings.toml) |

## Files
- `code.py` - Main application with robust WiFi
- `code_wifi_rtc_webserver.py` - Reference code (not committed)
- `DESIGN.md` - Original design document
- `settings.toml` - WiFi credentials (on device, not in repo)

## Next Steps (Phase 2+)
- [ ] Add sensor reading
- [ ] Local data storage (CSV)
- [ ] Cloud sync (HTTPS)
- [ ] Web dashboard

## Git History
```
0a6bc7f Add robust WiFi connection with exponential backoff
cb51cbd Add WiFi provisioning via settings.toml
943b927 Initial project setup with design document
```

## Repository
https://github.com/ohararp/ESP32-WIFI
