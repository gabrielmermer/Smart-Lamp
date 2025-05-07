import RPi.GPIO as GPIO
import spidev
import json
import time
import threading

# === GPIO Pin Setup ===
BUTTON_ON_OFF = 17
BUTTON_COLOR = 27
BUTTON_MODE = 22
LED_PINS = {'R': 18, 'G': 23, 'B': 24}

# === State Variables ===
state = {
    "power": False,
    "color_index": 0,
    "auto_mode": False,
    "brightness": 100
}
colors = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,0,1), (0,1,1), (1,1,1)]

# === MCP3008 Setup ===
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    adc = spi.xfer2([1, (8+channel)<<4, 0])
    return ((adc[1]&3) << 8) + adc[2]

# === GPIO Setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setup([BUTTON_ON_OFF, BUTTON_COLOR, BUTTON_MODE], GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

pwm = {color: GPIO.PWM(pin, 1000) for color, pin in LED_PINS.items()}
for p in pwm.values():
    p.start(0)

# === Lamp Control ===
def apply_color():
    r, g, b = colors[state["color_index"]]
    brightness = state["brightness"]
    pwm['R'].ChangeDutyCycle(r * brightness)
    pwm['G'].ChangeDutyCycle(g * brightness)
    pwm['B'].ChangeDutyCycle(b * brightness)

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
        adc_value = read_adc(0)
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
