"""
Application Settings for Smart Lamp

All API URLs, thresholds, and behavior settings loaded from .env file.
Easy to modify without changing code!
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    def __init__(self):
        # API Configuration
        self.EARTHQUAKE_API_URL = os.getenv('EARTHQUAKE_API_URL', 
            'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson')
        self.OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
        self.OPENWEATHER_API_URL = os.getenv('OPENWEATHER_API_URL', 
            'http://api.openweathermap.org/data/2.5/air_pollution')
        self.WEATHER_API_URL = os.getenv('WEATHER_API_URL',
            'http://api.openweathermap.org/data/2.5/weather')
        self.RADIO_API_URL = os.getenv('RADIO_API_URL',
            'http://all.api.radio-browser.info/json/stations/search')
        
        # Location Settings
        self.LOCATION_LAT = float(os.getenv('LOCATION_LAT', 37.5665))
        self.LOCATION_LON = float(os.getenv('LOCATION_LON', 126.9780))
        self.LOCATION_CITY = os.getenv('LOCATION_CITY', 'Seoul')
        
        # Thresholds and Limits
        self.EARTHQUAKE_MIN_MAGNITUDE = float(os.getenv('EARTHQUAKE_MIN_MAGNITUDE', 5.5))
        self.BAD_AIR_THRESHOLD = int(os.getenv('BAD_AIR_THRESHOLD', 100))
        self.COLD_TEMPERATURE_THRESHOLD = int(os.getenv('COLD_TEMPERATURE_THRESHOLD', 18))
        self.HOT_TEMPERATURE_THRESHOLD = int(os.getenv('HOT_TEMPERATURE_THRESHOLD', 28))
        
        # Check Intervals (seconds)
        self.EARTHQUAKE_CHECK_INTERVAL = int(os.getenv('EARTHQUAKE_CHECK_INTERVAL', 300))
        self.AIR_QUALITY_CHECK_INTERVAL = int(os.getenv('AIR_QUALITY_CHECK_INTERVAL', 600))
        self.WEATHER_CHECK_INTERVAL = int(os.getenv('WEATHER_CHECK_INTERVAL', 900))
        
        # ML Model Settings
        self.ML_LEARNING_PERIOD_DAYS = int(os.getenv('ML_LEARNING_PERIOD_DAYS', 7))
        self.ML_PREDICTION_ACCURACY_THRESHOLD = float(os.getenv('ML_PREDICTION_ACCURACY_THRESHOLD', 0.75))
        self.ML_MODEL_UPDATE_INTERVAL = int(os.getenv('ML_MODEL_UPDATE_INTERVAL', 3600))
        self.ML_DATA_COLLECTION_INTERVAL = int(os.getenv('ML_DATA_COLLECTION_INTERVAL', 60))
        
        # File Paths
        self.ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'models/user_pattern.pkl')
        self.ML_DATA_PATH = os.getenv('ML_DATA_PATH', 'data/smart_lamp.db')
        self.STATE_FILE_PATH = os.getenv('STATE_FILE_PATH', 'data/lamp_state.json')
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/smart_lamp.log')
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/smart_lamp.db')
        
        # Colors (RGB tuples)
        self.DEFAULT_COLOR = self._parse_color(os.getenv('DEFAULT_COLOR_RED', '255'), 
                                               os.getenv('DEFAULT_COLOR_GREEN', '255'), 
                                               os.getenv('DEFAULT_COLOR_BLUE', '255'))
        
        # Air Quality Colors
        self.AQI_GOOD_COLOR = self._parse_rgb_string(os.getenv('AQI_GOOD_COLOR', '0,255,0'))
        self.AQI_MODERATE_COLOR = self._parse_rgb_string(os.getenv('AQI_MODERATE_COLOR', '255,255,0'))
        self.AQI_UNHEALTHY_COLOR = self._parse_rgb_string(os.getenv('AQI_UNHEALTHY_COLOR', '255,165,0'))
        self.AQI_DANGEROUS_COLOR = self._parse_rgb_string(os.getenv('AQI_DANGEROUS_COLOR', '255,0,0'))
        
        # Temperature Colors
        self.COLD_COLOR = self._parse_rgb_string(os.getenv('COLD_COLOR', '255,140,0'))
        self.WARM_COLOR = self._parse_rgb_string(os.getenv('WARM_COLOR', '255,255,255'))
        self.HOT_COLOR = self._parse_rgb_string(os.getenv('HOT_COLOR', '0,191,255'))
        
        # Alert Colors
        self.EARTHQUAKE_ALERT_COLOR = self._parse_rgb_string(os.getenv('EARTHQUAKE_ALERT_COLOR', '255,0,0'))
        self.EMERGENCY_COLOR = self._parse_rgb_string(os.getenv('EMERGENCY_COLOR', '255,0,255'))
        
        # Brightness Settings
        self.MIN_BRIGHTNESS = int(os.getenv('MIN_BRIGHTNESS', 5))
        self.MAX_BRIGHTNESS = int(os.getenv('MAX_BRIGHTNESS', 100))
        self.DEFAULT_BRIGHTNESS = int(os.getenv('DEFAULT_BRIGHTNESS', 50))
        
        # Auto Mode Settings
        self.AUTO_COLOR_CYCLE_INTERVAL = int(os.getenv('AUTO_COLOR_CYCLE_INTERVAL', 30))
        self.AUTO_BRIGHTNESS_ADJUSTMENT = os.getenv('AUTO_BRIGHTNESS_ADJUSTMENT', 'True').lower() == 'true'
        
        # Web Interface
        self.STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', 8501))
        self.WEB_UPDATE_INTERVAL = int(os.getenv('WEB_UPDATE_INTERVAL', 5))
        
        # Audio Settings
        self.DEFAULT_VOLUME = int(os.getenv('DEFAULT_VOLUME', 50))
        self.ALERT_VOLUME = int(os.getenv('ALERT_VOLUME', 80))
        self.RADIO_VOLUME = int(os.getenv('RADIO_VOLUME', 30))
        
        # System Settings
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))
    
    def _parse_color(self, r, g, b):
        """Parse individual RGB values into tuple"""
        return (int(r), int(g), int(b))
    
    def _parse_rgb_string(self, rgb_string):
        """Parse RGB string like '255,0,0' into tuple (255, 0, 0)"""
        try:
            r, g, b = rgb_string.split(',')
            return (int(r.strip()), int(g.strip()), int(b.strip()))
        except:
            return (255, 255, 255)  # Default to white if parsing fails
    
    def get_aqi_color(self, aqi_value):
        """Get color based on AQI value"""
        if aqi_value <= 50:
            return self.AQI_GOOD_COLOR
        elif aqi_value <= 100:
            return self.AQI_MODERATE_COLOR
        elif aqi_value <= 150:
            return self.AQI_UNHEALTHY_COLOR
        else:
            return self.AQI_DANGEROUS_COLOR
    
    def get_temperature_color(self, temperature):
        """Get color based on temperature"""
        if temperature < self.COLD_TEMPERATURE_THRESHOLD:
            return self.COLD_COLOR
        elif temperature > self.HOT_TEMPERATURE_THRESHOLD:
            return self.HOT_COLOR
        else:
            return self.WARM_COLOR
    
    def is_api_key_valid(self):
        """Check if required API keys are present"""
        return bool(self.OPENWEATHER_API_KEY and self.OPENWEATHER_API_KEY != 'your_openweather_api_key_here')
    
    def __str__(self):
        """String representation for debugging"""
        return f"""
Settings Configuration:
- Location: {self.LOCATION_CITY} ({self.LOCATION_LAT}, {self.LOCATION_LON})
- Earthquake threshold: {self.EARTHQUAKE_MIN_MAGNITUDE}
- Air quality threshold: {self.BAD_AIR_THRESHOLD}
- Temperature range: {self.COLD_TEMPERATURE_THRESHOLD}°C - {self.HOT_TEMPERATURE_THRESHOLD}°C
- ML learning period: {self.ML_LEARNING_PERIOD_DAYS} days
- API key configured: {self.is_api_key_valid()}
        """