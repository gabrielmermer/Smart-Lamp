import os
from typing import Dict, Any

class HardwareConfig:
    """Hardware configuration for Smart Lamp components"""
    
    def __init__(self):
        self._load_hardware_config()
    
    def _load_hardware_config(self):
        """Load hardware configuration from environment variables"""
        
        # =============================================================================
        # GPIO PIN CONFIGURATION
        # =============================================================================
        
        # Physical Control Buttons
        self.GPIO_MAIN_SWITCH = int(os.getenv('GPIO_MAIN_SWITCH', '18'))
        self.GPIO_COLOR_BUTTON = int(os.getenv('GPIO_COLOR_BUTTON', '19'))
        self.GPIO_MODE_BUTTON = int(os.getenv('GPIO_MODE_BUTTON', '20'))
        
        # RGB LEDs
        self.GPIO_RGB_LED_1 = int(os.getenv('GPIO_RGB_LED_1', '21'))
        self.GPIO_RGB_LED_2 = int(os.getenv('GPIO_RGB_LED_2', '16'))
        self.GPIO_RGB_LED_3 = int(os.getenv('GPIO_RGB_LED_3', '12'))
        
        # LED Strip
        self.LED_STRIP_PIN = int(os.getenv('LED_STRIP_PIN', '10'))
        self.LED_STRIP_COUNT = int(os.getenv('LED_STRIP_COUNT', '18'))
        
        # SPI/ADC Configuration
        self.SPI_BUS = int(os.getenv('SPI_BUS', '0'))
        self.SPI_DEVICE = int(os.getenv('SPI_DEVICE', '0'))
        self.ADC_CHANNEL_BRIGHTNESS = int(os.getenv('ADC_CHANNEL_BRIGHTNESS', '0'))
        
        # Audio
        self.GPIO_SPEAKER_ENABLE = int(os.getenv('GPIO_SPEAKER_ENABLE', '26'))
        
        # =============================================================================
        # HARDWARE CONSTANTS
        # =============================================================================
        
        # PWM Configuration
        self.PWM_FREQUENCY = 1000  # 1kHz PWM frequency
        self.PWM_RANGE = 100       # PWM duty cycle range
        
        # ADC Configuration
        self.ADC_MAX_VALUE = 1023  # 10-bit ADC
        self.ADC_REFERENCE_VOLTAGE = 3.3
        
        # LED Strip Configuration
        self.LED_STRIP_BRIGHTNESS = 255
        self.LED_STRIP_CHANNEL = 0
        self.LED_STRIP_FREQ_HZ = 800000
        self.LED_STRIP_DMA = 10
        self.LED_STRIP_INVERT = False
        
        # Button Debounce
        self.BUTTON_DEBOUNCE_TIME = 0.3  # seconds
        
        # Color presets for easy access
        self.COLOR_PRESETS = {
            "white": {"r": 255, "g": 255, "b": 255},
            "warm_white": {"r": 255, "g": 230, "b": 180},
            "cool_white": {"r": 180, "g": 220, "b": 255},
            "red": {"r": 255, "g": 0, "b": 0},
            "green": {"r": 0, "g": 255, "b": 0},
            "blue": {"r": 0, "g": 0, "b": 255},
            "yellow": {"r": 255, "g": 255, "b": 0},
            "purple": {"r": 128, "g": 0, "b": 128},
            "orange": {"r": 255, "g": 165, "b": 0},
            "pink": {"r": 255, "g": 192, "b": 203},
            "cyan": {"r": 0, "g": 255, "b": 255},
        }
        
        # Temperature-based color mapping
        self.TEMPERATURE_COLORS = {
            "very_cold": {"r": 100, "g": 150, "b": 255},  # Blue
            "cold": {"r": 150, "g": 200, "b": 255},       # Light blue
            "cool": {"r": 200, "g": 230, "b": 255},       # Very light blue
            "comfortable": {"r": 255, "g": 255, "b": 255}, # White
            "warm": {"r": 255, "g": 230, "b": 200},       # Light orange
            "hot": {"r": 255, "g": 200, "b": 150},        # Orange
            "very_hot": {"r": 255, "g": 100, "b": 100},   # Red
        }
    
    def get_gpio_pins(self) -> Dict[str, int]:
        """Get all GPIO pin assignments"""
        return {
            "main_switch": self.GPIO_MAIN_SWITCH,
            "color_button": self.GPIO_COLOR_BUTTON,
            "mode_button": self.GPIO_MODE_BUTTON,
            "rgb_led_1": self.GPIO_RGB_LED_1,
            "rgb_led_2": self.GPIO_RGB_LED_2,
            "rgb_led_3": self.GPIO_RGB_LED_3,
            "led_strip": self.LED_STRIP_PIN,
            "speaker_enable": self.GPIO_SPEAKER_ENABLE,
        }
    
    def get_led_strip_config(self) -> Dict[str, Any]:
        """Get LED strip configuration"""
        return {
            "pin": self.LED_STRIP_PIN,
            "count": self.LED_STRIP_COUNT,
            "brightness": self.LED_STRIP_BRIGHTNESS,
            "channel": self.LED_STRIP_CHANNEL,
            "freq_hz": self.LED_STRIP_FREQ_HZ,
            "dma": self.LED_STRIP_DMA,
            "invert": self.LED_STRIP_INVERT,
        }
    
    def get_spi_config(self) -> Dict[str, int]:
        """Get SPI configuration for ADC"""
        return {
            "bus": self.SPI_BUS,
            "device": self.SPI_DEVICE,
            "channel": self.ADC_CHANNEL_BRIGHTNESS,
            "max_value": self.ADC_MAX_VALUE,
        }
    
    def get_color_by_temperature(self, temperature: float) -> Dict[str, int]:
        """Get color based on temperature"""
        if temperature < 10:
            return self.TEMPERATURE_COLORS["very_cold"]
        elif temperature < 15:
            return self.TEMPERATURE_COLORS["cold"]
        elif temperature < 20:
            return self.TEMPERATURE_COLORS["cool"]
        elif temperature < 25:
            return self.TEMPERATURE_COLORS["comfortable"]
        elif temperature < 30:
            return self.TEMPERATURE_COLORS["warm"]
        elif temperature < 35:
            return self.TEMPERATURE_COLORS["hot"]
        else:
            return self.TEMPERATURE_COLORS["very_hot"]
    
    def validate_hardware_config(self) -> bool:
        """Validate hardware configuration"""
        errors = []
        
        # Check GPIO pin ranges (valid Raspberry Pi GPIO pins)
        valid_gpio_pins = list(range(2, 28))  # GPIO 2-27 are available
        
        gpio_pins = self.get_gpio_pins()
        for pin_name, pin_number in gpio_pins.items():
            if pin_number not in valid_gpio_pins:
                errors.append(f"Invalid GPIO pin {pin_number} for {pin_name}")
        
        # Check for pin conflicts
        used_pins = list(gpio_pins.values())
        if len(used_pins) != len(set(used_pins)):
            errors.append("GPIO pin conflict detected - same pin used multiple times")
        
        # Check LED strip configuration
        if not (1 <= self.LED_STRIP_COUNT <= 300):
            errors.append("LED_STRIP_COUNT should be between 1 and 300")
        
        if not (0 <= self.LED_STRIP_BRIGHTNESS <= 255):
            errors.append("LED_STRIP_BRIGHTNESS should be between 0 and 255")
        
        if errors:
            print("Hardware configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# Create global hardware config instance
hardware_config = HardwareConfig()

