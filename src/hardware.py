"""
Hardware Controller for Smart Lamp

This module handles all hardware interactions:
- RGB LEDs control
- Button input handling  
- Potentiometer brightness control
- LED strip control
- Speaker control

Independent module - can be used standalone.
"""

import time
import threading
import logging
from typing import Tuple, Callable, Optional

try:
    import RPi.GPIO as GPIO
    import spidev
    from rpi_ws281x import PixelStrip, Color
    import pygame
    RASPBERRY_PI = True
except ImportError:
    # For testing on non-Raspberry Pi systems
    RASPBERRY_PI = False
    print("Warning: Running in simulation mode (not on Raspberry Pi)")

from config import hardware, settings

class HardwareController:
    """Independent hardware controller for Smart Lamp"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Hardware state
        self.is_initialized = False
        self.lamp_on = False
        self.current_color = (255, 255, 255)  # Default white
        self.current_brightness = settings.DEFAULT_BRIGHTNESS
        
        # Button callback functions
        self.power_callback = None
        self.color_callback = None
        self.mode_callback = None
        
        # Threading control
        self.running = False
        self.button_thread = None
        
        # Initialize hardware if on Raspberry Pi
        if RASPBERRY_PI:
            self._setup_gpio()
            self._setup_spi()
            self._setup_led_strip()
            self._setup_audio()
        
        self.is_initialized = True
        self.logger.info("Hardware controller initialized")
    
    def _setup_gpio(self):
        """Setup GPIO pins for LEDs and buttons"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup RGB LED pins as outputs
            for led_num in [1, 2, 3]:
                r, g, b = hardware.get_rgb_led_pins(led_num)
                GPIO.setup(r, GPIO.OUT)
                GPIO.setup(g, GPIO.OUT)
                GPIO.setup(b, GPIO.OUT)
            
            # Setup button pins as inputs with pull-up resistors
            for button_pin in hardware.get_all_button_pins():
                GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Setup speaker pin
            GPIO.setup(hardware.SPEAKER_PIN, GPIO.OUT)
            
            self.logger.info("GPIO setup completed")
            
        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
    
    def _setup_spi(self):
        """Setup SPI for MCP3008 ADC"""
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Bus 0, Device 0
            self.spi.max_speed_hz = 1350000
            self.logger.info("SPI setup completed")
        except Exception as e:
            self.logger.error(f"SPI setup failed: {e}")
            self.spi = None
    
    def _setup_led_strip(self):
        """Setup addressable LED strip"""
        try:
            self.led_strip = PixelStrip(
                hardware.LED_STRIP_COUNT,
                hardware.LED_STRIP_PIN,
                800000,  # LED signal frequency in hertz
                10,      # DMA channel
                False,   # Invert signal
                255,     # Brightness
                0        # Channel
            )
            self.led_strip.begin()
            self.logger.info("LED strip setup completed")
        except Exception as e:
            self.logger.error(f"LED strip setup failed: {e}")
            self.led_strip = None
    
    def _setup_audio(self):
        """Setup audio system"""
        try:
            pygame.mixer.init()
            self.logger.info("Audio system setup completed")
        except Exception as e:
            self.logger.error(f"Audio setup failed: {e}")
    
    def set_rgb_led(self, led_number: int, r: int, g: int, b: int):
        """Set color for specific RGB LED (1, 2, or 3)"""
        if not RASPBERRY_PI:
            self.logger.info(f"SIMULATION: LED {led_number} set to RGB({r}, {g}, {b})")
            return True
        
        try:
            red_pin, green_pin, blue_pin = hardware.get_rgb_led_pins(led_number)
            
            # Convert 0-255 values to PWM duty cycle (0-100)
            red_pwm = GPIO.PWM(red_pin, 1000)
            green_pwm = GPIO.PWM(green_pin, 1000)
            blue_pwm = GPIO.PWM(blue_pin, 1000)
            
            red_pwm.start(0)
            green_pwm.start(0)
            blue_pwm.start(0)
            
            # Apply brightness
            brightness_factor = self.current_brightness / 100.0
            red_pwm.ChangeDutyCycle((r / 255.0) * 100 * brightness_factor)
            green_pwm.ChangeDutyCycle((g / 255.0) * 100 * brightness_factor)
            blue_pwm.ChangeDutyCycle((b / 255.0) * 100 * brightness_factor)
            
            self.current_color = (r, g, b)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set RGB LED {led_number}: {e}")
            return False
    
    def set_all_leds(self, r: int, g: int, b: int):
        """Set color for all RGB LEDs"""
        success = True
        for led_num in [1, 2, 3]:
            if not self.set_rgb_led(led_num, r, g, b):
                success = False
        return success
    
    def set_led_strip(self, r: int, g: int, b: int):
        """Set color for entire LED strip"""
        if not RASPBERRY_PI or not self.led_strip:
            self.logger.info(f"SIMULATION: LED strip set to RGB({r}, {g}, {b})")
            return True
        
        try:
            color = Color(r, g, b)
            brightness_factor = self.current_brightness / 100.0
            
            for i in range(hardware.LED_STRIP_COUNT):
                adjusted_color = Color(
                    int(r * brightness_factor),
                    int(g * brightness_factor), 
                    int(b * brightness_factor)
                )
                self.led_strip.setPixelColor(i, adjusted_color)
            
            self.led_strip.show()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set LED strip: {e}")
            return False
    
    def turn_off_all_leds(self):
        """Turn off all LEDs"""
        self.set_all_leds(0, 0, 0)
        self.set_led_strip(0, 0, 0)
        self.lamp_on = False
        self.logger.info("All LEDs turned off")
    
    def turn_on_leds(self, r: int = None, g: int = None, b: int = None):
        """Turn on LEDs with specified color or current color"""
        if r is None or g is None or b is None:
            r, g, b = self.current_color
        
        self.set_all_leds(r, g, b)
        self.set_led_strip(r, g, b)
        self.lamp_on = True
        self.logger.info(f"LEDs turned on with color RGB({r}, {g}, {b})")
    
    def read_potentiometer(self) -> int:
        """Read potentiometer value for brightness control"""
        if not RASPBERRY_PI or not self.spi:
            # Simulation: return random value
            import random
            return random.randint(0, 100)
        
        try:
            # Read from MCP3008 channel
            channel = hardware.BRIGHTNESS_CHANNEL
            adc_value = self.spi.xfer2([1, (8 + channel) << 4, 0])
            data = ((adc_value[1] & 3) << 8) + adc_value[2]
            
            # Convert to brightness percentage (0-100)
            brightness = int((data / 1023.0) * 100)
            brightness = max(settings.MIN_BRIGHTNESS, 
                           min(settings.MAX_BRIGHTNESS, brightness))
            
            return brightness
            
        except Exception as e:
            self.logger.error(f"Failed to read potentiometer: {e}")
            return self.current_brightness
    
    def update_brightness(self):
        """Update brightness based on potentiometer"""
        new_brightness = self.read_potentiometer()
        if abs(new_brightness - self.current_brightness) > 2:  # Only update if significant change
            self.current_brightness = new_brightness
            if self.lamp_on:
                # Refresh current color with new brightness
                self.turn_on_leds()
            self.logger.debug(f"Brightness updated to {new_brightness}%")
    
    def is_button_pressed(self, button_pin: int) -> bool:
        """Check if a button is currently pressed"""
        if not RASPBERRY_PI:
            return False
        
        try:
            return GPIO.input(button_pin) == GPIO.LOW  # Active low with pull-up
        except Exception as e:
            self.logger.error(f"Failed to read button {button_pin}: {e}")
            return False
    
    def set_power_callback(self, callback: Callable):
        """Set callback function for power button"""
        self.power_callback = callback
    
    def set_color_callback(self, callback: Callable):
        """Set callback function for color button"""
        self.color_callback = callback
    
    def set_mode_callback(self, callback: Callable):
        """Set callback function for mode button"""
        self.mode_callback = callback
    
    def start_button_monitoring(self):
        """Start monitoring buttons in a separate thread"""
        if self.button_thread and self.button_thread.is_alive():
            return
        
        self.running = True
        self.button_thread = threading.Thread(target=self._button_monitor_loop)
        self.button_thread.daemon = True
        self.button_thread.start()
        self.logger.info("Button monitoring started")
    
    def stop_button_monitoring(self):
        """Stop button monitoring"""
        self.running = False
        if self.button_thread:
            self.button_thread.join(timeout=1)
        self.logger.info("Button monitoring stopped")
    
    def _button_monitor_loop(self):
        """Main button monitoring loop"""
        last_power_press = 0
        last_color_press = 0
        last_mode_press = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check power button
                if (self.is_button_pressed(hardware.POWER_BUTTON) and 
                    current_time - last_power_press > hardware.BUTTON_DEBOUNCE_TIME):
                    last_power_press = current_time
                    if self.power_callback:
                        self.power_callback()
                
                # Check color button
                if (self.is_button_pressed(hardware.COLOR_BUTTON) and 
                    current_time - last_color_press > hardware.BUTTON_DEBOUNCE_TIME):
                    last_color_press = current_time
                    if self.color_callback:
                        self.color_callback()
                
                # Check mode button
                if (self.is_button_pressed(hardware.MODE_BUTTON) and 
                    current_time - last_mode_press > hardware.BUTTON_DEBOUNCE_TIME):
                    last_mode_press = current_time
                    if self.mode_callback:
                        self.mode_callback()
                
                # Update brightness continuously
                self.update_brightness()
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in button monitoring: {e}")
                time.sleep(1)
    
    def play_alert_sound(self, duration: float = 1.0):
        """Play alert sound"""
        if not RASPBERRY_PI:
            self.logger.info(f"SIMULATION: Playing alert sound for {duration}s")
            return
        
        try:
            # Generate a simple beep tone
            frequency = 1000  # Hz
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            arr = []
            for i in range(frames):
                wave = 4096 * (i % (sample_rate // frequency) < (sample_rate // frequency) // 2)
                arr.append([wave, wave])
            
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
            time.sleep(duration)
            
        except Exception as e:
            self.logger.error(f"Failed to play alert sound: {e}")
    
    def blink_leds(self, r: int, g: int, b: int, times: int = 3, interval: float = 0.5):
        """Blink LEDs with specified color"""
        original_state = self.lamp_on
        original_color = self.current_color
        
        for _ in range(times):
            self.turn_on_leds(r, g, b)
            time.sleep(interval)
            self.turn_off_all_leds()
            time.sleep(interval)
        
        # Restore original state
        if original_state:
            self.turn_on_leds(*original_color)
    
    def get_status(self) -> dict:
        """Get current hardware status"""
        return {
            'initialized': self.is_initialized,
            'lamp_on': self.lamp_on,
            'current_color': self.current_color,
            'current_brightness': self.current_brightness,
            'raspberry_pi': RASPBERRY_PI
        }
    
    def cleanup(self):
        """Clean up hardware resources"""
        self.stop_button_monitoring()
        
        if RASPBERRY_PI:
            self.turn_off_all_leds()
            GPIO.cleanup()
            
            if self.spi:
                self.spi.close()
        
        self.logger.info("Hardware cleanup completed")
    
    def __del__(self):
        """Destructor - cleanup resources"""
        self.cleanup()

# Standalone testing
if __name__ == "__main__":
    # Simple test of hardware controller
    logging.basicConfig(level=logging.INFO)
    
    hw = HardwareController()
    
    print("Testing hardware controller...")
    print(f"Status: {hw.get_status()}")
    
    # Test LED colors
    print("Testing red...")
    hw.turn_on_leds(255, 0, 0)
    time.sleep(2)
    
    print("Testing green...")
    hw.turn_on_leds(0, 255, 0)
    time.sleep(2)
    
    print("Testing blue...")
    hw.turn_on_leds(0, 0, 255)
    time.sleep(2)
    
    print("Testing blink...")
    hw.blink_leds(255, 255, 0, 3, 0.3)
    
    print("Turning off...")
    hw.turn_off_all_leds()
    
    hw.cleanup()
    print("Test completed!")