# ESP32 Health Monitor
# For YD-ESP32-S3 N16R8
#
# WiFi credentials in settings.toml:
#   WIFI_SSID = "YourNetwork"
#   WIFI_PASSWORD = "YourPassword"
#
# Robust WiFi connection with exponential backoff and LED feedback

import board
import microcontroller
import neopixel
import os
import supervisor
import time
import wifi

# =============================================================================
# CONFIGURATION
# =============================================================================

DEVICE_NAME = "ESP32-Health"

# WiFi reconnection settings (can override in settings.toml)
DEFAULT_WIFI_RETRY_MIN_SECONDS = 5
DEFAULT_WIFI_RETRY_MAX_SECONDS = 120
DEFAULT_WIFI_OFFLINE_RESET_SECONDS = 15 * 60  # 15 minutes

# =============================================================================
# LED STATE MACHINE
# =============================================================================

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.12, auto_write=False)

# Colors
C_OFF = (0, 0, 0)
C_BLUE = (0, 0, 255)
C_DIM_BLUE = (0, 0, 20)
C_GREEN = (0, 255, 0)
C_YELLOW = (255, 180, 0)
C_RED = (255, 0, 0)

# LED patterns
LED_SOLID = "solid"
LED_BLINK_SLOW = "blink_slow"
LED_BLINK_FAST = "blink_fast"

led_pattern = LED_SOLID
led_color = C_DIM_BLUE
_led_on = True
_led_last_toggle = 0.0
LED_SLOW_PERIOD = 1.5
LED_FAST_PERIOD = 0.25


def led_set_solid(color):
    global led_pattern, led_color, _led_on
    led_pattern = LED_SOLID
    led_color = color
    _led_on = True
    pixel[0] = color
    pixel.show()


def led_set_blink_slow(color):
    global led_pattern, led_color
    led_pattern = LED_BLINK_SLOW
    led_color = color


def led_set_blink_fast(color):
    global led_pattern, led_color
    led_pattern = LED_BLINK_FAST
    led_color = color


def led_flash(color, seconds=0.2):
    pixel[0] = color
    pixel.show()
    time.sleep(seconds)
    pixel[0] = C_OFF
    pixel.show()
    time.sleep(0.05)


def led_update(now):
    global _led_on, _led_last_toggle
    if led_pattern == LED_SOLID:
        return
    period = LED_SLOW_PERIOD if led_pattern == LED_BLINK_SLOW else LED_FAST_PERIOD
    half = period / 2.0
    if now - _led_last_toggle < half:
        return
    _led_last_toggle = now
    _led_on = not _led_on
    pixel[0] = led_color if _led_on else C_OFF
    pixel.show()


def led_state_meaning():
    if led_pattern == LED_SOLID and led_color == C_DIM_BLUE:
        return "Booting"
    if led_pattern == LED_BLINK_SLOW and led_color == C_BLUE:
        return "Connecting to WiFi"
    if led_pattern == LED_SOLID and led_color == C_BLUE:
        return "WiFi connected (brief)"
    if led_pattern == LED_BLINK_SLOW and led_color == C_GREEN:
        return "WiFi OK - Normal operation"
    if led_pattern == LED_BLINK_SLOW and led_color == C_YELLOW:
        return "WiFi disconnected - Retrying"
    if led_pattern == LED_BLINK_FAST and led_color == C_RED:
        return "Error"
    return "Unknown"


# Start with dim blue (booting)
led_set_solid(C_DIM_BLUE)

# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def load_int_from_settings(name, default):
    try:
        raw = os.getenv(name)
        if raw is None:
            return default
        return int(raw)
    except Exception:
        return default


def load_str_from_settings(name):
    try:
        raw = os.getenv(name)
        if raw is None:
            return None
        raw = str(raw).strip()
        return raw if raw else None
    except Exception:
        return None


# Load WiFi credentials
ssid = load_str_from_settings("WIFI_SSID")
password = load_str_from_settings("WIFI_PASSWORD")

# Load retry settings
wifi_retry_min = load_int_from_settings("WIFI_RETRY_MIN_SECONDS", DEFAULT_WIFI_RETRY_MIN_SECONDS)
wifi_retry_max = load_int_from_settings("WIFI_RETRY_MAX_SECONDS", DEFAULT_WIFI_RETRY_MAX_SECONDS)
wifi_offline_reset = load_int_from_settings("WIFI_OFFLINE_RESET_SECONDS", DEFAULT_WIFI_OFFLINE_RESET_SECONDS)

# =============================================================================
# WIFI CONNECTION MANAGER
# =============================================================================

wifi_last_connected = False
wifi_last_ip = "0.0.0.0"
wifi_reconnect_attempts = 0
wifi_next_attempt_time = 0.0
wifi_offline_since = None


def wifi_connected():
    try:
        return bool(wifi.radio.connected)
    except Exception:
        return False


def wifi_current_ip():
    try:
        return str(wifi.radio.ipv4_address)
    except Exception:
        return "0.0.0.0"


def wifi_schedule_next_attempt(now):
    global wifi_next_attempt_time
    delay = wifi_retry_min * (2 ** max(0, wifi_reconnect_attempts - 1))
    if delay > wifi_retry_max:
        delay = wifi_retry_max
    wifi_next_attempt_time = now + delay
    print(f"WiFi: next reconnect in {int(delay)}s")


def wifi_try_connect(now, reason):
    global wifi_reconnect_attempts, wifi_last_connected, wifi_last_ip
    global wifi_offline_since

    led_set_blink_slow(C_BLUE)
    wifi_reconnect_attempts += 1
    print(f"WiFi: connect attempt #{wifi_reconnect_attempts} ({reason})")

    try:
        wifi.radio.connect(ssid, password)
        ip = wifi_current_ip()
        wifi_last_connected = True
        wifi_last_ip = ip
        wifi_reconnect_attempts = 0
        wifi_offline_since = None

        led_set_solid(C_BLUE)
        time.sleep(0.3)
        print(f"WiFi: connected! IP={ip}")
        led_set_blink_slow(C_GREEN)
        return True

    except Exception as e:
        wifi_last_connected = False
        if wifi_offline_since is None:
            wifi_offline_since = now
        print(f"WiFi: connect failed ({e})")
        led_set_blink_slow(C_YELLOW)
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    global wifi_last_connected, wifi_last_ip, wifi_offline_since
    global wifi_reconnect_attempts, wifi_next_attempt_time

    print("\n" + "=" * 50)
    print("ESP32 Health Monitor")
    print("=" * 50)

    # Check for credentials
    if not ssid or not password:
        print("ERROR: Missing WIFI_SSID / WIFI_PASSWORD in settings.toml")
        print("")
        print("Edit settings.toml on CIRCUITPY drive:")
        print('  WIFI_SSID = "YourNetwork"')
        print('  WIFI_PASSWORD = "YourPassword"')
        led_set_blink_fast(C_RED)
        while True:
            led_update(time.monotonic())
            time.sleep(0.01)

    print(f"WiFi SSID: {ssid}")
    print(f"Retry: min={wifi_retry_min}s max={wifi_retry_max}s reset={wifi_offline_reset}s")

    # Initial connection
    now = time.monotonic()
    wifi_try_connect(now, "startup")

    print("")
    print("LED Status Guide:")
    print("  Slow BLUE blink  = Connecting to WiFi")
    print("  Slow GREEN blink = Connected, normal operation")
    print("  Slow YELLOW blink = Disconnected, retrying")
    print("  Fast RED blink   = Error (check settings.toml)")
    print("")

    # Main loop
    while True:
        now = time.monotonic()

        connected = wifi_connected()

        if connected:
            # Currently connected
            if not wifi_last_connected:
                # Just reconnected
                wifi_last_connected = True
                wifi_last_ip = wifi_current_ip()
                wifi_offline_since = None
                wifi_reconnect_attempts = 0
                print(f"WiFi: reconnected! IP={wifi_last_ip}")
                led_set_blink_slow(C_GREEN)
            else:
                # Check for IP change
                current_ip = wifi_current_ip()
                if current_ip != wifi_last_ip and current_ip != "0.0.0.0":
                    wifi_last_ip = current_ip
                    print(f"WiFi: IP changed to {current_ip}")

        else:
            # Currently disconnected
            if wifi_last_connected:
                # Just disconnected
                wifi_last_connected = False
                wifi_offline_since = now
                wifi_reconnect_attempts = 0
                wifi_next_attempt_time = now
                print("WiFi: disconnected")
                led_set_blink_slow(C_YELLOW)

            # Check if offline too long - reset
            if wifi_offline_since is not None:
                offline_duration = now - wifi_offline_since
                if offline_duration > wifi_offline_reset:
                    print(f"WiFi: offline too long ({int(offline_duration)}s), resetting...")
                    led_set_blink_fast(C_RED)
                    time.sleep(0.5)
                    supervisor.reload()

            # Try to reconnect
            if now >= wifi_next_attempt_time:
                ok = wifi_try_connect(now, "reconnect")
                if not ok:
                    wifi_schedule_next_attempt(now)

        # Update LED
        led_update(now)

        # Small delay
        time.sleep(0.01)


if __name__ == "__main__":
    main()
