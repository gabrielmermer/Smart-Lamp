"""
Smart Lamp Sensor Controller
Handles external API integrations for earthquake, air quality, and temperature monitoring
"""

import asyncio
import time
import requests
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class SensorController:
    """Main sensor controller for environmental monitoring"""
    
    def __init__(self):
        self.monitoring_active = False
        self.sensor_callbacks = {}
        self.last_readings = {}
        self.monitoring_task = None
        
        # Cache for API responses
        self.cache = {
            "earthquake": {"data": None, "timestamp": 0},
            "air_quality": {"data": None, "timestamp": 0},
            "temperature": {"data": None, "timestamp": 0}
        }
        
        logger.info("Sensor controller initialized")
    
    # =============================================================================
    # EARTHQUAKE MONITORING
    # =============================================================================
    
    def get_earthquake_data(self) -> Optional[Dict]:
        """Get recent earthquake data from USGS API"""
        if settings.settings.MOCK_SENSORS:
            return self._get_mock_earthquake_data()
        
        try:
            # Check cache first
            cache_age = time.time() - self.cache["earthquake"]["timestamp"]
            if cache_age < settings.settings.EARTHQUAKE_CHECK_INTERVAL and self.cache["earthquake"]["data"]:
                return self.cache["earthquake"]["data"]
            
            response = requests.get(settings.settings.USGS_API_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            earthquakes = []
            
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])
                
                if len(coords) >= 2:
                    earthquake = {
                        "magnitude": props.get("mag", 0),
                        "location": props.get("place", "Unknown"),
                        "time": datetime.fromtimestamp(props.get("time", 0) / 1000),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "depth": coords[2] if len(coords) > 2 else 0,
                        "url": props.get("url", "")
                    }
                    
                    # Filter by magnitude and proximity
                    if (earthquake["magnitude"] >= settings.settings.EARTHQUAKE_MIN_MAGNITUDE and 
                        self._is_nearby_location(earthquake["latitude"], earthquake["longitude"])):
                        earthquakes.append(earthquake)
            
            result = {
                "earthquakes": sorted(earthquakes, key=lambda x: x["magnitude"], reverse=True),
                "total_count": len(earthquakes),
                "max_magnitude": max([eq["magnitude"] for eq in earthquakes]) if earthquakes else 0,
                "timestamp": datetime.now()
            }
            
            # Update cache
            self.cache["earthquake"] = {"data": result, "timestamp": time.time()}
            self.last_readings["earthquake"] = result
            
            logger.info(f"Found {len(earthquakes)} significant earthquakes")
            return result
            
        except Exception as e:
            logger.error(f"Earthquake data fetch error: {e}")
            return self.cache["earthquake"]["data"]  # Return cached data on error
    
    def _is_nearby_location(self, lat: float, lon: float, max_distance_km: float = 500) -> bool:
        """Check if coordinates are within max_distance_km of configured location"""
        import math
        
        # Haversine formula for distance calculation
        lat1, lon1 = math.radians(settings.settings.LOCATION_LAT), math.radians(settings.settings.LOCATION_LON)
        lat2, lon2 = math.radians(lat), math.radians(lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c  # Earth's radius in km
        
        return distance_km <= max_distance_km
    
    def _get_mock_earthquake_data(self) -> Dict:
        """Return mock earthquake data for testing"""
        return {
            "earthquakes": [
                {
                    "magnitude": 5.2,
                    "location": "Mock Location - 50km NE of Incheon",
                    "time": datetime.now(),
                    "latitude": 37.5,
                    "longitude": 126.8,
                    "depth": 10.5,
                    "url": "https://earthquake.usgs.gov/mock"
                }
            ],
            "total_count": 1,
            "max_magnitude": 5.2,
            "timestamp": datetime.now()
        }
    
    # =============================================================================
    # AIR QUALITY MONITORING
    # =============================================================================
    
    def get_air_quality_data(self) -> Optional[Dict]:
        """Get air quality data from OpenWeatherMap API"""
        if settings.settings.MOCK_SENSORS:
            return self._get_mock_air_quality_data()
        
        try:
            # Check cache first
            cache_age = time.time() - self.cache["air_quality"]["timestamp"]
            if cache_age < settings.settings.AIR_QUALITY_CHECK_INTERVAL and self.cache["air_quality"]["data"]:
                return self.cache["air_quality"]["data"]
            
            if not settings.settings.OPENWEATHER_API_KEY:
                logger.error("OpenWeatherMap API key not configured")
                return None
            
            url = f"{settings.settings.OPENWEATHER_BASE_URL}/air_pollution"
            params = {
                "lat": settings.settings.LOCATION_LAT,
                "lon": settings.settings.LOCATION_LON,
                "appid": settings.settings.OPENWEATHER_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "list" in data and len(data["list"]) > 0:
                pollution_data = data["list"][0]
                
                result = {
                    "aqi": pollution_data.get("main", {}).get("aqi", 0),
                    "components": pollution_data.get("components", {}),
                    "timestamp": datetime.now(),
                    "location": settings.settings.LOCATION_NAME,
                    "status": self._get_aqi_status(pollution_data.get("main", {}).get("aqi", 0))
                }
                
                # Update cache
                self.cache["air_quality"] = {"data": result, "timestamp": time.time()}
                self.last_readings["air_quality"] = result
                
                logger.info(f"Air quality AQI: {result['aqi']} ({result['status']})")
                return result
            
        except Exception as e:
            logger.error(f"Air quality data fetch error: {e}")
            return self.cache["air_quality"]["data"]
        
        return None
    
    def _get_aqi_status(self, aqi: int) -> str:
        """Convert AQI number to status string"""
        if aqi == 1:
            return "Good"
        elif aqi == 2:
            return "Fair"
        elif aqi == 3:
            return "Moderate"
        elif aqi == 4:
            return "Poor"
        elif aqi == 5:
            return "Very Poor"
        else:
            return "Unknown"
    
    def _get_mock_air_quality_data(self) -> Dict:
        """Return mock air quality data for testing"""
        return {
            "aqi": 3,
            "components": {
                "co": 233.0,
                "no": 0.01,
                "no2": 8.5,
                "o3": 55.8,
                "so2": 1.2,
                "pm2_5": 12.3,
                "pm10": 18.7,
                "nh3": 0.5
            },
            "timestamp": datetime.now(),
            "location": "Mock Location",
            "status": "Moderate"
        }
    
    # =============================================================================
    # TEMPERATURE MONITORING
    # =============================================================================
    
    def get_temperature_data(self) -> Optional[Dict]:
        """Get temperature data from OpenWeatherMap API"""
        if settings.settings.MOCK_SENSORS:
            return self._get_mock_temperature_data()
        
        try:
            # Check cache first
            cache_age = time.time() - self.cache["temperature"]["timestamp"]
            if cache_age < settings.settings.TEMPERATURE_CHECK_INTERVAL and self.cache["temperature"]["data"]:
                return self.cache["temperature"]["data"]
            
            if not settings.settings.OPENWEATHER_API_KEY:
                logger.error("OpenWeatherMap API key not configured")
                return None
            
            url = f"{settings.settings.OPENWEATHER_BASE_URL}/weather"
            params = {
                "lat": settings.settings.LOCATION_LAT,
                "lon": settings.settings.LOCATION_LON,
                "appid": settings.settings.OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {
                "temperature": data.get("main", {}).get("temp", 0),
                "feels_like": data.get("main", {}).get("feels_like", 0),
                "humidity": data.get("main", {}).get("humidity", 0),
                "pressure": data.get("main", {}).get("pressure", 0),
                "weather": data.get("weather", [{}])[0].get("description", "Unknown"),
                "timestamp": datetime.now(),
                "location": data.get("name", settings.settings.LOCATION_NAME),
                "temperature_category": self._get_temperature_category(data.get("main", {}).get("temp", 20))
            }
            
            # Update cache
            self.cache["temperature"] = {"data": result, "timestamp": time.time()}
            self.last_readings["temperature"] = result
            
            logger.info(f"Temperature: {result['temperature']}°C ({result['temperature_category']})")
            return result
            
        except Exception as e:
            logger.error(f"Temperature data fetch error: {e}")
            return self.cache["temperature"]["data"]
        
        return None
    
    def _get_temperature_category(self, temp: float) -> str:
        """Categorize temperature for lamp color control"""
        if temp < settings.settings.TEMPERATURE_COLD_THRESHOLD:
            return "cold"
        elif temp > settings.settings.TEMPERATURE_HOT_THRESHOLD:
            return "hot"
        else:
            return "comfortable"
    
    def _get_mock_temperature_data(self) -> Dict:
        """Return mock temperature data for testing"""
        return {
            "temperature": 22.5,
            "feels_like": 23.1,
            "humidity": 65,
            "pressure": 1013,
            "weather": "Clear sky",
            "timestamp": datetime.now(),
            "location": "Mock Location",
            "temperature_category": "comfortable"
        }
    
    # =============================================================================
    # ALERT SYSTEM
    # =============================================================================
    
    def check_alerts(self) -> Dict[str, Any]:
        """Check all sensors for alert conditions"""
        alerts = {
            "earthquake_alert": False,
            "air_quality_alert": False,
            "temperature_alert": False,
            "alerts": []
        }
        
        # Check earthquake alerts
        earthquake_data = self.get_earthquake_data()
        if earthquake_data and earthquake_data["max_magnitude"] >= settings.settings.EARTHQUAKE_MIN_MAGNITUDE:
            alerts["earthquake_alert"] = True
            alerts["alerts"].append({
                "type": "earthquake",
                "severity": "high",
                "message": f"Earthquake detected: {earthquake_data['max_magnitude']} magnitude",
                "data": earthquake_data["earthquakes"][0] if earthquake_data["earthquakes"] else None
            })
        
        # Check air quality alerts
        air_data = self.get_air_quality_data()
        if air_data and air_data["aqi"] >= 4:  # Poor or Very Poor
            alerts["air_quality_alert"] = True
            alerts["alerts"].append({
                "type": "air_quality",
                "severity": "medium",
                "message": f"Poor air quality: AQI {air_data['aqi']} ({air_data['status']})",
                "data": air_data
            })
        
        # Check temperature alerts
        temp_data = self.get_temperature_data()
        if temp_data:
            temp = temp_data["temperature"]
            if temp < settings.settings.TEMPERATURE_COLD_THRESHOLD or temp > settings.settings.TEMPERATURE_HOT_THRESHOLD:
                alerts["temperature_alert"] = True
                alerts["alerts"].append({
                    "type": "temperature",
                    "severity": "low",
                    "message": f"Extreme temperature: {temp}°C",
                    "data": temp_data
                })
        
        return alerts
    
    # =============================================================================
    # MONITORING SYSTEM
    # =============================================================================
    
    def register_sensor_callback(self, sensor_type: str, callback: Callable):
        """Register callback for sensor alerts"""
        if sensor_type in ["earthquake", "air_quality", "temperature", "all"]:
            self.sensor_callbacks[sensor_type] = callback
            logger.info(f"Callback registered for {sensor_type} sensor")
        else:
            logger.error(f"Unknown sensor type: {sensor_type}")
    
    async def start_monitoring(self):
        """Start continuous sensor monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitor_sensors())
        logger.info("Sensor monitoring started")
    
    def stop_monitoring(self):
        """Stop sensor monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("Sensor monitoring stopped")
    
    async def _monitor_sensors(self):
        """Background sensor monitoring loop"""
        while self.monitoring_active:
            try:
                alerts = self.check_alerts()
                
                # Trigger callbacks for alerts
                for alert in alerts["alerts"]:
                    sensor_type = alert["type"]
                    
                    # Call specific sensor callback
                    if sensor_type in self.sensor_callbacks:
                        callback = self.sensor_callbacks[sensor_type]
                        asyncio.create_task(self._run_callback(callback, alert))
                    
                    # Call general callback
                    if "all" in self.sensor_callbacks:
                        callback = self.sensor_callbacks["all"]
                        asyncio.create_task(self._run_callback(callback, alert))
                
                # Wait before next check (use shortest interval)
                min_interval = min(
                    settings.settings.EARTHQUAKE_CHECK_INTERVAL,
                    settings.settings.AIR_QUALITY_CHECK_INTERVAL,
                    settings.settings.TEMPERATURE_CHECK_INTERVAL
                )
                await asyncio.sleep(min_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sensor monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _run_callback(self, callback: Callable, alert: Dict):
        """Run callback safely"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(alert)
            else:
                callback(alert)
        except Exception as e:
            logger.error(f"Sensor callback error: {e}")
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_all_sensor_data(self) -> Dict:
        """Get data from all sensors"""
        return {
            "earthquake": self.get_earthquake_data(),
            "air_quality": self.get_air_quality_data(),
            "temperature": self.get_temperature_data(),
            "last_update": datetime.now(),
            "monitoring_active": self.monitoring_active
        }
    
    def get_sensor_status(self) -> Dict:
        """Get sensor system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "mock_mode": settings.settings.MOCK_SENSORS,
            "api_key_configured": bool(settings.settings.OPENWEATHER_API_KEY),
            "last_readings": self.last_readings,
            "cache_status": {
                sensor: {
                    "has_data": cache["data"] is not None,
                    "age_seconds": time.time() - cache["timestamp"]
                }
                for sensor, cache in self.cache.items()
            }
        }
    
    def clear_cache(self):
        """Clear sensor data cache"""
        for sensor in self.cache:
            self.cache[sensor] = {"data": None, "timestamp": 0}
        logger.info("Sensor cache cleared")


# Create global sensor controller instance
sensor_controller = SensorController()