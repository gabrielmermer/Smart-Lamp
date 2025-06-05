import time
import threading
from typing import Dict, Callable, Optional, Tuple
from src.config import settings, hardware_config
from src.utils import get_logger

# Import GPIO libraries with fallback for development
try:
    import RPi.GPIO as GPIO
    import spidev
    from rpi_ws281x import PixelStrip, Color
    import pygame
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    if not settings.settings.MOCK_GPIO:
        print("Warning: GPIO libraries not available. Set MOCK_GPIO=True for development.")

logger = get_logger(__name__)


class HardwareController:
    """Main hardware controller for Smart Lamp"""
    
    def __init__(self):
        self.is_initialized = False
        self.button_callbacks = {}
        self.last_button_press = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Hardware components
        self.led_strip = None
        self.spi = None
        
        # Current state
        self.current_brightness = 0
        self.current_color = {"r": 255, "g": 255, "b": 255}
        self.is_lamp_on = False
        
        self._initialize_hardware()
    
    def _initialize_hardware(self):
        """Initialize all hardware components"""
        try:
            if GPIO_AVAILABLE and not settings.settings.MOCK_GPIO:
                self._setup_gpio()
                self._setup_led_strip()
                self._setup_spi()
                self._setup_audio()
            else:
                logger.info("Running in mock mode - no actual hardware control")
            
            self.is_initialized = True
            logger.info("Hardware initialized successfully")
            
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            self.is_initialized = False
    
    def _setup_gpio(self):
        """Setup GPIO pins for buttons and LEDs"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup button pins as inputs with pull-up resistors
        buttons = [
            hardware_config.hardware_config.GPIO_MAIN_SWITCH,
            hardware_config.hardware_config.GPIO_COLOR_BUTTON,
            hardware_config.hardware_config.GPIO_MODE_BUTTON
        ]
        
        for pin in buttons:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_button_press[pin] = 0
        
        # Setup RGB LED pins as outputs
        rgb_pins = [
            hardware_config.hardware_config.GPIO_RGB_LED_1,
            hardware_config.hardware_config.GPIO_RGB_LED_2,
            hardware_config.hardware_config.GPIO_RGB_LED_3
        ]
        
        for pin in rgb_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Setup speaker enable pin
        GPIO.setup(hardware_config.hardware_config.GPIO_SPEAKER_ENABLE, GPIO.OUT)
        GPIO.output(hardware_config.hardware_config.GPIO_SPEAKER_ENABLE, GPIO.LOW)
        
        logger.info("GPIO pins configured")
    
    def _setup_led_strip(self):
        """Setup addressable LED strip"""
        if not GPIO_AVAILABLE or settings.settings.MOCK_GPIO:
            return
        
        try:
            config = hardware_config.hardware_config.get_led_strip_config()
            self.led_strip = PixelStrip(
                config["count"],
                config["pin"],
                config["freq_hz"],
                config["dma"],
                config["invert"],
                config["brightness"],
                config["channel"]
            )
            self.led_strip.begin()
            logger.info(f"LED strip initialized with {config['count']} LEDs")
            
        except Exception as e:
            logger.error(f"LED strip initialization failed: {e}")
            self.led_strip = None
    
    def _setup_spi(self):
        """Setup SPI for ADC communication"""
        if not GPIO_AVAILABLE or settings.settings.MOCK_GPIO:
            return
        
        try:
            self.spi = spidev.SpiDev()
            config = hardware_config.hardware_config.get_spi_config()
            self.spi.open(config["bus"], config["device"])
            self.spi.max_speed_hz = 1000000
            logger.info("SPI initialized for ADC")
            
        except Exception as e:
            logger.error(f"SPI initialization failed: {e}")
            self.spi = None
    
    def _setup_audio(self):
        """Setup audio system"""
        try:
            pygame.mixer.init(
                frequency=settings.settings.AUDIO_SAMPLE_RATE,
                size=-16,
                channels=2,
                buffer=512
            )
            logger.info("Audio system initialized")
            
        except Exception as e:
            logger.error(f"Audio initialization failed: {e}")
    
    # =============================================================================
    # LED CONTROL METHODS
    # =============================================================================
    
    def set_lamp_state(self, is_on: bool, brightness: int = None, color: Dict[str, int] = None):
        """Set overall lamp state"""
        self.is_lamp_on = is_on
        
        if brightness is not None:
            self.current_brightness = max(0, min(100, brightness))
        
        if color is not None:
            self.current_color = color
        
        if is_on:
            self._update_leds()
        else:
            self._turn_off_all_leds()
        
        logger.info(f"Lamp {'ON' if is_on else 'OFF'} - Brightness: {self.current_brightness}%")
    
    def set_color(self, r: int, g: int, b: int):
        """Set lamp color"""
        self.current_color = {"r": r, "g": g, "b": b}
        if self.is_lamp_on:
            self._update_leds()
        logger.info(f"Color set to RGB({r}, {g}, {b})")
    
    def set_brightness(self, brightness: int):
        """Set lamp brightness (0-100)"""
        self.current_brightness = max(0, min(100, brightness))
        if self.is_lamp_on:
            self._update_leds()
        logger.info(f"Brightness set to {self.current_brightness}%")
    
    def _update_leds(self):
        """Update all LEDs with current color and brightness"""
        if not self.is_lamp_on:
            return
        
        # Calculate actual RGB values with brightness
        brightness_factor = self.current_brightness / 100.0
        r = int(self.current_color["r"] * brightness_factor)
        g = int(self.current_color["g"] * brightness_factor)
        b = int(self.current_color["b"] * brightness_factor)
        
        # Update individual RGB LEDs
        self._set_rgb_leds(r, g, b)
        
        # Update LED strip
        self._set_led_strip(r, g, b)
    
    def _set_rgb_leds(self, r: int, g: int, b: int):
        """Control individual RGB LEDs"""
        if not GPIO_AVAILABLE or settings.settings.MOCK_GPIO:
            return
        
        try:
            # Simple on/off control for RGB LEDs based on color intensity
            rgb_pins = [
                hardware_config.hardware_config.GPIO_RGB_LED_1,
                hardware_config.hardware_config.GPIO_RGB_LED_2,
                hardware_config.hardware_config.GPIO_RGB_LED_3
            ]
            
            # Turn on LEDs based on color values
            GPIO.output(rgb_pins[0], GPIO.HIGH if r > 50 else GPIO.LOW)  # Red LED
            GPIO.output(rgb_pins[1], GPIO.HIGH if g > 50 else GPIO.LOW)  # Green LED
            GPIO.output(rgb_pins[2], GPIO.HIGH if b > 50 else GPIO.LOW)  # Blue LED
            
        except Exception as e:
            logger.error(f"RGB LED control error: {e}")
    
    def _set_led_strip(self, r: int, g: int, b: int):
        """Control LED strip"""
        if not self.led_strip:
            return
        
        try:
            color = Color(r, g, b)
            for i in range(self.led_strip.numPixels()):
                self.led_strip.setPixelColor(i, color)
            self.led_strip.show()
            
        except Exception as e:
            logger.error(f"LED strip control error: {e}")
    
    def _turn_off_all_leds(self):
        """Turn off all LEDs"""
        self._set_rgb_leds(0, 0, 0)
        self._set_led_strip(0, 0, 0)
    
    # =============================================================================
    # BUTTON CONTROL METHODS
    # =============================================================================
    
    def register_button_callback(self, button_name: str, callback: Callable):
        """Register callback for button press"""
        button_pin_map = {
            "main_switch": hardware_config.hardware_config.GPIO_MAIN_SWITCH,
            "color_button": hardware_config.hardware_config.GPIO_COLOR_BUTTON,
            "mode_button": hardware_config.hardware_config.GPIO_MODE_BUTTON
        }
        
        if button_name in button_pin_map:
            self.button_callbacks[button_pin_map[button_name]] = callback
            logger.info(f"Callback registered for {button_name}")
        else:
            logger.error(f"Unknown button: {button_name}")
    
    def start_button_monitoring(self):
        """Start monitoring button presses"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_buttons, daemon=True)
        self.monitoring_thread.start()
        logger.info("Button monitoring started")
    
    def stop_button_monitoring(self):
        """Stop monitoring button presses"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        logger.info("Button monitoring stopped")
    
    def _monitor_buttons(self):
        """Monitor button states in background thread"""
        while self.monitoring_active:
            try:
                for pin, callback in self.button_callbacks.items():
                    if self._is_button_pressed(pin):
                        current_time = time.time()
                        # Debounce button press
                        if current_time - self.last_button_press.get(pin, 0) > hardware_config.hardware_config.BUTTON_DEBOUNCE_TIME:
                            self.last_button_press[pin] = current_time
                            threading.Thread(target=callback, daemon=True).start()
                
                time.sleep(0.1)  # Check buttons every 100ms
                
            except Exception as e:
                logger.error(f"Button monitoring error: {e}")
    
    def _is_button_pressed(self, pin: int) -> bool:
        """Check if button is pressed (with mock support)"""
        if settings.settings.MOCK_GPIO:
            return False  # No button presses in mock mode
        
        if GPIO_AVAILABLE:
            return GPIO.input(pin) == GPIO.LOW  # Button pressed = LOW (pull-up resistor)
        
        return False
    
    # =============================================================================
    # POTENTIOMETER METHODS
    # =============================================================================
    
    def read_potentiometer(self) -> int:
        """Read potentiometer value and return brightness (0-100)"""
        if settings.settings.MOCK_GPIO:
            return 50  # Return middle value in mock mode
        
        if not self.spi:
            return self.current_brightness
        
        try:
            # Read from MCP3008 ADC
            channel = hardware_config.hardware_config.ADC_CHANNEL_BRIGHTNESS
            adc_value = self._read_adc(channel)
            
            # Convert ADC value (0-1023) to brightness (0-100)
            brightness = int((adc_value / hardware_config.hardware_config.ADC_MAX_VALUE) * 100)
            return max(0, min(100, brightness))
            
        except Exception as e:
            logger.error(f"Potentiometer read error: {e}")
            return self.current_brightness
    
    def _read_adc(self, channel: int) -> int:
        """Read value from ADC channel"""
        if channel < 0 or channel > 7:
            raise ValueError("ADC channel must be 0-7")
        
        # MCP3008 command: start bit + single/diff + channel + don't care bits
        command = 0x18 | channel  # 0x18 = start bit + single-ended
        
        # Send command and read response
        response = self.spi.xfer2([1, command << 4, 0])
        
        # Extract 10-bit value from response
        adc_value = ((response[1] & 0x03) << 8) + response[2]
        return adc_value
    
    # =============================================================================
    # AUDIO METHODS
    # =============================================================================
    
    def play_audio_file(self, file_path: str, volume: float = None):
        """Play audio file"""
        try:
            if volume is None:
                volume = settings.settings.DEFAULT_VOLUME
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            
            # Enable speaker
            if GPIO_AVAILABLE and not settings.settings.MOCK_GPIO:
                GPIO.output(hardware_config.hardware_config.GPIO_SPEAKER_ENABLE, GPIO.HIGH)
            
            logger.info(f"Playing audio: {file_path}")
            
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
    
    def stop_audio(self):
        """Stop audio playback"""
        try:
            pygame.mixer.music.stop()
            
            # Disable speaker
            if GPIO_AVAILABLE and not settings.settings.MOCK_GPIO:
                GPIO.output(hardware_config.hardware_config.GPIO_SPEAKER_ENABLE, GPIO.LOW)
            
            logger.info("Audio stopped")
            
        except Exception as e:
            logger.error(f"Audio stop error: {e}")
    
    def set_volume(self, volume: float):
        """Set audio volume (0.0 to 1.0)"""
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)
        logger.info(f"Volume set to {volume:.1f}")
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_status(self) -> Dict:
        """Get current hardware status"""
        return {
            "initialized": self.is_initialized,
            "lamp_on": self.is_lamp_on,
            "brightness": self.current_brightness,
            "color": self.current_color.copy(),
            "gpio_available": GPIO_AVAILABLE,
            "mock_mode": settings.settings.MOCK_GPIO,
            "potentiometer_value": self.read_potentiometer(),
            "button_monitoring": self.monitoring_active
        }
    
    def cleanup(self):
        """Cleanup hardware resources"""
        try:
            self.stop_button_monitoring()
            self._turn_off_all_leds()
            self.stop_audio()
            
            if GPIO_AVAILABLE and not settings.settings.MOCK_GPIO:
                GPIO.cleanup()
            
            if self.spi:
                self.spi.close()
            
            logger.info("Hardware cleanup completed")
            
        except Exception as e:
            logger.error(f"Hardware cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


# Create global hardware controller instance
hardware_controller = HardwareController()