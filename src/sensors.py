"""
Environmental sensors module for Smart Lamp.
Handles earthquake detection, air quality monitoring, and temperature APIs.
Team members: Mansurbek (Earthquake & Air Quality), Leyla (Temperature)
"""

import asyncio
import aiohttp
import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import settings


@dataclass
class EnvironmentalData:
    """Container for environmental sensor data."""
    earthquake_magnitude: Optional[float] = None
    earthquake_location: Optional[str] = None
    earthquake_time: Optional[datetime] = None
    air_quality_index: Optional[int] = None
    air_quality_status: Optional[str] = None
    temperature_celsius: Optional[float] = None
    temperature_fahrenheit: Optional[float] = None
    humidity: Optional[float] = None
    last_updated: Optional[datetime] = None


class EnvironmentalSensors:
    """Environmental monitoring system for the Smart Lamp."""
    
    def __init__(self, lamp_controller=None):
        self.lamp_controller = lamp_controller
        self.data = EnvironmentalData()
        self.running = False
        self.tasks = []
        self.session = None
        self.last_earthquake_id = None
        self.callbacks = {
            'earthquake': [],
            'air_quality': [],
            'temperature': []
        }
        
    async def start_monitoring(self):
        """Start all environmental monitoring tasks."""
        self.running = True
        
        # Create aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Start monitoring tasks
        if settings.api.openweather_api_key:
            self.tasks.append(asyncio.create_task(self._monitor_earthquake()))
            self.tasks.append(asyncio.create_task(self._monitor_air_quality()))
            self.tasks.append(asyncio.create_task(self._monitor_temperature()))
        else:
            print("Warning: OpenWeatherMap API key not configured. Environmental monitoring disabled.")
        
        print("Environmental monitoring started")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks."""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close session
        if self.session:
            await self.session.close()
        
        print("Environmental monitoring stopped")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for environmental events."""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    async def _monitor_earthquake(self):
        """Monitor earthquake data from USGS API."""
        print("Starting earthquake monitoring...")
        
        while self.running:
            try:
                async with self.session.get(settings.api.earthquake_api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_earthquake_data(data)
                    else:
                        print(f"Earthquake API error: {response.status}")
                
            except Exception as e:
                print(f"Error fetching earthquake data: {e}")
            
            await asyncio.sleep(settings.api.earthquake_check_interval)
    
    async def _process_earthquake_data(self, data: Dict[str, Any]):
        """Process earthquake data and trigger alerts if needed."""
        try:
            features = data.get('features', [])
            
            for feature in features:
                properties = feature.get('properties', {})
                magnitude = properties.get('mag', 0)
                location = properties.get('place', 'Unknown')
                event_id = properties.get('id')
                event_time = datetime.fromtimestamp(properties.get('time', 0) / 1000)
                
                # Check if this is a new significant earthquake
                if (magnitude >= settings.api.earthquake_min_magnitude and 
                    event_id != self.last_earthquake_id):
                    
                    self.last_earthquake_id = event_id
                    self.data.earthquake_magnitude = magnitude
                    self.data.earthquake_location = location
                    self.data.earthquake_time = event_time
                    self.data.last_updated = datetime.now()
                    
                    print(f"Earthquake detected: Magnitude {magnitude} at {location}")
                    
                    # Trigger lamp alert
                    if self.lamp_controller:
                        await self._trigger_earthquake_alert(magnitude, location)
                    
                    # Call registered callbacks
                    for callback in self.callbacks['earthquake']:
                        try:
                            callback(magnitude, location, event_time)
                        except Exception as e:
                            print(f"Error in earthquake callback: {e}")
                    
                    break  # Only process the most recent significant earthquake
                    
        except Exception as e:
            print(f"Error processing earthquake data: {e}")
    
    async def _trigger_earthquake_alert(self, magnitude: float, location: str):
        """Trigger lamp alert for earthquake."""
        try:
            # Blink lamp red for earthquake alert
            original_color = (
                self.lamp_controller.state.color_r,
                self.lamp_controller.state.color_g,
                self.lamp_controller.state.color_b
            )
            
            # Set to red and blink
            self.lamp_controller.set_led_color(255, 0, 0)  # Red
            await asyncio.sleep(0.1)  # Small delay for color change
            
            # Blink pattern based on magnitude
            blink_count = min(int(magnitude), 10)  # Max 10 blinks
            for _ in range(blink_count):
                self.lamp_controller.turn_off()
                await asyncio.sleep(0.5)
                self.lamp_controller.turn_on()
                await asyncio.sleep(0.5)
            
            # Wait 10 seconds as specified in pseudocode
            await asyncio.sleep(10)
            
            # Restore original color
            self.lamp_controller.set_led_color(*original_color)
            
        except Exception as e:
            print(f"Error triggering earthquake alert: {e}")
    
    async def _monitor_air_quality(self):
        """Monitor air quality data from OpenWeatherMap API."""
        print("Starting air quality monitoring...")
        
        while self.running:
            try:
                url = f"{settings.api.openweather_base_url}/air_pollution"
                params = {
                    'lat': settings.api.latitude,
                    'lon': settings.api.longitude,
                    'appid': settings.api.openweather_api_key
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_air_quality_data(data)
                    else:
                        print(f"Air quality API error: {response.status}")
                
            except Exception as e:
                print(f"Error fetching air quality data: {e}")
            
            await asyncio.sleep(settings.api.temp_check_interval)  # Use same interval as temperature
    
    async def _process_air_quality_data(self, data: Dict[str, Any]):
        """Process air quality data and trigger alerts if needed."""
        try:
            air_quality = data.get('list', [{}])[0]
            main_data = air_quality.get('main', {})
            
            # OpenWeatherMap AQI: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
            aqi_level = main_data.get('aqi', 1)
            
            # Convert to standard AQI scale (approximate)
            aqi_mapping = {1: 25, 2: 50, 3: 100, 4: 150, 5: 200}
            aqi_value = aqi_mapping.get(aqi_level, 50)
            
            status_mapping = {
                1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"
            }
            aqi_status = status_mapping.get(aqi_level, "Unknown")
            
            self.data.air_quality_index = aqi_value
            self.data.air_quality_status = aqi_status
            self.data.last_updated = datetime.now()
            
            print(f"Air Quality: {aqi_status} (AQI: {aqi_value})")
            
            # Trigger alert if air quality is bad
            if aqi_value >= settings.api.air_quality_threshold:
                if self.lamp_controller:
                    await self._trigger_air_quality_alert(aqi_value, aqi_status)
                
                # Call registered callbacks
                for callback in self.callbacks['air_quality']:
                    try:
                        callback(aqi_value, aqi_status)
                    except Exception as e:
                        print(f"Error in air quality callback: {e}")
                        
        except Exception as e:
            print(f"Error processing air quality data: {e}")
    
    async def _trigger_air_quality_alert(self, aqi: int, status: str):
        """Trigger lamp alert for poor air quality."""
        try:
            original_color = (
                self.lamp_controller.state.color_r,
                self.lamp_controller.state.color_g,
                self.lamp_controller.state.color_b
            )
            
            # Set to purple/brown for air quality alert
            self.lamp_controller.set_led_color(128, 0, 128)  # Purple
            await asyncio.sleep(0.1)
            
            # Turn on for 30 seconds as specified in pseudocode
            self.lamp_controller.turn_on()
            await asyncio.sleep(30)
            
            # Restore original color
            self.lamp_controller.set_led_color(*original_color)
            
        except Exception as e:
            print(f"Error triggering air quality alert: {e}")
    
    async def _monitor_temperature(self):
        """Monitor temperature data from OpenWeatherMap API."""
        print("Starting temperature monitoring...")
        
        while self.running:
            try:
                url = f"{settings.api.openweather_base_url}/weather"
                params = {
                    'lat': settings.api.latitude,
                    'lon': settings.api.longitude,
                    'appid': settings.api.openweather_api_key,
                    'units': 'metric'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_temperature_data(data)
                    else:
                        print(f"Temperature API error: {response.status}")
                
            except Exception as e:
                print(f"Error fetching temperature data: {e}")
            
            await asyncio.sleep(settings.api.temp_check_interval)
    
    async def _process_temperature_data(self, data: Dict[str, Any]):
        """Process temperature data and adjust lamp color accordingly."""
        try:
            main_data = data.get('main', {})
            temp_celsius = main_data.get('temp')
            humidity = main_data.get('humidity')
            
            if temp_celsius is not None:
                temp_fahrenheit = (temp_celsius * 9/5) + 32
                
                self.data.temperature_celsius = temp_celsius
                self.data.temperature_fahrenheit = temp_fahrenheit
                self.data.humidity = humidity
                self.data.last_updated = datetime.now()
                
                print(f"Temperature: {temp_celsius:.1f}°C ({temp_fahrenheit:.1f}°F), Humidity: {humidity}%")
                
                # Adjust lamp color based on temperature
                if self.lamp_controller:
                    await self._adjust_lamp_for_temperature(temp_celsius)
                
                # Call registered callbacks
                for callback in self.callbacks['temperature']:
                    try:
                        callback(temp_celsius, temp_fahrenheit, humidity)
                    except Exception as e:
                        print(f"Error in temperature callback: {e}")
                        
        except Exception as e:
            print(f"Error processing temperature data: {e}")
    
    async def _adjust_lamp_for_temperature(self, temp_celsius: float):
        """Adjust lamp color based on temperature."""
        try:
            # Define temperature thresholds (can be configured later)
            cold_threshold = 18  # Below 18°C is cold
            hot_threshold = 25   # Above 25°C is hot
            
            if temp_celsius < cold_threshold:
                # Cold - set warm light (orange/yellow)
                self.lamp_controller.set_warm_light()
                print("Temperature is cold - setting warm light")
            elif temp_celsius > hot_threshold:
                # Hot - set cool light (blue/white)
                self.lamp_controller.set_cool_light()
                print("Temperature is hot - setting cool light")
            # Otherwise, keep current color
            
        except Exception as e:
            print(f"Error adjusting lamp for temperature: {e}")
    
    def get_current_data(self) -> EnvironmentalData:
        """Get current environmental data."""
        return self.data
    
    def get_earthquake_summary(self) -> Optional[str]:
        """Get earthquake summary string."""
        if self.data.earthquake_magnitude:
            return (f"Magnitude {self.data.earthquake_magnitude} earthquake "
                   f"at {self.data.earthquake_location} "
                   f"on {self.data.earthquake_time.strftime('%Y-%m-%d %H:%M')}")
        return None
    
    def get_air_quality_summary(self) -> Optional[str]:
        """Get air quality summary string."""
        if self.data.air_quality_index:
            return f"Air Quality: {self.data.air_quality_status} (AQI: {self.data.air_quality_index})"
        return None
    
    def get_temperature_summary(self) -> Optional[str]:
        """Get temperature summary string."""
        if self.data.temperature_celsius:
            return (f"Temperature: {self.data.temperature_celsius:.1f}°C "
                   f"({self.data.temperature_fahrenheit:.1f}°F), "
                   f"Humidity: {self.data.humidity}%")
        return None


def run_environmental_monitoring(lamp_controller=None):
    """Run environmental monitoring in a separate thread."""
    async def monitor():
        sensors = EnvironmentalSensors(lamp_controller)
        try:
            await sensors.start_monitoring()
            # Keep running until stopped
            while sensors.running:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in environmental monitoring: {e}")
        finally:
            await sensors.stop_monitoring()
    
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(monitor())
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread
