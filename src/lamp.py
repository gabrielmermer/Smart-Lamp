"""
Lamp Controller for Smart Lamp

Main controller that coordinates all lamp functionality:
- Manual controls (buttons, brightness)
- Environmental responses (weather, air quality, earthquakes)
- ML-based automation
- State management

Independent module - orchestrates other components.
"""

import time
import threading
import logging
import json
from datetime import datetime
from typing import Dict, Tuple, Optional

from config import settings
from .hardware import HardwareController
from .sensors import SensorManager
from .ml import MLManager
from .database import DatabaseManager
from .utils import Utils

class LampController:
    """Main lamp controller - coordinates all functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.hardware = HardwareController()
        self.sensors = SensorManager()
        self.db = DatabaseManager()
        self.ml = MLManager(self.db)
        self.utils = Utils()
        
        # Lamp state
        self.is_on = False
        self.current_color = settings.DEFAULT_COLOR
        self.current_brightness = settings.DEFAULT_BRIGHTNESS
        self.mode = "MANUAL"  # MANUAL or AUTO
        self.auto_color_cycling = False
        
        # Predefined colors for cycling
        self.color_cycle = [
            (255, 100, 100),  # Red
            (100, 255, 100),  # Green
            (100, 100, 255),  # Blue
            (255, 255, 100),  # Yellow
            (255, 100, 255),  # Magenta
            (100, 255, 255),  # Cyan
            (255, 255, 255),  # White
        ]
        self.current_color_index = 0
        
        # Threading control
        self.running = False
        self.auto_thread = None
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Load previous state
        self._load_state()
        
        self.logger.info("Lamp controller initialized")
    
    def _setup_callbacks(self):
        """Setup callback functions for hardware and sensors"""
        # Hardware button callbacks
        self.hardware.set_power_callback(self._on_power_button)
        self.hardware.set_color_callback(self._on_color_button)
        self.hardware.set_mode_callback(self._on_mode_button)
        
        # Sensor callbacks
        self.sensors.set_earthquake_callback(self._on_earthquake_alert)
        self.sensors.set_air_quality_callback(self._on_air_quality_alert)
        self.sensors.set_temperature_callback(self._on_temperature_change)
    
    def _on_power_button(self):
        """Handle power button press"""
        self.logger.info("Power button pressed")
        
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()
        
        # Log user action
        action = "TURN_ON" if self.is_on else "TURN_OFF"
        self.db.log_user_action(action, self.current_color if self.is_on else None, self.current_brightness)
    
    def _on_color_button(self):
        """Handle color button press (only in manual mode)"""
        if self.mode == "MANUAL" and self.is_on:
            self.logger.info("Color button pressed")
            self.cycle_color()
            
            # Log user action
            self.db.log_user_action("COLOR_CHANGE", self.current_color, self.current_brightness)
    
    def _on_mode_button(self):
        """Handle mode button press"""
        self.logger.info("Mode button pressed")
        
        if self.mode == "MANUAL":
            self.mode = "AUTO"
            self.auto_color_cycling = True
        else:
            self.mode = "MANUAL"
            self.auto_color_cycling = False
        
        self.logger.info(f"Mode changed to: {self.mode}")
    
    def _on_earthquake_alert(self, earthquakes):
        """Handle earthquake alert"""
        self.logger.warning(f"Earthquake alert: {len(earthquakes)} significant earthquakes")
        
        # Flash red for earthquake alert
        self.hardware.blink_leds(*settings.EARTHQUAKE_ALERT_COLOR, times=5, interval=0.3)
        self.hardware.play_alert_sound(2.0)
        
        # Log environmental event
        for eq in earthquakes:
            self.db.log_environmental_data("earthquake", eq['magnitude'], {
                'place': eq['place'],
                'time': eq['time'].isoformat()
            })
    
    def _on_air_quality_alert(self, aqi_value, aqi_level):
        """Handle air quality alert"""
        self.logger.warning(f"Air quality alert: AQI {aqi_value}")
        
        # Change to red color for bad air quality
        alert_color = settings.get_aqi_color(aqi_value)
        if self.is_on:
            self.set_color(*alert_color)
        else:
            # Briefly show air quality status
            self.hardware.blink_leds(*alert_color, times=3, interval=0.5)
        
        # Log environmental event
        self.db.log_environmental_data("air_quality", aqi_value, {'aqi_level': aqi_level})
    
    def _on_temperature_change(self, temperature):
        """Handle temperature-based color change"""
        self.logger.info(f"Temperature update: {temperature}°C")
        
        # Only auto-adjust color in AUTO mode
        if self.mode == "AUTO" and self.is_on:
            temp_color = settings.get_temperature_color(temperature)
            self.set_color(*temp_color)
        
        # Log environmental data
        self.db.log_environmental_data("temperature", temperature)
    
    def turn_on(self, color: Tuple[int, int, int] = None):
        """Turn on the lamp"""
        color = color or self.current_color
        self.current_color = color
        self.is_on = True
        
        self.hardware.turn_on_leds(*color)
        self._save_state()
        
        self.logger.info(f"Lamp turned ON - Color: {color}")
    
    def turn_off(self):
        """Turn off the lamp"""
        self.is_on = False
        self.hardware.turn_off_all_leds()
        self._save_state()
        
        self.logger.info("Lamp turned OFF")
    
    def set_color(self, r: int, g: int, b: int):
        """Set lamp color"""
        self.current_color = (r, g, b)
        
        if self.is_on:
            self.hardware.turn_on_leds(r, g, b)
        
        self._save_state()
        self.logger.info(f"Color set to RGB({r}, {g}, {b})")
    
    def cycle_color(self):
        """Cycle to next color in the sequence"""
        self.current_color_index = (self.current_color_index + 1) % len(self.color_cycle)
        new_color = self.color_cycle[self.current_color_index]
        self.set_color(*new_color)
    
    def set_brightness(self, brightness: int):
        """Set lamp brightness (0-100)"""
        brightness = max(settings.MIN_BRIGHTNESS, min(settings.MAX_BRIGHTNESS, brightness))
        self.current_brightness = brightness
        self.hardware.current_brightness = brightness
        
        # Refresh current color with new brightness
        if self.is_on:
            self.hardware.turn_on_leds(*self.current_color)
        
        self._save_state()
        self.logger.info(f"Brightness set to {brightness}%")
    
    def start_automation(self):
        """Start automated lamp control"""
        if self.auto_thread and self.auto_thread.is_alive():
            return
        
        self.running = True
        
        # Start hardware monitoring
        self.hardware.start_button_monitoring()
        
        # Start sensor monitoring
        self.sensors.start_monitoring()
        
        # Start automation thread
        self.auto_thread = threading.Thread(target=self._automation_loop)
        self.auto_thread.daemon = True
        self.auto_thread.start()
        
        self.logger.info("Lamp automation started")
    
    def stop_automation(self):
        """Stop automated lamp control"""
        self.running = False
        
        # Stop components
        self.hardware.stop_button_monitoring()
        self.sensors.stop_monitoring()
        
        # Wait for automation thread
        if self.auto_thread:
            self.auto_thread.join(timeout=5)
        
        self.logger.info("Lamp automation stopped")
    
    def _automation_loop(self):
        """Main automation loop"""
        last_ml_check = 0
        last_color_cycle = 0
        last_brightness_update = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Update brightness from potentiometer (every 2 seconds)
                if current_time - last_brightness_update > 2:
                    old_brightness = self.current_brightness
                    new_brightness = self.hardware.read_potentiometer()
                    
                    if abs(new_brightness - old_brightness) > 3:  # Significant change
                        self.set_brightness(new_brightness)
                    
                    last_brightness_update = current_time
                
                # Auto color cycling (in AUTO mode)
                if (self.mode == "AUTO" and self.auto_color_cycling and self.is_on and
                    current_time - last_color_cycle > settings.AUTO_COLOR_CYCLE_INTERVAL):
                    self.cycle_color()
                    last_color_cycle = current_time
                
                # ML-based automation (every hour)
                if current_time - last_ml_check > settings.ML_MODEL_UPDATE_INTERVAL:
                    self._check_ml_automation()
                    last_ml_check = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in automation loop: {e}")
                time.sleep(5)
    
    def _check_ml_automation(self):
        """Check if ML model suggests any changes"""
        try:
            if not self.ml.can_start_prediction():
                return
            
            should_adjust, adjustments = self.ml.should_auto_adjust()
            
            if should_adjust and self.mode == "AUTO":
                self.logger.info("Applying ML-based adjustments")
                
                # Apply power state changes
                if 'power' in adjustments:
                    power_state = adjustments['power']['state']
                    confidence = adjustments['power']['confidence']
                    
                    if power_state and not self.is_on:
                        self.turn_on()
                        self.logger.info(f"ML turned lamp ON (confidence: {confidence:.2f})")
                    elif not power_state and self.is_on:
                        self.turn_off()
                        self.logger.info(f"ML turned lamp OFF (confidence: {confidence:.2f})")
                
                # Apply color changes
                if 'color' in adjustments and self.is_on:
                    color = adjustments['color']['rgb']
                    confidence = adjustments['color']['confidence']
                    self.set_color(*color)
                    self.logger.info(f"ML changed color to {color} (confidence: {confidence:.2f})")
        
        except Exception as e:
            self.logger.error(f"ML automation error: {e}")
    
    def force_environmental_check(self):
        """Force immediate check of all environmental sensors"""
        return self.sensors.force_check_all()
    
    def train_ml_model(self):
        """Manually trigger ML model training"""
        return self.ml.train_models()
    
    def _save_state(self):
        """Save current lamp state to file"""
        try:
            state = {
                'is_on': self.is_on,
                'current_color': self.current_color,
                'current_brightness': self.current_brightness,
                'mode': self.mode,
                'auto_color_cycling': self.auto_color_cycling,
                'current_color_index': self.current_color_index,
                'timestamp': datetime.now().isoformat()
            }
            
            self.utils.save_json(settings.STATE_FILE_PATH, state)
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load previous lamp state from file"""
        try:
            state = self.utils.load_json(settings.STATE_FILE_PATH)
            
            if state:
                self.is_on = state.get('is_on', False)
                self.current_color = tuple(state.get('current_color', settings.DEFAULT_COLOR))
                self.current_brightness = state.get('current_brightness', settings.DEFAULT_BRIGHTNESS)
                self.mode = state.get('mode', 'MANUAL')
                self.auto_color_cycling = state.get('auto_color_cycling', False)
                self.current_color_index = state.get('current_color_index', 0)
                
                # Restore hardware state
                self.hardware.current_brightness = self.current_brightness
                if self.is_on:
                    self.hardware.turn_on_leds(*self.current_color)
                
                self.logger.info("Previous lamp state restored")
        
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
    
    def get_status(self) -> Dict:
        """Get complete lamp status"""
        return {
            'lamp': {
                'is_on': self.is_on,
                'current_color': self.current_color,
                'current_brightness': self.current_brightness,
                'mode': self.mode,
                'auto_color_cycling': self.auto_color_cycling
            },
            'hardware': self.hardware.get_status(),
            'sensors': self.sensors.get_status(),
            'ml': self.ml.get_status(),
            'database': self.db.get_stats()
        }
    
    def cleanup(self):
        """Clean up all resources"""
        self.stop_automation()
        self._save_state()
        self.hardware.cleanup()
        
        self.logger.info("Lamp controller cleanup completed")

# Standalone testing
if __name__ == "__main__":
    import signal
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Create lamp controller
    lamp = LampController()
    
    def signal_handler(sig, frame):
        print("\nShutting down lamp controller...")
        lamp.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting lamp controller test...")
    print("Press Ctrl+C to stop")
    
    # Start automation
    lamp.start_automation()
    
    # Test basic functions
    print("Testing lamp functions...")
    
    lamp.turn_on((255, 0, 0))  # Red
    time.sleep(2)
    
    lamp.set_color(0, 255, 0)  # Green
    time.sleep(2)
    
    lamp.set_brightness(80)
    time.sleep(2)
    
    lamp.cycle_color()
    time.sleep(2)
    
    # Show status
    status = lamp.get_status()
    print(f"Lamp status: {status['lamp']}")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        lamp.cleanup()