import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Settings:
    """Central configuration class for Smart Lamp"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load all configuration from environment variables"""
        
        # =============================================================================
        # API CONFIGURATION
        # =============================================================================
        self.OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
        self.OPENWEATHER_BASE_URL = os.getenv('OPENWEATHER_BASE_URL', 'http://api.openweathermap.org/data/2.5')
        self.USGS_API_URL = os.getenv('USGS_API_URL', 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson')
        
        # Location settings
        self.LOCATION_LAT = float(os.getenv('LOCATION_LAT', '37.4563'))
        self.LOCATION_LON = float(os.getenv('LOCATION_LON', '126.7052'))
        self.LOCATION_NAME = os.getenv('LOCATION_NAME', 'Incheon')
        
        # =============================================================================
        # DATABASE CONFIGURATION
        # =============================================================================
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/smart_lamp.db')
        self.BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
        
        # =============================================================================
        # MACHINE LEARNING CONFIGURATION
        # =============================================================================
        self.ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'data/models/user_pattern.pkl')
        self.ML_RETRAIN_INTERVAL_HOURS = int(os.getenv('ML_RETRAIN_INTERVAL_HOURS', '24'))
        self.ML_MIN_DATA_POINTS = int(os.getenv('ML_MIN_DATA_POINTS', '50'))
        self.ML_PREDICTION_CONFIDENCE_THRESHOLD = float(os.getenv('ML_PREDICTION_CONFIDENCE_THRESHOLD', '0.75'))
        
        # Data collection
        self.INTERACTION_LOG_MAX_ENTRIES = int(os.getenv('INTERACTION_LOG_MAX_ENTRIES', '10000'))
        self.PATTERN_ANALYSIS_DAYS = int(os.getenv('PATTERN_ANALYSIS_DAYS', '30'))
        
        # =============================================================================
        # SENSOR MONITORING CONFIGURATION
        # =============================================================================
        self.EARTHQUAKE_CHECK_INTERVAL = int(os.getenv('EARTHQUAKE_CHECK_INTERVAL', '300'))
        self.AIR_QUALITY_CHECK_INTERVAL = int(os.getenv('AIR_QUALITY_CHECK_INTERVAL', '600'))
        self.TEMPERATURE_CHECK_INTERVAL = int(os.getenv('TEMPERATURE_CHECK_INTERVAL', '300'))
        
        # Alert thresholds
        self.EARTHQUAKE_MIN_MAGNITUDE = float(os.getenv('EARTHQUAKE_MIN_MAGNITUDE', '4.5'))
        self.AIR_QUALITY_UNHEALTHY_THRESHOLD = int(os.getenv('AIR_QUALITY_UNHEALTHY_THRESHOLD', '100'))
        self.TEMPERATURE_COLD_THRESHOLD = float(os.getenv('TEMPERATURE_COLD_THRESHOLD', '18.0'))
        self.TEMPERATURE_HOT_THRESHOLD = float(os.getenv('TEMPERATURE_HOT_THRESHOLD', '28.0'))
        
        # =============================================================================
        # SYSTEM CONFIGURATION
        # =============================================================================
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/app.log')
        self.LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', '10'))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Web interface
        self.STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', '8501'))
        self.WEB_AUTO_REFRESH_SECONDS = int(os.getenv('WEB_AUTO_REFRESH_SECONDS', '5'))
        
        # Lamp behavior
        self.DEFAULT_BRIGHTNESS = int(os.getenv('DEFAULT_BRIGHTNESS', '80'))
        self.DEFAULT_COLOR_R = int(os.getenv('DEFAULT_COLOR_R', '255'))
        self.DEFAULT_COLOR_G = int(os.getenv('DEFAULT_COLOR_G', '255'))
        self.DEFAULT_COLOR_B = int(os.getenv('DEFAULT_COLOR_B', '255'))
        self.AUTO_OFF_TIMEOUT_MINUTES = int(os.getenv('AUTO_OFF_TIMEOUT_MINUTES', '30'))
        
        # System health
        self.HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', '60'))
        self.MAX_CPU_USAGE_PERCENT = int(os.getenv('MAX_CPU_USAGE_PERCENT', '80'))
        self.MAX_MEMORY_USAGE_PERCENT = int(os.getenv('MAX_MEMORY_USAGE_PERCENT', '85'))
        
        # =============================================================================
        # AUDIO CONFIGURATION
        # =============================================================================
        self.RADIO_CLASSICAL = os.getenv('RADIO_CLASSICAL', 'http://stream.radioparadise.com/aac-320')
        self.RADIO_AMBIENT = os.getenv('RADIO_AMBIENT', 'http://ice1.somafm.com/dronezone-256-mp3')
        self.RADIO_NATURE = os.getenv('RADIO_NATURE', 'http://ice1.somafm.com/deepspaceone-128-mp3')
        
        self.DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.7'))
        self.AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '44100'))
        
        # =============================================================================
        # DEVELOPMENT SETTINGS
        # =============================================================================
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.MOCK_GPIO = os.getenv('MOCK_GPIO', 'False').lower() == 'true'
        self.MOCK_SENSORS = os.getenv('MOCK_SENSORS', 'False').lower() == 'true'
        
        self.TEST_DATABASE_PATH = os.getenv('TEST_DATABASE_PATH', 'data/test_smart_lamp.db')
        self.TEST_LOG_LEVEL = os.getenv('TEST_LOG_LEVEL', 'DEBUG')
    
    def validate_config(self) -> bool:
        """Validate critical configuration values"""
        errors = []
        
        # Check API key
        if not self.OPENWEATHER_API_KEY and not self.MOCK_SENSORS:
            errors.append("OPENWEATHER_API_KEY is required")
        
        # Check paths exist
        if not os.path.exists(Path(self.DATABASE_PATH).parent):
            try:
                os.makedirs(Path(self.DATABASE_PATH).parent, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory: {e}")
        
        if not os.path.exists(Path(self.LOG_FILE_PATH).parent):
            try:
                os.makedirs(Path(self.LOG_FILE_PATH).parent, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory: {e}")
        
        # Check value ranges
        if not (0 <= self.DEFAULT_BRIGHTNESS <= 100):
            errors.append("DEFAULT_BRIGHTNESS must be between 0 and 100")
        
        if not (0.0 <= self.DEFAULT_VOLUME <= 1.0):
            errors.append("DEFAULT_VOLUME must be between 0.0 and 1.0")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_default_lamp_state(self) -> dict:
        """Get default lamp state configuration"""
        return {
            "is_on": False,
            "brightness": self.DEFAULT_BRIGHTNESS,
            "color": {
                "r": self.DEFAULT_COLOR_R,
                "g": self.DEFAULT_COLOR_G,
                "b": self.DEFAULT_COLOR_B
            },
            "mode": "manual",  # manual, auto, environmental
            "auto_mode_enabled": False,
            "volume": self.DEFAULT_VOLUME,
            "current_audio": None,
            "last_interaction": None
        }

# Create global settings instance
settings = Settings()