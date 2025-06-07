"""
Hardware Configuration for Smart Lamp

All hardware pin numbers and settings are loaded from .env file.
To change any pin, just modify the .env file - no need to touch this code!
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class HardwareConfig:
    """Hardware pin configuration and settings"""
    
    def __init__(self):
        # RGB LED Pins (Individual LEDs)
        self.RGB_LED_1_RED = int(os.getenv('RGB_LED_1_RED_PIN', 18))
        self.RGB_LED_1_GREEN = int(os.getenv('RGB_LED_1_GREEN_PIN', 19))
        self.RGB_LED_1_BLUE = int(os.getenv('RGB_LED_1_BLUE_PIN', 20))
        
        self.RGB_LED_2_RED = int(os.getenv('RGB_LED_2_RED_PIN', 21))
        self.RGB_LED_2_GREEN = int(os.getenv('RGB_LED_2_GREEN_PIN', 22))
        self.RGB_LED_2_BLUE = int(os.getenv('RGB_LED_2_BLUE_PIN', 23))
        
        self.RGB_LED_3_RED = int(os.getenv('RGB_LED_3_RED_PIN', 24))
        self.RGB_LED_3_GREEN = int(os.getenv('RGB_LED_3_GREEN_PIN', 25))
        self.RGB_LED_3_BLUE = int(os.getenv('RGB_LED_3_BLUE_PIN', 26))
        
        # LED Strip Configuration
        self.LED_STRIP_PIN = int(os.getenv('LED_STRIP_PIN', 12))
        self.LED_STRIP_COUNT = int(os.getenv('LED_STRIP_COUNT', 60))
        
        # Button Pins
        self.POWER_BUTTON = int(os.getenv('POWER_BUTTON_PIN', 2))
        self.COLOR_BUTTON = int(os.getenv('COLOR_BUTTON_PIN', 3))
        self.MODE_BUTTON = int(os.getenv('MODE_BUTTON_PIN', 4))
        
        # MCP3008 ADC Pins (for potentiometer)
        self.MCP3008_CLK = int(os.getenv('MCP3008_CLK_PIN', 11))
        self.MCP3008_MISO = int(os.getenv('MCP3008_MISO_PIN', 9))
        self.MCP3008_MOSI = int(os.getenv('MCP3008_MOSI_PIN', 10))
        self.MCP3008_CS = int(os.getenv('MCP3008_CS_PIN', 8))
        self.BRIGHTNESS_CHANNEL = int(os.getenv('BRIGHTNESS_CHANNEL', 0))
        
        # Speaker Pin
        self.SPEAKER_PIN = int(os.getenv('SPEAKER_PIN', 13))
        
        # Button Settings
        self.BUTTON_DEBOUNCE_TIME = float(os.getenv('BUTTON_DEBOUNCE_TIME', 0.2))
        
        # System Settings
        self.SYSTEM_STARTUP_DELAY = int(os.getenv('SYSTEM_STARTUP_DELAY', 2))
    
    def get_rgb_led_pins(self, led_number):
        """Get RGB pins for a specific LED (1, 2, or 3)"""
        if led_number == 1:
            return (self.RGB_LED_1_RED, self.RGB_LED_1_GREEN, self.RGB_LED_1_BLUE)
        elif led_number == 2:
            return (self.RGB_LED_2_RED, self.RGB_LED_2_GREEN, self.RGB_LED_2_BLUE)
        elif led_number == 3:
            return (self.RGB_LED_3_RED, self.RGB_LED_3_GREEN, self.RGB_LED_3_BLUE)
        else:
            raise ValueError("LED number must be 1, 2, or 3")
    
    def get_all_button_pins(self):
        """Get all button pins as a list"""
        return [self.POWER_BUTTON, self.COLOR_BUTTON, self.MODE_BUTTON]
    
    def get_mcp3008_pins(self):
        """Get MCP3008 SPI pins as a tuple"""
        return (self.MCP3008_CLK, self.MCP3008_MISO, self.MCP3008_MOSI, self.MCP3008_CS)
    
    def __str__(self):
        """String representation for debugging"""
        return f"""
Hardware Configuration:
- RGB LEDs: {self.get_rgb_led_pins(1)}, {self.get_rgb_led_pins(2)}, {self.get_rgb_led_pins(3)}
- LED Strip: Pin {self.LED_STRIP_PIN}, Count {self.LED_STRIP_COUNT}
- Buttons: Power={self.POWER_BUTTON}, Color={self.COLOR_BUTTON}, Mode={self.MODE_BUTTON}
- MCP3008: {self.get_mcp3008_pins()}
- Speaker: Pin {self.SPEAKER_PIN}
        """