"""
Hardware control module for Smart Lamp.
Handles GPIO operations, LED control, buttons, and potentiometer.
"""

import time
import threading
from typing import Callable, Optional, Tuple, List
from dataclasses import dataclass

try:
    import RPi.GPIO as GPIO
    import spidev
    from rpi_ws281x import PixelStrip, Color
    RASPBERRY_PI_AVAILABLE = True
except ImportError:
    print("Warning: Raspberry Pi libraries not available. Running in simulation mode.")
    RASPBERRY_PI_AVAILABLE = False
    
    # Mock classes for development on non-Pi systems
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        OUT = "OUT"
        PUD_UP = "PUD_UP"
        PUD_DOWN = "PUD_DOWN"
        HIGH = 1
        LOW = 0
        RISING = "RISING"
        FALLING = "FALLING"
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def output(pin, value): pass
        @staticmethod
        def input(pin): return 0
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def cleanup(): pass
        @staticmethod
        def PWM(pin, frequency): return MockPWM()
    
    class MockPWM:
        def start(self, duty_cycle): pass
        def ChangeDutyCycle(self, duty_cycle): pass
        def stop(self): pass
    
    class MockSpiDev:
        def open(self, bus, device): pass
        def xfer2(self, data): return [0, 0, 0]
        def close(self): pass
    
    class MockPixelStrip:
        def __init__(self, count, pin): pass
        def begin(self): pass
        def setPixelColor(self, n, color): pass
        def show(self): pass
        def getBrightness(self): return 255
        def setBrightness(self, brightness): pass
    
    def Color(r, g, b): return (r << 16) | (g << 8) | b
    
    GPIO = MockGPIO()
    spidev = type('MockSpiDev', (), {'SpiDev': MockSpiDev})()
    PixelStrip = MockPixelStrip

from .config import settings


@dataclass
class LampState:
    """Represents the current state of the lamp."""
    is_on: bool = False
    brightness: int = 50  # 0-100
    color_r: int = 255
    color_g: int = 255
    color_b: int = 255
    auto_mode: bool = False
    current_color_index: int = 0


class HardwareController:
    """Main hardware controller for the Smart Lamp."""
    
    def __init__(self):
        self.state = LampState()
        self.color_presets = settings.get_color_presets()
        self.button_callbacks = {}
        self.pwm_pins = {}
        self.led_strip = None
        self.spi = None
        self.auto_cycle_thread = None
        self.auto_cycle_running = False
        self._lock = threading.Lock()
        
        if RASPBERRY_PI_AVAILABLE:
            self._setup_gpio()
            self._setup_leds()
            self._setup_led_strip()
            self._setup_spi()
        
        # Load saved state
        self.load_state()
    
    def _setup_gpio(self):
        """Initialize GPIO settings."""
        GPIO.setmode(GPIO.BCM)
        
        # Setup button pins
        GPIO.setup(settings.hardware.main_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(settings.hardware.color_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(settings.hardware.mode_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Setup LED pins as outputs
        led_pins = [
            settings.hardware.led1_red_pin, settings.hardware.led1_green_pin, settings.hardware.led1_blue_pin,
            settings.hardware.led2_red_pin, settings.hardware.led2_green_pin, settings.hardware.led2_blue_pin,
            settings.hardware.led3_red_pin, settings.hardware.led3_green_pin, settings.hardware.led3_blue_pin
        ]
        
        for pin in led_pins:
            GPIO.setup(pin, GPIO.OUT)
    
    def _setup_leds(self):
        """Initialize PWM for RGB LEDs."""
        led_pin_groups = [
            (settings.hardware.led1_red_pin, settings.hardware.led1_green_pin, settings.hardware.led1_blue_pin),
            (settings.hardware.led2_red_pin, settings.hardware.led2_green_pin, settings.hardware.led2_blue_pin),
            (settings.hardware.led3_red_pin, settings.hardware.led3_green_pin, settings.hardware.led3_blue_pin)
        ]
        
        for i, (r_pin, g_pin, b_pin) in enumerate(led_pin_groups):
            self.pwm_pins[f'led{i+1}_r'] = GPIO.PWM(r_pin, 1000)  # 1kHz frequency
            self.pwm_pins[f'led{i+1}_g'] = GPIO.PWM(g_pin, 1000)
            self.pwm_pins[f'led{i+1}_b'] = GPIO.PWM(b_pin, 1000)
            
            # Start PWM with 0% duty cycle (off)
            self.pwm_pins[f'led{i+1}_r'].start(0)
            self.pwm_pins[f'led{i+1}_g'].start(0)
            self.pwm_pins[f'led{i+1}_b'].start(0)
    
    def _setup_led_strip(self):
        """Initialize the LED strip."""
        if RASPBERRY_PI_AVAILABLE:
            self.led_strip = PixelStrip(
                settings.hardware.led_strip_count,
                settings.hardware.led_strip_pin
            )
            self.led_strip.begin()
    
    def _setup_spi(self):
        """Initialize SPI for MCP3008 ADC."""
        if RASPBERRY_PI_AVAILABLE:
            self.spi = spidev.SpiDev()
            self.spi.open(settings.hardware.spi_bus, settings.hardware.spi_device)
            self.spi.max_speed_hz = 1350000
    
    def setup_button_callbacks(self, main_callback: Callable, color_callback: Callable, mode_callback: Callable):
        """Setup button event callbacks."""
        self.button_callbacks = {
            'main': main_callback,
            'color': color_callback,
            'mode': mode_callback
        }
        
        if RASPBERRY_PI_AVAILABLE:
            GPIO.add_event_detect(
                settings.hardware.main_button_pin,
                GPIO.FALLING,
                callback=lambda x: main_callback(),
                bouncetime=300
            )
            GPIO.add_event_detect(
                settings.hardware.color_button_pin,
                GPIO.FALLING,
                callback=lambda x: color_callback(),
                bouncetime=300
            )
            GPIO.add_event_detect(
                settings.hardware.mode_button_pin,
                GPIO.FALLING,
                callback=lambda x: mode_callback(),
                bouncetime=300
            )
    
    def read_potentiometer(self) -> int:
        """Read potentiometer value and return brightness (0-100)."""
        if not RASPBERRY_PI_AVAILABLE or not self.spi:
            return self.state.brightness
        
        try:
            # Read MCP3008 channel
            adc = self.spi.xfer2([1, (8 + settings.hardware.potentiometer_channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            
            # Convert to percentage (0-100)
            brightness = int((data / 1023.0) * 100)
            return max(0, min(100, brightness))
        except Exception as e:
            print(f"Error reading potentiometer: {e}")
            return self.state.brightness
    
    def set_led_color(self, r: int, g: int, b: int, brightness: Optional[int] = None):
        """Set color for all RGB LEDs."""
        with self._lock:
            if brightness is None:
                brightness = self.state.brightness
            
            # Convert to duty cycle (0-100)
            brightness_factor = brightness / 100.0
            
            r_duty = (r / 255.0) * 100 * brightness_factor
            g_duty = (g / 255.0) * 100 * brightness_factor
            b_duty = (b / 255.0) * 100 * brightness_factor
            
            # Update all LEDs
            for i in range(1, 4):  # LED1, LED2, LED3
                if f'led{i}_r' in self.pwm_pins:
                    self.pwm_pins[f'led{i}_r'].ChangeDutyCycle(r_duty if self.state.is_on else 0)
                    self.pwm_pins[f'led{i}_g'].ChangeDutyCycle(g_duty if self.state.is_on else 0)
                    self.pwm_pins[f'led{i}_b'].ChangeDutyCycle(b_duty if self.state.is_on else 0)
            
            # Update LED strip
            self._update_led_strip(r, g, b, brightness)
            
            # Update state
            self.state.color_r = r
            self.state.color_g = g
            self.state.color_b = b
            self.state.brightness = brightness
    
    def _update_led_strip(self, r: int, g: int, b: int, brightness: int):
        """Update the LED strip with the given color and brightness."""
        if not self.led_strip:
            return
        
        try:
            brightness_factor = brightness / 100.0
            strip_r = int(r * brightness_factor)
            strip_g = int(g * brightness_factor)
            strip_b = int(b * brightness_factor)
            
            color = Color(strip_r, strip_g, strip_b) if self.state.is_on else Color(0, 0, 0)
            
            for i in range(settings.hardware.led_strip_count):
                self.led_strip.setPixelColor(i, color)
            
            self.led_strip.show()
        except Exception as e:
            print(f"Error updating LED strip: {e}")
    
    def toggle_power(self):
        """Toggle lamp on/off."""
        with self._lock:
            self.state.is_on = not self.state.is_on
            if self.state.is_on:
                self.set_led_color(self.state.color_r, self.state.color_g, self.state.color_b)
            else:
                self.turn_off()
    
    def turn_on(self):
        """Turn lamp on."""
        with self._lock:
            self.state.is_on = True
            self.set_led_color(self.state.color_r, self.state.color_g, self.state.color_b)
    
    def turn_off(self):
        """Turn lamp off."""
        with self._lock:
            self.state.is_on = False
            # Set all LEDs to 0
            for i in range(1, 4):
                if f'led{i}_r' in self.pwm_pins:
                    self.pwm_pins[f'led{i}_r'].ChangeDutyCycle(0)
                    self.pwm_pins[f'led{i}_g'].ChangeDutyCycle(0)
                    self.pwm_pins[f'led{i}_b'].ChangeDutyCycle(0)
            
            # Turn off LED strip
            if self.led_strip:
                for i in range(settings.hardware.led_strip_count):
                    self.led_strip.setPixelColor(i, Color(0, 0, 0))
                self.led_strip.show()
    
    def cycle_color(self):
        """Cycle to the next color preset."""
        if not self.state.auto_mode:
            self.state.current_color_index = (self.state.current_color_index + 1) % len(self.color_presets)
            r, g, b = self.color_presets[self.state.current_color_index]
            self.set_led_color(r, g, b)
    
    def toggle_auto_mode(self):
        """Toggle automatic color cycling mode."""
        with self._lock:
            self.state.auto_mode = not self.state.auto_mode
            
            if self.state.auto_mode and not self.auto_cycle_running:
                self._start_auto_cycle()
            elif not self.state.auto_mode and self.auto_cycle_running:
                self._stop_auto_cycle()
    
    def _start_auto_cycle(self):
        """Start automatic color cycling."""
        self.auto_cycle_running = True
        self.auto_cycle_thread = threading.Thread(target=self._auto_cycle_worker, daemon=True)
        self.auto_cycle_thread.start()
    
    def _stop_auto_cycle(self):
        """Stop automatic color cycling."""
        self.auto_cycle_running = False
        if self.auto_cycle_thread:
            self.auto_cycle_thread.join(timeout=1)
    
    def _auto_cycle_worker(self):
        """Worker thread for automatic color cycling."""
        while self.auto_cycle_running and self.state.auto_mode:
            if self.state.is_on:
                self.state.current_color_index = (self.state.current_color_index + 1) % len(self.color_presets)
                r, g, b = self.color_presets[self.state.current_color_index]
                self.set_led_color(r, g, b)
            
            time.sleep(settings.system.auto_cycle_interval)
    
    def update_brightness_from_potentiometer(self):
        """Update brightness based on potentiometer reading."""
        new_brightness = self.read_potentiometer()
        if abs(new_brightness - self.state.brightness) > 2:  # Threshold to avoid noise
            self.set_led_color(self.state.color_r, self.state.color_g, self.state.color_b, new_brightness)
    
    def blink(self, duration: float = 1.0, blink_count: int = 3):
        """Blink the lamp for alerts."""
        original_state = self.state.is_on
        
        for _ in range(blink_count):
            self.turn_on()
            time.sleep(duration / 2)
            self.turn_off()
            time.sleep(duration / 2)
        
        # Restore original state
        if original_state:
            self.turn_on()
    
    def set_warm_light(self):
        """Set warm light (yellow/orange) for cold temperature."""
        self.set_led_color(255, 165, 0)  # Orange
    
    def set_cool_light(self):
        """Set cool light (blue/white) for hot temperature."""
        self.set_led_color(173, 216, 230)  # Light blue
    
    def save_state(self):
        """Save current lamp state to file."""
        import json
        import os
        
        state_data = {
            'is_on': self.state.is_on,
            'brightness': self.state.brightness,
            'color_r': self.state.color_r,
            'color_g': self.state.color_g,
            'color_b': self.state.color_b,
            'auto_mode': self.state.auto_mode,
            'current_color_index': self.state.current_color_index
        }
        
        try:
            os.makedirs(os.path.dirname(settings.system.lamp_state_file), exist_ok=True)
            with open(settings.system.lamp_state_file, 'w') as f:
                json.dump(state_data, f)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def load_state(self):
        """Load lamp state from file."""
        import json
        import os
        
        if not os.path.exists(settings.system.lamp_state_file):
            return
        
        try:
            with open(settings.system.lamp_state_file, 'r') as f:
                state_data = json.load(f)
            
            self.state.is_on = state_data.get('is_on', False)
            self.state.brightness = state_data.get('brightness', settings.system.default_brightness)
            self.state.color_r = state_data.get('color_r', settings.system.default_color_r)
            self.state.color_g = state_data.get('color_g', settings.system.default_color_g)
            self.state.color_b = state_data.get('color_b', settings.system.default_color_b)
            self.state.auto_mode = state_data.get('auto_mode', False)
            self.state.current_color_index = state_data.get('current_color_index', 0)
            
            # Apply loaded state
            if self.state.is_on:
                self.set_led_color(self.state.color_r, self.state.color_g, self.state.color_b)
            
        except Exception as e:
            print(f"Error loading state: {e}")
    
    def cleanup(self):
        """Clean up GPIO and threads."""
        self._stop_auto_cycle()
        self.save_state()
        
        # Stop all PWM
        for pwm in self.pwm_pins.values():
            pwm.stop()
        
        # Close SPI
        if self.spi:
            self.spi.close()
        
        # GPIO cleanup
        if RASPBERRY_PI_AVAILABLE:
            GPIO.cleanup()
