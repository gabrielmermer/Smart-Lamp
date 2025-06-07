"""
Sensor Manager for Smart Lamp

This module handles all external API calls and environmental monitoring:
- Earthquake detection (USGS API)
- Air quality monitoring (OpenWeatherMap API)
- Weather/temperature monitoring (OpenWeatherMap API)
- Radio stations (Radio Browser API)

Independent module - can be used standalone.
"""

import time
import threading
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from config import settings

class SensorManager:
    """Independent sensor manager for environmental monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.earthquake_data = {}
        self.air_quality_data = {}
        self.weather_data = {}
        self.radio_stations = []
        
        # Last update times
        self.last_earthquake_check = 0
        self.last_air_quality_check = 0
        self.last_weather_check = 0
        
        # Callback functions for alerts
        self.earthquake_callback = None
        self.air_quality_callback = None
        self.temperature_callback = None
        
        # Threading control
        self.running = False
        self.monitor_thread = None
        
        self.logger.info("Sensor manager initialized")
    
    def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            response = requests.get(
                url, 
                params=params, 
                timeout=settings.API_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"API request timeout: {url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {url} - {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {url} - {e}")
        
        return None
    
    def check_earthquakes(self) -> bool:
        """Check for significant earthquakes"""
        current_time = time.time()
        
        # Check if enough time has passed since last check
        if current_time - self.last_earthquake_check < settings.EARTHQUAKE_CHECK_INTERVAL:
            return False
        
        self.logger.info("Checking for earthquakes...")
        
        try:
            # Get earthquake data from USGS
            data = self._make_api_request(settings.EARTHQUAKE_API_URL)
            
            if not data or 'features' not in data:
                self.logger.warning("No earthquake data received")
                return False
            
            # Look for significant earthquakes
            significant_earthquakes = []
            for earthquake in data['features']:
                properties = earthquake.get('properties', {})
                magnitude = properties.get('mag', 0)
                place = properties.get('place', 'Unknown')
                time_stamp = properties.get('time', 0)
                
                if magnitude >= settings.EARTHQUAKE_MIN_MAGNITUDE:
                    earthquake_info = {
                        'magnitude': magnitude,
                        'place': place,
                        'time': datetime.fromtimestamp(time_stamp / 1000),
                        'coordinates': earthquake.get('geometry', {}).get('coordinates', [])
                    }
                    significant_earthquakes.append(earthquake_info)
            
            # Update stored data
            self.earthquake_data = {
                'last_check': datetime.now(),
                'significant_earthquakes': significant_earthquakes,
                'total_earthquakes': len(data['features'])
            }
            
            self.last_earthquake_check = current_time
            
            # Trigger callback if significant earthquakes found
            if significant_earthquakes and self.earthquake_callback:
                self.earthquake_callback(significant_earthquakes)
            
            self.logger.info(f"Earthquake check completed. Found {len(significant_earthquakes)} significant earthquakes")
            return True
            
        except Exception as e:
            self.logger.error(f"Earthquake check failed: {e}")
            return False
    
    def check_air_quality(self) -> bool:
        """Check air quality using OpenWeatherMap API"""
        current_time = time.time()
        
        # Check if enough time has passed since last check
        if current_time - self.last_air_quality_check < settings.AIR_QUALITY_CHECK_INTERVAL:
            return False
        
        if not settings.is_api_key_valid():
            self.logger.warning("OpenWeatherMap API key not configured")
            return False
        
        self.logger.info("Checking air quality...")
        
        try:
            # Parameters for air quality API
            params = {
                'lat': settings.LOCATION_LAT,
                'lon': settings.LOCATION_LON,
                'appid': settings.OPENWEATHER_API_KEY
            }
            
            # Get air quality data
            data = self._make_api_request(settings.OPENWEATHER_API_URL, params)
            
            if not data or 'list' not in data:
                self.logger.warning("No air quality data received")
                return False
            
            # Extract air quality information
            current_aqi_data = data['list'][0]
            aqi_value = current_aqi_data.get('main', {}).get('aqi', 1)
            components = current_aqi_data.get('components', {})
            
            # Convert API AQI (1-5) to standard AQI (0-500)
            aqi_mapping = {1: 25, 2: 75, 3: 125, 4: 200, 5: 350}
            standard_aqi = aqi_mapping.get(aqi_value, 50)
            
            # Update stored data
            self.air_quality_data = {
                'last_check': datetime.now(),
                'aqi': standard_aqi,
                'aqi_level': aqi_value,
                'components': components,
                'location': f"{settings.LOCATION_LAT}, {settings.LOCATION_LON}"
            }
            
            self.last_air_quality_check = current_time
            
            # Trigger callback if air quality is bad
            if standard_aqi >= settings.BAD_AIR_THRESHOLD and self.air_quality_callback:
                self.air_quality_callback(standard_aqi, aqi_value)
            
            self.logger.info(f"Air quality check completed. AQI: {standard_aqi}")
            return True
            
        except Exception as e:
            self.logger.error(f"Air quality check failed: {e}")
            return False
    
    def check_weather(self) -> bool:
        """Check weather and temperature"""
        current_time = time.time()
        
        # Check if enough time has passed since last check
        if current_time - self.last_weather_check < settings.WEATHER_CHECK_INTERVAL:
            return False
        
        if not settings.is_api_key_valid():
            self.logger.warning("OpenWeatherMap API key not configured")
            return False
        
        self.logger.info("Checking weather...")
        
        try:
            # Parameters for weather API
            params = {
                'lat': settings.LOCATION_LAT,
                'lon': settings.LOCATION_LON,
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric'  # Celsius
            }
            
            # Get weather data
            data = self._make_api_request(settings.WEATHER_API_URL, params)
            
            if not data or 'main' not in data:
                self.logger.warning("No weather data received")
                return False
            
            # Extract weather information
            main_data = data['main']
            weather_info = data['weather'][0] if data.get('weather') else {}
            
            temperature = main_data.get('temp', 20)
            humidity = main_data.get('humidity', 50)
            feels_like = main_data.get('feels_like', temperature)
            description = weather_info.get('description', 'Unknown')
            
            # Update stored data
            self.weather_data = {
                'last_check': datetime.now(),
                'temperature': temperature,
                'feels_like': feels_like,
                'humidity': humidity,
                'description': description,
                'location': data.get('name', settings.LOCATION_CITY)
            }
            
            self.last_weather_check = current_time
            
            # Trigger callback for temperature-based lighting
            if self.temperature_callback:
                self.temperature_callback(temperature)
            
            self.logger.info(f"Weather check completed. Temperature: {temperature}°C")
            return True
            
        except Exception as e:
            self.logger.error(f"Weather check failed: {e}")
            return False
    
    def get_radio_stations(self, limit: int = 10) -> List[Dict]:
        """Get list of available radio stations"""
        self.logger.info("Fetching radio stations...")
        
        try:
            # Search for radio stations
            params = {
                'limit': limit,
                'order': 'clickcount',
                'reverse': 'true'
            }
            
            data = self._make_api_request(settings.RADIO_API_URL, params)
            
            if not data:
                self.logger.warning("No radio station data received")
                return []
            
            # Extract station information
            stations = []
            for station in data[:limit]:
                station_info = {
                    'name': station.get('name', 'Unknown'),
                    'url': station.get('url_resolved', ''),
                    'country': station.get('country', ''),
                    'language': station.get('language', ''),
                    'genre': station.get('tags', ''),
                    'bitrate': station.get('bitrate', 0)
                }
                if station_info['url']:  # Only add stations with valid URLs
                    stations.append(station_info)
            
            self.radio_stations = stations
            self.logger.info(f"Found {len(stations)} radio stations")
            return stations
            
        except Exception as e:
            self.logger.error(f"Radio station fetch failed: {e}")
            return []
    
    def set_earthquake_callback(self, callback: Callable):
        """Set callback function for earthquake alerts"""
        self.earthquake_callback = callback
    
    def set_air_quality_callback(self, callback: Callable):
        """Set callback function for air quality alerts"""
        self.air_quality_callback = callback
    
    def set_temperature_callback(self, callback: Callable):
        """Set callback function for temperature changes"""
        self.temperature_callback = callback
    
    def start_monitoring(self):
        """Start continuous sensor monitoring in a separate thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Sensor monitoring started")
    
    def stop_monitoring(self):
        """Stop sensor monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Sensor monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check all sensors
                self.check_earthquakes()
                self.check_air_quality()
                self.check_weather()
                
                # Sleep for a short time before next cycle
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def force_check_all(self):
        """Force immediate check of all sensors"""
        self.logger.info("Forcing immediate sensor checks...")
        
        # Reset timers to force checks
        self.last_earthquake_check = 0
        self.last_air_quality_check = 0
        self.last_weather_check = 0
        
        # Run checks
        earthquake_ok = self.check_earthquakes()
        air_ok = self.check_air_quality()
        weather_ok = self.check_weather()
        
        return {
            'earthquake': earthquake_ok,
            'air_quality': air_ok,
            'weather': weather_ok
        }
    
    def get_all_data(self) -> Dict:
        """Get all current sensor data"""
        return {
            'earthquake': self.earthquake_data,
            'air_quality': self.air_quality_data,
            'weather': self.weather_data,
            'radio_stations': self.radio_stations
        }
    
    def get_status(self) -> Dict:
        """Get sensor manager status"""
        return {
            'monitoring': self.running,
            'api_key_configured': settings.is_api_key_valid(),
            'last_checks': {
                'earthquake': datetime.fromtimestamp(self.last_earthquake_check) if self.last_earthquake_check else None,
                'air_quality': datetime.fromtimestamp(self.last_air_quality_check) if self.last_air_quality_check else None,
                'weather': datetime.fromtimestamp(self.last_weather_check) if self.last_weather_check else None
            },
            'data_available': {
                'earthquake': bool(self.earthquake_data),
                'air_quality': bool(self.air_quality_data),
                'weather': bool(self.weather_data),
                'radio': bool(self.radio_stations)
            }
        }

# Standalone testing
if __name__ == "__main__":
    # Simple test of sensor manager
    logging.basicConfig(level=logging.INFO)
    
    sensors = SensorManager()
    
    print("Testing sensor manager...")
    print(f"Status: {sensors.get_status()}")
    
    # Test individual sensor checks
    print("\nTesting earthquake check...")
    earthquake_result = sensors.check_earthquakes()
    print(f"Earthquake check result: {earthquake_result}")
    
    print("\nTesting air quality check...")
    air_result = sensors.check_air_quality()
    print(f"Air quality check result: {air_result}")
    
    print("\nTesting weather check...")
    weather_result = sensors.check_weather()
    print(f"Weather check result: {weather_result}")
    
    print("\nTesting radio stations...")
    stations = sensors.get_radio_stations(5)
    print(f"Found {len(stations)} radio stations")
    
    print("\nAll sensor data:")
    data = sensors.get_all_data()
    for key, value in data.items():
        print(f"{key}: {value}")
    
    print("\nTest completed!")