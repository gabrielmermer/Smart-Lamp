import RPi.GPIO as GPIO
import spidev
import json
import time
import threading
from neopixel import Adafruit_NeoPixel

# === GPIO Pin Setup ===
BUTTON_ON_OFF = 17
BUTTON_COLOR = 27
BUTTON_MODE = 22
POTENTIOMETER_CHANNEL = 0  # MCP3008 channel for potentiometer

# === LED Strip Setup ===
LED_COUNT = 60  # 60 LEDs in the strip
LED_PIN = 18  # GPIO pin for the LED data line

# === State Variables ===
state = {
    "power": False,
    "color_index": 0,
    "auto_mode": False,
    "brightness": 100
}

colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255)]  # RGB colors for manual control

# === MCP3008 Setup (for potentiometer) ===
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel): #for manual adjustment
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

# === NeoPixel addressable LED strip Setup ===
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, 800000, 10, False, 255)
strip.begin()

# === GPIO Setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setup([BUTTON_ON_OFF, BUTTON_COLOR, BUTTON_MODE], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === Lamp Control ===
def apply_color():
    r, g, b = colors[state["color_index"]]
    brightness = state["brightness"] / 100.0  # normalize to 0-1 range
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, strip.Color(int(r * brightness), int(g * brightness), int(b * brightness)))
    strip.show()

def save_state(): 
    with open("lamp_state.json", "w") as f:
        json.dump(state, f)

def load_state():
    global state
    try:
        with open("lamp_state.json", "r") as f:
            state = json.load(f)
    except FileNotFoundError:
        pass

# === Button Handlers ===
def button_loop():
    prev_on = GPIO.input(BUTTON_ON_OFF)
    prev_color = GPIO.input(BUTTON_COLOR)
    prev_mode = GPIO.input(BUTTON_MODE)
    while True:
        time.sleep(0.1)
        if GPIO.input(BUTTON_ON_OFF) == GPIO.LOW and prev_on == GPIO.HIGH:
            state["power"] = not state["power"]
            apply_color()
        if GPIO.input(BUTTON_COLOR) == GPIO.LOW and prev_color == GPIO.HIGH and not state["auto_mode"]:
            state["color_index"] = (state["color_index"] + 1) % len(colors)
            apply_color()
        if GPIO.input(BUTTON_MODE) == GPIO.LOW and prev_mode == GPIO.HIGH:
            state["auto_mode"] = not state["auto_mode"]
        prev_on = GPIO.input(BUTTON_ON_OFF)
        prev_color = GPIO.input(BUTTON_COLOR)
        prev_mode = GPIO.input(BUTTON_MODE)

# === Auto Mode Thread ===
def auto_mode_loop():
    while True:
        if state["auto_mode"] and state["power"]:
            state["color_index"] = (state["color_index"] + 1) % len(colors)
            apply_color()
            time.sleep(2)  # Speed of cycling
        else:
            time.sleep(0.5)

# === Brightness Control Thread ===
def brightness_loop():
    while True:
        adc_value = read_adc(POTENTIOMETER_CHANNEL)
        state["brightness"] = int((adc_value / 1023) * 100)
        apply_color()
        time.sleep(0.2)

# === Main ===
load_state()
threading.Thread(target=button_loop, daemon=True).start()
threading.Thread(target=brightness_loop, daemon=True).start()
threading.Thread(target=auto_mode_loop, daemon=True).start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    save_state()
    GPIO.cleanup()
