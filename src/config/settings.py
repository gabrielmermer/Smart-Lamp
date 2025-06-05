"""
Configuration settings for the Smart Lamp project.
Loads environment variables and provides type-safe configuration.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class APIConfig:
    """API configuration settings."""
    earthquake_api_url: str
    earthquake_check_interval: int
    earthquake_min_magnitude: float
    openweather_api_key: str
    openweather_base_url: str
    air_quality_threshold: int
    temp_check_interval: int
    latitude: float
    longitude: float
    location_name: str


@dataclass
class HardwareConfig:
    """Hardware pin configuration."""
    # Button pins
    main_button_pin: int
    color_button_pin: int
    mode_button_pin: int
    
    # LED pins (3 RGB LEDs)
    led1_red_pin: int
    led1_green_pin: int
    led1_blue_pin: int
    led2_red_pin: int
    led2_green_pin: int
    led2_blue_pin: int
    led3_red_pin: int
    led3_green_pin: int
    led3_blue_pin: int
    
    # LED strip
    led_strip_pin: int
    led_strip_count: int
    
    # ADC configuration
    spi_bus: int
    spi_device: int
    potentiometer_channel: int
    
    # Audio
    audio_device: str
    speaker_volume: int


@dataclass
class SystemConfig:
    """System configuration settings."""
    data_log_path: str
    database_path: str
    model_save_path: str
    lamp_state_file: str
    ml_retrain_interval: int
    ml_min_data_points: int
    ml_prediction_confidence_threshold: float
    web_host: str
    web_port: int
    debug_mode: bool
    default_brightness: int
    default_color_r: int
    default_color_g: int
    default_color_b: int
    auto_cycle_interval: float
    inactivity_timeout: int
    radio_stations: List[Dict[str, str]]
    ambient_sounds_path: str


class Settings:
    """Main settings class that loads all configurations."""
    
    def __init__(self):
        self.api = APIConfig(
            earthquake_api_url=os.getenv(
                'EARTHQUAKE_API_URL',
                'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.geojson'
            ),
            earthquake_check_interval=int(os.getenv('EARTHQUAKE_CHECK_INTERVAL', '300')),
            earthquake_min_magnitude=float(os.getenv('EARTHQUAKE_MIN_MAGNITUDE', '5.5')),
            openweather_api_key=os.getenv('OPENWEATHER_API_KEY', ''),
            openweather_base_url=os.getenv(
                'OPENWEATHER_BASE_URL',
                'http://api.openweathermap.org/data/2.5'
            ),
            air_quality_threshold=int(os.getenv('AIR_QUALITY_THRESHOLD', '100')),
            temp_check_interval=int(os.getenv('TEMP_CHECK_INTERVAL', '180')),
            latitude=float(os.getenv('LATITUDE', '37.4419')),
            longitude=float(os.getenv('LONGITUDE', '-122.1430')),
            location_name=os.getenv('LOCATION_NAME', 'Tashkent')
        )
        
        self.hardware = HardwareConfig(
            main_button_pin=int(os.getenv('MAIN_BUTTON_PIN', '18')),
            color_button_pin=int(os.getenv('COLOR_BUTTON_PIN', '24')),
            mode_button_pin=int(os.getenv('MODE_BUTTON_PIN', '23')),
            led1_red_pin=int(os.getenv('LED1_RED_PIN', '12')),
            led1_green_pin=int(os.getenv('LED1_GREEN_PIN', '13')),
            led1_blue_pin=int(os.getenv('LED1_BLUE_PIN', '19')),
            led2_red_pin=int(os.getenv('LED2_RED_PIN', '16')),
            led2_green_pin=int(os.getenv('LED2_GREEN_PIN', '20')),
            led2_blue_pin=int(os.getenv('LED2_BLUE_PIN', '21')),
            led3_red_pin=int(os.getenv('LED3_RED_PIN', '5')),
            led3_green_pin=int(os.getenv('LED3_GREEN_PIN', '6')),
            led3_blue_pin=int(os.getenv('LED3_BLUE_PIN', '26')),
            led_strip_pin=int(os.getenv('LED_STRIP_PIN', '10')),
            led_strip_count=int(os.getenv('LED_STRIP_COUNT', '30')),
            spi_bus=int(os.getenv('SPI_BUS', '0')),
            spi_device=int(os.getenv('SPI_DEVICE', '0')),
            potentiometer_channel=int(os.getenv('POTENTIOMETER_CHANNEL', '0')),
            audio_device=os.getenv('AUDIO_DEVICE', 'default'),
            speaker_volume=int(os.getenv('SPEAKER_VOLUME', '70'))
        )
        
        # Parse radio stations from JSON string
        radio_stations_str = os.getenv('RADIO_STATIONS', '[]')
        try:
            radio_stations = json.loads(radio_stations_str)
        except json.JSONDecodeError:
            radio_stations = []
        
        self.system = SystemConfig(
            data_log_path=os.getenv('DATA_LOG_PATH', './data/usage_logs.json'),
            database_path=os.getenv('DATABASE_PATH', './data/smart_lamp.db'),
            model_save_path=os.getenv('MODEL_SAVE_PATH', './data/models/'),
            lamp_state_file=os.getenv('LAMP_STATE_FILE', './data/lamp_state.json'),
            ml_retrain_interval=int(os.getenv('ML_RETRAIN_INTERVAL', '86400')),
            ml_min_data_points=int(os.getenv('ML_MIN_DATA_POINTS', '50')),
            ml_prediction_confidence_threshold=float(os.getenv('ML_PREDICTION_CONFIDENCE_THRESHOLD', '0.7')),
            web_host=os.getenv('WEB_HOST', '0.0.0.0'),
            web_port=int(os.getenv('WEB_PORT', '8501')),
            debug_mode=os.getenv('DEBUG_MODE', 'False').lower() == 'true',
            default_brightness=int(os.getenv('DEFAULT_BRIGHTNESS', '50')),
            default_color_r=int(os.getenv('DEFAULT_COLOR_R', '255')),
            default_color_g=int(os.getenv('DEFAULT_COLOR_G', '255')),
            default_color_b=int(os.getenv('DEFAULT_COLOR_B', '255')),
            auto_cycle_interval=float(os.getenv('AUTO_CYCLE_INTERVAL', '5.0')),
            inactivity_timeout=int(os.getenv('INACTIVITY_TIMEOUT', '1800')),
            radio_stations=radio_stations,
            ambient_sounds_path=os.getenv('AMBIENT_SOUNDS_PATH', './data/audio/')
        )
    
    def validate(self) -> bool:
        """Validate that all required settings are present."""
        if not self.api.openweather_api_key:
            print("Warning: OPENWEATHER_API_KEY not set. Weather features will be disabled.")
            return False
        return True
    
    def get_color_presets(self) -> List[tuple]:
        """Get predefined color presets for the lamp."""
        return [
            (255, 255, 255),  # White
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan
            (255, 165, 0),    # Orange
            (128, 0, 128),    # Purple
            (255, 192, 203),  # Pink
        ]


# Global settings instance
settings = Settings()
