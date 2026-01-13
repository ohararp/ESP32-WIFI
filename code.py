# ESP32 Health Monitor
# For YD-ESP32-S3 N16R8
#
# WiFi credentials: Edit settings.toml on the CIRCUITPY drive
#   CIRCUITPY_WIFI_SSID = "YourNetwork"
#   CIRCUITPY_WIFI_PASSWORD = "YourPassword"

import board
import microcontroller
import neopixel
import os
import time
import wifi

# =============================================================================
# CONFIGURATION
# =============================================================================

DEVICE_NAME = "ESP32-Health"

# =============================================================================
# NEOPIXEL STATUS
# =============================================================================

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.3)

COLOR_YELLOW = (255, 150, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_PURPLE = (128, 0, 128)

class StatusLED:
    @staticmethod
    def solid(color):
        pixel[0] = color

    @staticmethod
    def pulse(color, duration=1.0, steps=20):
        r, g, b = color
        for i in range(steps):
            factor = i / steps
            pixel[0] = (int(r * factor), int(g * factor), int(b * factor))
            time.sleep(duration / (steps * 2))
        for i in range(steps, 0, -1):
            factor = i / steps
            pixel[0] = (int(r * factor), int(g * factor), int(b * factor))
            time.sleep(duration / (steps * 2))

    @staticmethod
    def flash(color, times=3, on_time=0.1, off_time=0.1):
        for _ in range(times):
            pixel[0] = color
            time.sleep(on_time)
            pixel[0] = (0, 0, 0)
            time.sleep(off_time)

# =============================================================================
# WIFI CONNECTION
# =============================================================================

def connect_wifi():
    """Connect to WiFi using credentials from settings.toml"""
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

    if not ssid:
        print("ERROR: No WiFi credentials found!")
        print("")
        print("Edit settings.toml on the CIRCUITPY drive:")
        print('  CIRCUITPY_WIFI_SSID = "YourNetwork"')
        print('  CIRCUITPY_WIFI_PASSWORD = "YourPassword"')
        print("")
        return False

    print(f"Connecting to WiFi: {ssid}")
    StatusLED.pulse(COLOR_YELLOW, duration=0.5)

    try:
        wifi.radio.connect(ssid, password)
        print(f"Connected! IP: {wifi.radio.ipv4_address}")
        StatusLED.solid(COLOR_GREEN)
        return True
    except Exception as e:
        print(f"WiFi connection failed: {e}")
        print("")
        print("Check your settings.toml credentials")
        StatusLED.flash(COLOR_RED, times=3)
        return False

# =============================================================================
# NORMAL MODE (Phase 2 placeholder)
# =============================================================================

def run_normal_mode():
    """Main operation loop - placeholder for health monitoring"""
    print("Running in normal mode...")
    print("(Phase 2: Add sensor reading and cloud sync here)")

    while True:
        StatusLED.solid(COLOR_GREEN)
        time.sleep(2)
        StatusLED.pulse(COLOR_GREEN, duration=1.0)
        print(f"WiFi: {wifi.radio.ipv4_address}")
        time.sleep(5)

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 50)
    print("ESP32 Health Monitor")
    print("=" * 50)

    if connect_wifi():
        run_normal_mode()
    else:
        # No credentials or connection failed - pulse purple
        print("Waiting for valid settings.toml...")
        while True:
            StatusLED.pulse(COLOR_PURPLE, duration=2.0)

if __name__ == "__main__":
    main()
