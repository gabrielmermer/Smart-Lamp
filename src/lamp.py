"""
Smart Lamp Main Controller
Orchestrates all components: hardware, sensors, ML, and database
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from src.config import settings,hardware_config
from src.hardware import hardware_controller
from src.sensors import sensor_controller
from src.ml import ml_controller
from src.database import db_manager
from src.utils import get_logger, load_json_file, save_json_file

logger = get_logger(__name__)


class SmartLamp:
    """Main Smart Lamp controller that orchestrates all components"""
    
    def __init__(self):
        self.is_running = False
        self.current_state = self._load_lamp_state()
        self.last_user_interaction = None
        self.auto_off_timer = None
        self.monitoring_tasks = []
        
        # Component status
        self.components_status = {
            "hardware": False,
            "sensors": False,
            "ml": False,
            "database": False
        }
        
        logger.info("Smart Lamp controller initialized")
    
    def _load_lamp_state(self) -> Dict[str, Any]:
        """Load persistent lamp state from JSON file"""
        state_file = Path("src/config/lamp_state.json")
        default_state = settings.settings.get_default_lamp_state()
        
        try:
            if state_file.exists():
                saved_state = load_json_file(str(state_file), default_state)
                # Merge with defaults to ensure all keys exist
                for key, value in default_state.items():
                    if key not in saved_state:
                        saved_state[key] = value
                return saved_state
            else:
                return default_state
        except Exception as e:
            logger.error(f"Error loading lamp state: {e}")
            return default_state
    
    def _save_lamp_state(self):
        """Save current lamp state to JSON file"""
        try:
            state_file = Path("src/config/lamp_state.json")
            self.current_state["last_interaction"] = datetime.now().isoformat()
            save_json_file(str(state_file), self.current_state)
        except Exception as e:
            logger.error(f"Error saving lamp state: {e}")
    
    # =============================================================================
    # INITIALIZATION AND STARTUP
    # =============================================================================
    
    async def start(self):
        """Start the Smart Lamp system"""
        if self.is_running:
            logger.warning("Smart Lamp is already running")
            return
        
        logger.info("Starting Smart Lamp system...")
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Setup event handlers
            self._setup_hardware_callbacks()
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            # Restore previous state
            await self._restore_lamp_state()
            
            self.is_running = True
            logger.info("Smart Lamp system started successfully")
            
            # Log system startup
            db_manager.log_system_event(
                "system_startup", 
                "Smart Lamp system started",
                "info",
                {"components": self.components_status}
            )
            
            # Keep running
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error starting Smart Lamp: {e}")
            await self.shutdown()
            raise
    
    async def _initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing components...")
        
        # Check hardware
        self.components_status["hardware"] = hardware_controller.is_initialized
        if self.components_status["hardware"]:
            logger.info("✓ Hardware initialized")
        else:
            logger.warning("⚠ Hardware initialization failed")
        
        # Check database
        try:
            db_info = db_manager.get_database_info()
            self.components_status["database"] = "error" not in db_info
            if self.components_status["database"]:
                logger.info("✓ Database initialized")
            else:
                logger.warning("⚠ Database initialization failed")
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            self.components_status["database"] = False
        
        # Check ML system
        try:
            ml_stats = ml_controller.get_model_stats()
            self.components_status["ml"] = "error" not in ml_stats
            if self.components_status["ml"]:
                logger.info("✓ ML system initialized")
            else:
                logger.warning("⚠ ML system initialization failed")
        except Exception as e:
            logger.error(f"ML check failed: {e}")
            self.components_status["ml"] = False
        
        # Start sensor monitoring
        try:
            await sensor_controller.start_monitoring()
            self.components_status["sensors"] = sensor_controller.monitoring_active
            if self.components_status["sensors"]:
                logger.info("✓ Sensors initialized")
            else:
                logger.warning("⚠ Sensor monitoring failed")
        except Exception as e:
            logger.error(f"Sensor initialization failed: {e}")
            self.components_status["sensors"] = False
    
    def _setup_hardware_callbacks(self):
        """Setup hardware button callbacks"""
        if not self.components_status["hardware"]:
            return
        
        # Main switch - toggle lamp on/off
        hardware_controller.register_button_callback("main_switch", self._on_main_switch_pressed)
        
        # Color button - cycle through colors (manual mode only)
        hardware_controller.register_button_callback("color_button", self._on_color_button_pressed)
        
        # Mode button - switch between manual/auto modes
        hardware_controller.register_button_callback("mode_button", self._on_mode_button_pressed)
        
        # Start button monitoring
        hardware_controller.start_button_monitoring()
        
        logger.info("Hardware callbacks configured")
    
    async def _start_monitoring_tasks(self):
        """Start background monitoring tasks"""
        # Sensor alert monitoring
        sensor_controller.register_sensor_callback("all", self._on_sensor_alert)
        
        # Potentiometer monitoring
        self.monitoring_tasks.append(
            asyncio.create_task(self._monitor_potentiometer())
        )
        
        # Auto-off timer monitoring
        self.monitoring_tasks.append(
            asyncio.create_task(self._monitor_auto_off())
        )
        
        # ML prediction monitoring
        if self.current_state.get("auto_mode_enabled", False):
            self.monitoring_tasks.append(
                asyncio.create_task(self._monitor_ml_predictions())
            )
        
        logger.info("Monitoring tasks started")
    
    async def _restore_lamp_state(self):
        """Restore lamp to previous state"""
        try:
            if self.current_state.get("is_on", False):
                await self.set_lamp_state(
                    is_on=True,
                    brightness=self.current_state.get("brightness", 80),
                    color=self.current_state.get("color", {"r": 255, "g": 255, "b": 255}),
                    trigger_type="system_restore"
                )
            
            logger.info("Lamp state restored")
            
        except Exception as e:
            logger.error(f"Error restoring lamp state: {e}")
    
    # =============================================================================
    # MAIN CONTROL METHODS
    # =============================================================================
    
    async def set_lamp_state(self, is_on: bool, brightness: int = None, color: Dict[str, int] = None, 
                           mode: str = None, trigger_type: str = "manual"):
        """Set lamp state with all parameters"""
        try:
            # Update internal state
            self.current_state["is_on"] = is_on
            
            if brightness is not None:
                self.current_state["brightness"] = max(0, min(100, brightness))
            
            if color is not None:
                self.current_state["color"] = color
            
            if mode is not None:
                self.current_state["mode"] = mode
            
            # Apply to hardware
            if self.components_status["hardware"]:
                hardware_controller.set_lamp_state(
                    is_on,
                    self.current_state["brightness"],
                    self.current_state["color"]
                )
            
            # Log interaction for ML
            if trigger_type == "manual":
                self.last_user_interaction = datetime.now()
                ml_controller.log_lamp_state_change(
                    is_on, 
                    self.current_state["brightness"], 
                    self.current_state["color"]
                )
            
            # Log to database
            db_manager.log_lamp_state(
                is_on,
                self.current_state["brightness"],
                self.current_state["color"],
                self.current_state["mode"],
                trigger_type
            )
            
            # Save state
            self._save_lamp_state()
            
            # Reset auto-off timer if lamp turned on
            if is_on:
                self._reset_auto_off_timer()
            
            logger.info(f"Lamp {'ON' if is_on else 'OFF'} - Brightness: {self.current_state['brightness']}% - Trigger: {trigger_type}")
            
        except Exception as e:
            logger.error(f"Error setting lamp state: {e}")
    
    async def toggle_lamp(self, trigger_type: str = "manual"):
        """Toggle lamp on/off"""
        new_state = not self.current_state.get("is_on", False)
        await self.set_lamp_state(new_state, trigger_type=trigger_type)
    
    async def set_color(self, color: Dict[str, int], trigger_type: str = "manual"):
        """Set lamp color"""
        await self.set_lamp_state(
            self.current_state.get("is_on", True),
            color=color,
            trigger_type=trigger_type
        )
        
        # Log color change for ML
        if trigger_type == "manual":
            ml_controller.log_color_change(color)
    
    async def set_brightness(self, brightness: int, trigger_type: str = "manual"):
        """Set lamp brightness"""
        await self.set_lamp_state(
            self.current_state.get("is_on", True),
            brightness=brightness,
            trigger_type=trigger_type
        )
        
        # Log brightness change for ML
        if trigger_type == "manual":
            ml_controller.log_brightness_change(brightness)
    
    async def set_mode(self, mode: str):
        """Set lamp operation mode"""
        valid_modes = ["manual", "auto", "environmental"]
        
        if mode not in valid_modes:
            logger.error(f"Invalid mode: {mode}. Valid modes: {valid_modes}")
            return
        
        old_mode = self.current_state.get("mode", "manual")
        self.current_state["mode"] = mode
        self.current_state["auto_mode_enabled"] = (mode != "manual")
        
        # Start/stop ML monitoring based on mode
        if mode == "auto" and old_mode != "auto":
            self.monitoring_tasks.append(
                asyncio.create_task(self._monitor_ml_predictions())
            )
        
        self._save_lamp_state()
        
        db_manager.log_system_event(
            "mode_change",
            f"Mode changed from {old_mode} to {mode}",
            "info"
        )
        
        logger.info(f"Mode changed to: {mode}")
    
    # =============================================================================
    # HARDWARE BUTTON HANDLERS
    # =============================================================================
    
    def _on_main_switch_pressed(self):
        """Handle main switch button press"""
        logger.info("Main switch pressed")
        asyncio.create_task(self.toggle_lamp("manual"))
    
    def _on_color_button_pressed(self):
        """Handle color button press"""
        logger.info("Color button pressed")
        
        # Only allow in manual mode
        if self.current_state.get("mode", "manual") != "manual":
            logger.warning("Color change ignored - not in manual mode")
            return
        
        # Cycle through preset colors
        colors = list(hardware_config.hardware_config.COLOR_PRESETS.values())
        current_color = self.current_state.get("color", {"r": 255, "g": 255, "b": 255})
        
        # Find current color index
        current_index = 0
        for i, color in enumerate(colors):
            if color == current_color:
                current_index = i
                break
        
        # Get next color
        next_index = (current_index + 1) % len(colors)
        next_color = colors[next_index]
        
        asyncio.create_task(self.set_color(next_color, "manual"))
    
    def _on_mode_button_pressed(self):
        """Handle mode button press"""
        logger.info("Mode button pressed")
        
        modes = ["manual", "auto", "environmental"]
        current_mode = self.current_state.get("mode", "manual")
        
        try:
            current_index = modes.index(current_mode)
            next_index = (current_index + 1) % len(modes)
            next_mode = modes[next_index]
            
            asyncio.create_task(self.set_mode(next_mode))
        except ValueError:
            # If current mode not in list, default to manual
            asyncio.create_task(self.set_mode("manual"))
    
    # =============================================================================
    # MONITORING TASKS
    # =============================================================================
    
    async def _monitor_potentiometer(self):
        """Monitor potentiometer for brightness changes"""
        last_brightness = None
        
        while self.is_running:
            try:
                if self.components_status["hardware"]:
                    current_brightness = hardware_controller.read_potentiometer()
                    
                    # Only update if significant change (>5%) and lamp is on
                    if (last_brightness is None or 
                        abs(current_brightness - last_brightness) > 5 and
                        self.current_state.get("is_on", False)):
                        
                        await self.set_brightness(current_brightness, "potentiometer")
                        last_brightness = current_brightness
                
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Potentiometer monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_auto_off(self):
        """Monitor auto-off timer"""
        while self.is_running:
            try:
                if (self.current_state.get("is_on", False) and 
                    self.last_user_interaction and
                    settings.settings.AUTO_OFF_TIMEOUT_MINUTES > 0):
                    
                    time_since_interaction = datetime.now() - self.last_user_interaction
                    timeout = timedelta(minutes=settings.settings.AUTO_OFF_TIMEOUT_MINUTES)
                    
                    if time_since_interaction > timeout:
                        logger.info("Auto-off timeout reached")
                        await self.set_lamp_state(False, trigger_type="auto_timeout")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-off monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_ml_predictions(self):
        """Monitor ML predictions for auto mode"""
        while self.is_running and self.current_state.get("auto_mode_enabled", False):
            try:
                if self.components_status["ml"]:
                    prediction = ml_controller.predict_lamp_state()
                    
                    if (prediction.get("confidence", 0) >= settings.settings.ML_PREDICTION_CONFIDENCE_THRESHOLD):
                        predicted_state = prediction.get("should_be_on", False)
                        current_state = self.current_state.get("is_on", False)
                        
                        if predicted_state != current_state:
                            logger.info(f"ML prediction: lamp should be {'ON' if predicted_state else 'OFF'} (confidence: {prediction['confidence']:.2f})")
                            await self.set_lamp_state(predicted_state, trigger_type="ml_prediction")
                            
                            # Also predict and set color
                            color_prediction = ml_controller.predict_preferred_color()
                            if color_prediction.get("confidence", 0) > 0.7:
                                await self.set_color(color_prediction["color"], "ml_prediction")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"ML monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _on_sensor_alert(self, alert: Dict[str, Any]):
        """Handle sensor alerts"""
        try:
            alert_type = alert.get("type", "unknown")
            severity = alert.get("severity", "low")
            
            logger.warning(f"Sensor alert: {alert['message']}")
            
            # Log alert to database
            db_manager.log_system_event(
                f"sensor_alert_{alert_type}",
                alert["message"],
                severity,
                alert.get("data", {})
            )
            
            # Respond based on alert type and current mode
            if self.current_state.get("mode") == "environmental" or severity == "high":
                await self._handle_environmental_alert(alert)
            
        except Exception as e:
            logger.error(f"Error handling sensor alert: {e}")
    
    async def _handle_environmental_alert(self, alert: Dict[str, Any]):
        """Handle environmental alerts with lamp responses"""
        alert_type = alert.get("type", "unknown")
        
        if alert_type == "earthquake":
            # Flash red for earthquake alert
            await self._emergency_flash({"r": 255, "g": 0, "b": 0}, duration=10)
            
        elif alert_type == "air_quality":
            # Change to yellow/orange for air quality warning
            await self.set_color({"r": 255, "g": 165, "b": 0}, "environmental_alert")
            
        elif alert_type == "temperature":
            # Adjust color based on temperature
            temp_data = alert.get("data", {})
            temperature = temp_data.get("temperature", 20)
            temp_color = hardware_config.hardware_config.get_color_by_temperature(temperature)
            await self.set_color(temp_color, "environmental_alert")
    
    async def _emergency_flash(self, color: Dict[str, int], duration: int = 5):
        """Flash lamp for emergency alerts"""
        if not self.current_state.get("is_on"):
            original_state = False
            await self.set_lamp_state(True, trigger_type="emergency_alert")
        else:
            original_state = True
        
        original_color = self.current_state.get("color", {"r": 255, "g": 255, "b": 255})
        
        # Flash 3 times
        for _ in range(3):
            await self.set_color(color, "emergency_alert")
            await asyncio.sleep(0.5)
            await self.set_color({"r": 0, "g": 0, "b": 0}, "emergency_alert")
            await asyncio.sleep(0.5)
        
        # Restore original state
        if original_state:
            await self.set_color(original_color, "emergency_alert")
        else:
            await self.set_lamp_state(False, trigger_type="emergency_alert")
    
    def _reset_auto_off_timer(self):
        """Reset auto-off timer"""
        self.last_user_interaction = datetime.now()
    
    # =============================================================================
    # MAIN LOOP AND SHUTDOWN
    # =============================================================================
    
    async def _main_loop(self):
        """Main application loop"""
        try:
            while self.is_running:
                # Periodic health checks
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
    
    async def shutdown(self):
        """Shutdown Smart Lamp system"""
        if not self.is_running:
            return
        
        logger.info("Shutting down Smart Lamp system...")
        self.is_running = False
        
        try:
            # Cancel monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            # Stop sensor monitoring
            sensor_controller.stop_monitoring()
            
            # Save final state
            self._save_lamp_state()
            
            # Cleanup hardware
            hardware_controller.cleanup()
            
            # Log shutdown
            db_manager.log_system_event(
                "system_shutdown",
                "Smart Lamp system shut down",
                "info"
            )
            
            logger.info("Smart Lamp system shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # =============================================================================
    # STATUS AND INFORMATION
    # =============================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            "system": {
                "running": self.is_running,
                "components": self.components_status,
                "last_user_interaction": self.last_user_interaction.isoformat() if self.last_user_interaction else None
            },
            "lamp": {
                "is_on": self.current_state.get("is_on", False),
                "brightness": self.current_state.get("brightness", 0),
                "color": self.current_state.get("color", {"r": 0, "g": 0, "b": 0}),
                "mode": self.current_state.get("mode", "manual"),
                "auto_mode_enabled": self.current_state.get("auto_mode_enabled", False)
            },
            "hardware": hardware_controller.get_status() if self.components_status["hardware"] else {},
            "sensors": sensor_controller.get_sensor_status() if self.components_status["sensors"] else {},
            "ml": ml_controller.get_model_stats() if self.components_status["ml"] else {},
            "database": db_manager.get_database_info() if self.components_status["database"] else {}
        }


# Create global smart lamp instance
smart_lamp = SmartLamp()