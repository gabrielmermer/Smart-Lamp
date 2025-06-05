"""
Main Smart Lamp controller that integrates all subsystems.
Coordinates hardware, sensors, audio, and ML components.
"""

import threading
import time
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from .hardware import HardwareController
from .sensors import EnvironmentalSensors, run_environmental_monitoring
from .audio import AudioManager
from .ml import MLController
from .config import settings


class SmartLamp:
    """Main Smart Lamp controller that orchestrates all subsystems."""
    
    def __init__(self):
        print("Initializing Smart Lamp...")
        
        # Initialize core components
        self.hardware = HardwareController()
        self.ml_controller = MLController(self.hardware)
        self.audio_manager = AudioManager(self.hardware)
        self.environmental_sensors = None
        self.environmental_thread = None
        
        # System state
        self.running = False
        self.last_activity = datetime.now()
        self.inactivity_timer = None
        
        # Setup button callbacks
        self._setup_button_callbacks()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("Smart Lamp initialized successfully")
    
    def _setup_button_callbacks(self):
        """Setup callbacks for physical button presses."""
        def main_button_callback():
            """Handle main button press (ON/OFF toggle)."""
            print("Main button pressed")
            self.hardware.toggle_power()
            self.ml_controller.log_user_action('on' if self.hardware.state.is_on else 'off')
            self._update_activity()
        
        def color_button_callback():
            """Handle color button press (cycle colors)."""
            print("Color button pressed")
            if self.hardware.state.is_on and not self.hardware.state.auto_mode:
                self.hardware.cycle_color()
                self.ml_controller.log_user_action('color_change')
                self._update_activity()
        
        def mode_button_callback():
            """Handle mode button press (toggle auto mode)."""
            print("Mode button pressed")
            self.hardware.toggle_auto_mode()
            self.ml_controller.log_user_action('mode_change')
            self._update_activity()
        
        # Register callbacks with hardware controller
        self.hardware.setup_button_callbacks(
            main_button_callback,
            color_button_callback,
            mode_button_callback
        )
    
    def start(self):
        """Start the Smart Lamp system."""
        if self.running:
            print("Smart Lamp is already running")
            return
        
        print("Starting Smart Lamp system...")
        self.running = True
        
        # Start environmental monitoring
        if settings.api.openweather_api_key:
            self.environmental_thread = run_environmental_monitoring(self.hardware)
            self._setup_environmental_callbacks()
        else:
            print("Environmental monitoring disabled (no API key)")
        
        # Start ML auto mode if enabled
        if self.ml_controller.pattern_analyzer.has_sufficient_data():
            print("Starting ML prediction system...")
            self.ml_controller.enable_auto_mode(True)
        
        # Start monitoring loops
        self._start_monitoring_threads()
        
        print("Smart Lamp system started successfully")
        print("Press Ctrl+C to stop")
    
    def _setup_environmental_callbacks(self):
        """Setup callbacks for environmental events."""
        # This would be implemented with the async sensor system
        # For now, we'll set up the audio manager to respond to environmental events
        self.audio_manager.enable_environmental_audio(True)
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads."""
        # Start potentiometer monitoring
        potentiometer_thread = threading.Thread(target=self._potentiometer_monitor, daemon=True)
        potentiometer_thread.start()
        
        # Start inactivity monitoring
        inactivity_thread = threading.Thread(target=self._inactivity_monitor, daemon=True)
        inactivity_thread.start()
        
        # Start periodic model retraining
        if settings.system.ml_retrain_interval > 0:
            retrain_thread = threading.Thread(target=self._periodic_retrain, daemon=True)
            retrain_thread.start()
    
    def _potentiometer_monitor(self):
        """Monitor potentiometer for brightness changes."""
        while self.running:
            try:
                self.hardware.update_brightness_from_potentiometer()
                time.sleep(0.1)  # Check 10 times per second
            except Exception as e:
                print(f"Error in potentiometer monitor: {e}")
                time.sleep(1)
    
    def _inactivity_monitor(self):
        """Monitor for inactivity and auto-turn off."""
        while self.running:
            try:
                time_since_activity = (datetime.now() - self.last_activity).total_seconds()
                
                if (time_since_activity > settings.system.inactivity_timeout and
                    self.hardware.state.is_on):
                    
                    print("Auto-turning off due to inactivity")
                    self.hardware.turn_off()
                    self.ml_controller.log_user_action('auto_off')
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in inactivity monitor: {e}")
                time.sleep(60)
    
    def _periodic_retrain(self):
        """Periodically retrain ML models."""
        while self.running:
            try:
                time.sleep(settings.system.ml_retrain_interval)
                
                if self.ml_controller.pattern_analyzer.has_sufficient_data():
                    print("Performing periodic ML model retraining...")
                    self.ml_controller.retrain_models()
                
            except Exception as e:
                print(f"Error in periodic retrain: {e}")
                time.sleep(3600)  # Wait an hour before trying again
    
    def _update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def stop(self):
        """Stop the Smart Lamp system."""
        if not self.running:
            return
        
        print("Stopping Smart Lamp system...")
        self.running = False
        
        # Stop ML controller
        self.ml_controller.cleanup()
        
        # Stop audio
        self.audio_manager.cleanup()
        
        # Stop environmental monitoring
        if self.environmental_thread:
            # Environmental monitoring runs in its own thread
            pass
        
        # Cleanup hardware
        self.hardware.cleanup()
        
        print("Smart Lamp system stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    # Public API methods for external control
    
    def turn_on(self):
        """Turn the lamp on."""
        self.hardware.turn_on()
        self.ml_controller.log_user_action('on')
        self._update_activity()
    
    def turn_off(self):
        """Turn the lamp off."""
        self.hardware.turn_off()
        self.ml_controller.log_user_action('off')
        self._update_activity()
    
    def set_color(self, r: int, g: int, b: int):
        """Set lamp color."""
        self.hardware.set_led_color(r, g, b)
        self.ml_controller.log_user_action('color_change')
        self._update_activity()
    
    def set_brightness(self, brightness: int):
        """Set lamp brightness."""
        current_color = (
            self.hardware.state.color_r,
            self.hardware.state.color_g,
            self.hardware.state.color_b
        )
        self.hardware.set_led_color(*current_color, brightness)
        self.ml_controller.log_user_action('brightness_change')
        self._update_activity()
    
    def cycle_color(self):
        """Cycle to next color."""
        self.hardware.cycle_color()
        self.ml_controller.log_user_action('color_change')
        self._update_activity()
    
    def toggle_auto_mode(self):
        """Toggle automatic color cycling."""
        self.hardware.toggle_auto_mode()
        self.ml_controller.log_user_action('mode_change')
        self._update_activity()
    
    def enable_ml_auto_mode(self, enable: bool = True):
        """Enable/disable ML-based automation."""
        self.ml_controller.enable_auto_mode(enable)
    
    def retrain_ml_models(self) -> bool:
        """Manually trigger ML model retraining."""
        return self.ml_controller.retrain_models()
    
    def play_audio(self, track_name: str, track_type: str = 'ambient') -> bool:
        """Play audio track by name."""
        if track_type == 'radio':
            return self.audio_manager.audio_controller.play_radio_by_name(track_name)
        else:
            return self.audio_manager.audio_controller.play_ambient_by_name(track_name)
    
    def stop_audio(self):
        """Stop audio playback."""
        self.audio_manager.audio_controller.stop()
    
    def set_audio_volume(self, volume: int):
        """Set audio volume (0-100)."""
        self.audio_manager.audio_controller.set_volume(volume)
    
    def set_audio_mode(self, mode: str):
        """Set predefined audio mode."""
        if mode == 'bedtime':
            self.audio_manager.set_bedtime_mode()
        elif mode == 'work':
            self.audio_manager.set_work_mode()
        elif mode == 'relaxation':
            self.audio_manager.set_relaxation_mode()
    
    def blink_alert(self, duration: float = 1.0, count: int = 3):
        """Trigger a blink alert."""
        self.hardware.blink(duration, count)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        hardware_state = self.hardware.state
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'running': self.running,
                'last_activity': self.last_activity.isoformat()
            },
            'lamp': {
                'is_on': hardware_state.is_on,
                'brightness': hardware_state.brightness,
                'color': {
                    'r': hardware_state.color_r,
                    'g': hardware_state.color_g,
                    'b': hardware_state.color_b
                },
                'auto_mode': hardware_state.auto_mode,
                'current_color_index': hardware_state.current_color_index
            },
            'ml': self.ml_controller.get_ml_status(),
            'audio': self.audio_manager.get_audio_status(),
            'environmental': {
                'monitoring_active': self.environmental_thread is not None,
                'api_configured': bool(settings.api.openweather_api_key)
            }
        }
        
        return status
    
    def get_environmental_data(self) -> Dict:
        """Get current environmental data if available."""
        # This would interface with the environmental sensors
        # For now, return a placeholder
        return {
            'earthquake': None,
            'air_quality': None,
            'temperature': None,
            'last_updated': None
        }
    
    def get_usage_patterns(self) -> Dict:
        """Get ML-analyzed usage patterns."""
        return self.ml_controller.pattern_analyzer.get_usage_patterns()
    
    def get_available_audio_tracks(self) -> Dict:
        """Get available audio tracks."""
        return self.audio_manager.audio_controller.get_available_tracks()
    
    def predict_for_time(self, target_time: datetime) -> Dict:
        """Get ML prediction for a specific time."""
        prediction = self.ml_controller.get_prediction_for_time(target_time)
        return {
            'should_be_on': prediction.should_be_on,
            'predicted_brightness': prediction.predicted_brightness,
            'predicted_color': {
                'r': prediction.predicted_color[0],
                'g': prediction.predicted_color[1],
                'b': prediction.predicted_color[2]
            },
            'confidence': prediction.confidence,
            'reasoning': prediction.reasoning
        }
    
    def run_interactive_mode(self):
        """Run in interactive command-line mode for testing."""
        print("\n=== Smart Lamp Interactive Mode ===")
        print("Commands:")
        print("  on/off - Turn lamp on/off")
        print("  color <r> <g> <b> - Set color (0-255)")
        print("  brightness <0-100> - Set brightness")
        print("  cycle - Cycle color")
        print("  auto - Toggle auto mode")
        print("  ml - Toggle ML auto mode")
        print("  audio <name> - Play audio")
        print("  stop - Stop audio")
        print("  status - Show status")
        print("  retrain - Retrain ML models")
        print("  quit - Exit")
        
        try:
            while self.running:
                try:
                    command = input("\n> ").strip().lower().split()
                    if not command:
                        continue
                    
                    if command[0] == 'quit':
                        break
                    elif command[0] == 'on':
                        self.turn_on()
                        print("Lamp turned on")
                    elif command[0] == 'off':
                        self.turn_off()
                        print("Lamp turned off")
                    elif command[0] == 'color' and len(command) == 4:
                        r, g, b = int(command[1]), int(command[2]), int(command[3])
                        self.set_color(r, g, b)
                        print(f"Color set to RGB({r}, {g}, {b})")
                    elif command[0] == 'brightness' and len(command) == 2:
                        brightness = int(command[1])
                        self.set_brightness(brightness)
                        print(f"Brightness set to {brightness}%")
                    elif command[0] == 'cycle':
                        self.cycle_color()
                        print("Cycled to next color")
                    elif command[0] == 'auto':
                        self.toggle_auto_mode()
                        state = "enabled" if self.hardware.state.auto_mode else "disabled"
                        print(f"Auto mode {state}")
                    elif command[0] == 'ml':
                        current_state = self.ml_controller.auto_mode_enabled
                        self.enable_ml_auto_mode(not current_state)
                        state = "enabled" if not current_state else "disabled"
                        print(f"ML auto mode {state}")
                    elif command[0] == 'audio' and len(command) == 2:
                        success = self.play_audio(command[1])
                        if success:
                            print(f"Playing audio: {command[1]}")
                        else:
                            print(f"Audio track '{command[1]}' not found")
                    elif command[0] == 'stop':
                        self.stop_audio()
                        print("Audio stopped")
                    elif command[0] == 'status':
                        status = self.get_status()
                        print(f"Lamp: {'ON' if status['lamp']['is_on'] else 'OFF'}")
                        print(f"Color: RGB({status['lamp']['color']['r']}, {status['lamp']['color']['g']}, {status['lamp']['color']['b']})")
                        print(f"Brightness: {status['lamp']['brightness']}%")
                        print(f"Auto mode: {status['lamp']['auto_mode']}")
                        print(f"ML auto: {status['ml']['auto_mode_enabled']}")
                        print(f"Audio: {status['audio']['current_track'] or 'None'}")
                    elif command[0] == 'retrain':
                        success = self.retrain_ml_models()
                        print("Model retraining " + ("completed" if success else "failed"))
                    else:
                        print("Unknown command")
                        
                except (ValueError, IndexError):
                    print("Invalid command format")
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            pass
        
        print("\nExiting interactive mode...")


def create_smart_lamp() -> SmartLamp:
    """Factory function to create a Smart Lamp instance."""
    return SmartLamp()
