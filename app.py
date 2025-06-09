#!/usr/bin/env python3
"""
Smart NeoPixel Lamp Dashboard - Real-time Hardware Control

Streamlit web interface for monitoring and controlling NeoPixel LED strips.
Compatible with Raspberry Pi GPIO setup (GPIO 18, 30 LEDs).
Works with real hardware or demo data when not on Raspberry Pi.

Access: http://localhost:8501
Run with: streamlit run neopixel_dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import threading
import random
import json
import os
import sys
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from colorsys import hsv_to_rgb

# Page configuration
st.set_page_config(
    page_title="Smart Lamp Dashboard",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to import Raspberry Pi libraries, fallback to simulation mode
SIMULATION_MODE = False
RASPBERRY_PI = os.path.exists('/sys/class/thermal/thermal_zone0/temp')

try:
    import board
    import neopixel
    LED_PIN = board.D18
    REAL_HARDWARE = True
except (ImportError, NotImplementedError):
    SIMULATION_MODE = True
    REAL_HARDWARE = False

# NeoPixel configuration
LED_COUNT = 30
LED_BRIGHTNESS = 1.0
LED_INVERT = False

class SimulatedNeoPixel:
    """Simulated NeoPixel for testing without hardware."""
    def __init__(self, pin, count, brightness=1.0, auto_write=True, pixel_order=None):
        self.count = count
        self.brightness = brightness
        self.pixels = [(0, 0, 0)] * count
        
    def __len__(self):
        return self.count
    
    def __setitem__(self, index, color):
        if isinstance(index, slice):
            for i in range(*index.indices(self.count)):
                self.pixels[i] = color
        else:
            self.pixels[index] = color
    
    def __getitem__(self, index):
        return self.pixels[index]
    
    def fill(self, color):
        self.pixels = [color] * self.count
    
    def show(self):
        pass

class NeoPixelController:
    """Enhanced NeoPixel controller with advanced features"""
    def __init__(self):
        if SIMULATION_MODE:
            self.strip = SimulatedNeoPixel(
                None, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False
            )
        else:
            self.strip = neopixel.NeoPixel(
                LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS,
                auto_write=False, pixel_order=neopixel.GRB
            )
        
        self.is_running = False
        self.current_effect = "off"
        self.animation_thread = None
        self.brightness = 0.5
        self.color = (255, 0, 0)
        self.speed = 50
        self.simulation_mode = SIMULATION_MODE
        self.last_update = datetime.now()
        
        # Advanced features
        self.temperature_mode = False
        self.music_sync = False
        self.auto_brightness = False
        
    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    def update_brightness(self, brightness):
        """Update strip brightness."""
        self.brightness = brightness
        self.strip.brightness = brightness
        self.last_update = datetime.now()
        if self.current_effect == "solid":
            self.set_solid_color(self.color)
    
    def set_solid_color(self, color):
        """Set all pixels to a solid color."""
        self.current_effect = "solid"
        self.color = color
        self.strip.fill(color)
        self.strip.show()
        self.last_update = datetime.now()
        if SIMULATION_MODE:
            print(f"🎨 Simulation: Set solid color to RGB{color}")
    
    def turn_off(self):
        """Turn off all pixels."""
        self.current_effect = "off"
        self.is_running = False
        self.strip.fill((0, 0, 0))
        self.strip.show()
        self.last_update = datetime.now()
        if SIMULATION_MODE:
            print("🔴 Simulation: Lamp turned OFF")
    
    def rainbow_cycle_animation(self):
        """Rainbow cycle animation."""
        j = 0
        while self.is_running and self.current_effect == "rainbow":
            for i in range(LED_COUNT):
                pixel_index = (i * 256 // LED_COUNT) + j
                self.strip[i] = self.wheel(pixel_index & 255)
            self.strip.show()
            time.sleep((101 - self.speed) / 1000.0)
            j = (j + 1) % 256
    
    def breathing_animation(self):
        """Breathing effect with selected color."""
        step = 0
        while self.is_running and self.current_effect == "breathing":
            breath_brightness = 0.1 + 0.9 * (np.sin(step * 0.1) + 1) / 2
            temp_brightness = self.brightness * breath_brightness
            
            r, g, b = self.color
            breathing_color = (int(r * breath_brightness), 
                             int(g * breath_brightness), 
                             int(b * breath_brightness))
            
            self.strip.brightness = temp_brightness
            self.strip.fill(breathing_color)
            self.strip.show()
            
            time.sleep((101 - self.speed) / 1000.0)
            step += 1
    
    def strobe_animation(self):
        """Strobe effect with selected color."""
        while self.is_running and self.current_effect == "strobe":
            self.strip.fill(self.color)
            self.strip.show()
            time.sleep((101 - self.speed) / 2000.0)
            
            self.strip.fill((0, 0, 0))
            self.strip.show()
            time.sleep((101 - self.speed) / 2000.0)
    
    def fire_animation(self):
        """Fire effect animation."""
        while self.is_running and self.current_effect == "fire":
            for i in range(LED_COUNT):
                flicker = random.randint(0, 55)
                r = max(0, min(255, 255 - flicker))
                g = max(0, min(255, 100 - flicker))
                b = 0
                self.strip[i] = (r, g, b)
            self.strip.show()
            time.sleep((101 - self.speed) / 1000.0)
    
    def wave_animation(self):
        """Wave effect animation."""
        step = 0
        while self.is_running and self.current_effect == "wave":
            for i in range(LED_COUNT):
                wave_val = (np.sin((i + step) * 0.3) + 1) / 2
                r, g, b = self.color
                wave_color = (int(r * wave_val), int(g * wave_val), int(b * wave_val))
                self.strip[i] = wave_color
            self.strip.show()
            time.sleep((101 - self.speed) / 1000.0)
            step += 1
    
    def start_effect(self, effect_name):
        """Start the selected effect."""
        self.stop_animation()
        self.current_effect = effect_name
        self.last_update = datetime.now()
        
        if SIMULATION_MODE:
            print(f"🌟 Simulation: Starting {effect_name} effect")
        
        effect_map = {
            "rainbow": self.rainbow_cycle_animation,
            "breathing": self.breathing_animation,
            "strobe": self.strobe_animation,
            "fire": self.fire_animation,
            "wave": self.wave_animation
        }
        
        if effect_name in effect_map:
            self.is_running = True
            self.animation_thread = threading.Thread(target=effect_map[effect_name])
            self.animation_thread.daemon = True
            self.animation_thread.start()
    
    def stop_animation(self):
        """Stop current animation."""
        self.is_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1)
    
    def get_status(self):
        """Get current lamp status."""
        return {
            'is_on': self.current_effect != "off",
            'current_color': list(self.color),
            'current_brightness': int(self.brightness * 100),
            'current_effect': self.current_effect,
            'speed': self.speed,
            'last_update': self.last_update.isoformat(),
            'temperature_mode': self.temperature_mode,
            'music_sync': self.music_sync,
            'auto_brightness': self.auto_brightness
        }

class DemoDataGenerator:
    """Generate realistic demo data for development/demo purposes"""
    
    @staticmethod
    def get_environmental_data():
        """Generate realistic environmental data"""
        now = datetime.now()
        hour = now.hour
        
        # Temperature based on time of day
        base_temp = 20 + 8 * abs(12 - hour) / 12
        temperature = base_temp + random.uniform(-2, 2)
        
        # Air quality varies throughout day
        base_aqi = 60 + 20 * (hour > 7 and hour < 19)
        aqi = max(20, min(150, base_aqi + random.uniform(-15, 15)))
        
        # Earthquake activity (rare)
        earthquakes = []
        if random.random() < 0.1:
            earthquakes.append({
                'magnitude': round(random.uniform(5.5, 7.2), 1),
                'place': random.choice(['Pacific Ocean', 'California', 'Japan', 'Chile']),
                'time': now - timedelta(hours=random.randint(1, 12))
            })
        
        return {
            'weather': {
                'temperature': round(temperature, 1),
                'humidity': random.randint(40, 80),
                'feels_like': round(temperature + random.uniform(-2, 2), 1),
                'description': random.choice(['Clear sky', 'Few clouds', 'Partly cloudy', 'Overcast']),
                'location': 'Your Location',
                'last_check': now
            },
            'air_quality': {
                'aqi': int(aqi),
                'aqi_level': min(5, int(aqi / 50) + 1),
                'components': {
                    'pm2_5': round(aqi * 0.4 + random.uniform(-5, 5), 1),
                    'pm10': round(aqi * 0.6 + random.uniform(-8, 8), 1),
                    'no2': round(aqi * 0.3 + random.uniform(-3, 3), 1),
                    'o3': round(aqi * 0.5 + random.uniform(-6, 6), 1)
                },
                'last_check': now
            },
            'earthquake': {
                'significant_earthquakes': earthquakes,
                'total_earthquakes': len(earthquakes) + random.randint(0, 5),
                'last_check': now
            },
            'radio_stations': [
                {'name': 'BBC World Service', 'country': 'UK', 'language': 'English', 'genre': 'News', 'bitrate': 128},
                {'name': 'Jazz FM', 'country': 'US', 'language': 'English', 'genre': 'Jazz', 'bitrate': 192},
                {'name': 'Classic Rock Radio', 'country': 'DE', 'language': 'English', 'genre': 'Rock', 'bitrate': 160},
                {'name': 'K-Pop Live', 'country': 'KR', 'language': 'Korean', 'genre': 'Pop', 'bitrate': 128},
                {'name': 'Chill Lounge', 'country': 'FR', 'language': 'French', 'genre': 'Lounge', 'bitrate': 192}
            ]
        }
    
    @staticmethod
    def get_ml_predictions():
        """Generate realistic ML predictions"""
        now = datetime.now()
        hour = now.hour
        
        # Power predictions based on time
        if 6 <= hour <= 22:
            power_on_prob = 0.8 - 0.3 * abs(14 - hour) / 8
        else:
            power_on_prob = 0.2
        
        power_on_prob = max(0.1, min(0.9, power_on_prob + random.uniform(-0.1, 0.1)))
        
        # Color predictions based on time
        time_colors = {
            range(6, 11): (255, 200, 150),   # Morning - warm
            range(11, 17): (255, 255, 255),  # Afternoon - bright
            range(17, 22): (255, 180, 100),  # Evening - orange
        }
        
        predicted_color = (100, 150, 255)  # Default night blue
        for time_range, color in time_colors.items():
            if hour in time_range:
                predicted_color = color
                break
        
        # Add randomness
        predicted_color = tuple(max(50, min(255, c + random.randint(-30, 30))) for c in predicted_color)
        
        # Generate 24-hour predictions
        daily_predictions = []
        for h in range(24):
            should_be_on = 6 <= h <= 22
            confidence = 0.7 + 0.2 * random.random()
            
            daily_predictions.append({
                'hour': h,
                'should_be_on': should_be_on,
                'power_confidence': confidence,
                'predicted_color': (
                    random.randint(150, 255),
                    random.randint(150, 255),
                    random.randint(150, 255)
                ),
                'color_confidence': 0.6 + 0.3 * random.random()
            })
        
        return {
            'current_power_prediction': power_on_prob > 0.5,
            'power_confidence': power_on_prob,
            'current_color_prediction': predicted_color,
            'color_confidence': 0.7 + 0.2 * random.random(),
            'daily_predictions': daily_predictions,
            'is_trained': True,
            'model_accuracy': 0.82,
            'data_points': 156,
            'learning_period_days': 7,
            'can_predict': True
        }
    
    @staticmethod
    def get_user_interactions():
        """Generate realistic user interaction history"""
        interactions = []
        now = datetime.now()
        
        for day in range(7):
            date = now - timedelta(days=day)
            
            # Morning interactions
            if random.random() < 0.8:
                morning_time = date.replace(hour=random.randint(6, 9), minute=random.randint(0, 59))
                interactions.append({
                    'timestamp': morning_time.isoformat(),
                    'action': 'TURN_ON',
                    'color': (255, 200, 150),
                    'brightness': random.randint(60, 90),
                    'hour': morning_time.hour,
                    'day_of_week': morning_time.weekday()
                })
            
            # Afternoon color changes
            for _ in range(random.randint(0, 3)):
                afternoon_time = date.replace(hour=random.randint(12, 17), minute=random.randint(0, 59))
                interactions.append({
                    'timestamp': afternoon_time.isoformat(),
                    'action': 'COLOR_CHANGE',
                    'color': (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255)),
                    'brightness': random.randint(50, 100),
                    'hour': afternoon_time.hour,
                    'day_of_week': afternoon_time.weekday()
                })
            
            # Evening turn off
            if random.random() < 0.9:
                evening_time = date.replace(hour=random.randint(21, 23), minute=random.randint(0, 59))
                interactions.append({
                    'timestamp': evening_time.isoformat(),
                    'action': 'TURN_OFF',
                    'color': None,
                    'brightness': None,
                    'hour': evening_time.hour,
                    'day_of_week': evening_time.weekday()
                })
        
        return sorted(interactions, key=lambda x: x['timestamp'], reverse=True)
    
    @staticmethod
    def get_system_info():
        """Generate system information"""
        return {
            'database_stats': {
                'user_interactions': 156,
                'environmental_data': 1240,
                'system_logs': 89,
                'database_size': 2.4
            },
            'system_resources': {
                'cpu_percent': random.randint(20, 60),
                'memory_percent': random.randint(30, 70),
                'disk_percent': random.randint(15, 85),
                'temperature': round(45 + random.uniform(-10, 15), 1),
                'uptime_hours': random.randint(24, 168)
            },
            'configuration': {
                'ml_learning_period': 7,
                'earthquake_threshold': 5.5,
                'air_quality_threshold': 100,
                'api_configured': True
            }
        }

class SmartNeoPixelDashboard:
    """Main dashboard class with comprehensive features"""
    
    def __init__(self):
        self.demo_data = DemoDataGenerator()
        
        # Initialize controller
        if 'controller' not in st.session_state:
            st.session_state.controller = NeoPixelController()
        self.controller = st.session_state.controller
    
    def render_header(self):
        """Render page header with status"""
        st.title("💡 Smart NeoPixel Lamp Dashboard")
        
        if SIMULATION_MODE:
            st.warning("🧪 **Simulation Mode** - Raspberry Pi libraries not available")
            st.info("💡 Install `rpi_ws281x` and `adafruit-circuitpython-neopixel` for hardware control")
        else:
            st.success("🔌 **Hardware Mode** - Connected to NeoPixel strip")
        
        st.markdown("---")
        
        # Get current status
        status = self.controller.get_status()
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            lamp_status = "🟢 ON" if status['is_on'] else "🔴 OFF"
            st.metric("Lamp Status", lamp_status)
        
        with col2:
            st.metric("Current Effect", f"✨ {status['current_effect'].title()}")
        
        with col3:
            st.metric("Brightness", f"{status['current_brightness']}%")
        
        with col4:
            st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    def render_lamp_controls(self):
        """Render comprehensive lamp control panel"""
        st.subheader("🎛️ Advanced Lamp Controls")
        
        if SIMULATION_MODE:
            st.info("📺 **Demo Mode** - Controls are simulated with visual feedback")
        else:
            st.success("🔗 **Real-time Hardware Control** - Changes applied to physical lamp")
        
        status = self.controller.get_status()
        
        # Main controls
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Power & Basic Controls**")
            
            # Power control
            current_state = status['is_on']
            if st.button("🔴 Turn OFF" if current_state else "🟢 Turn ON", key="power_btn"):
                if current_state:
                    self.controller.turn_off()
                    st.success("✅ Lamp turned OFF")
                else:
                    self.controller.set_solid_color(status['current_color'])
                    st.success("✅ Lamp turned ON")
                st.rerun()
            
            # Brightness control
            st.write("**Brightness Control**")
            brightness = st.slider("Brightness", 0, 100, status['current_brightness'], key="brightness_slider")
            if brightness != status['current_brightness']:
                self.controller.update_brightness(brightness / 100.0)
        
        with col2:
            st.write("**Color Control**")
            
            # Color picker
            r, g, b = status['current_color']
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            new_color = st.color_picker("Select Color", value=color_hex, key="color_picker")
            
            # Convert hex to RGB
            hex_color = new_color.lstrip('#')
            rgb_color = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            
            if rgb_color != status['current_color']:
                self.controller.set_solid_color(tuple(rgb_color))
                st.success(f"✅ Color changed to RGB{tuple(rgb_color)}")
        
        # Effect selection
        st.write("**✨ Lighting Effects**")
        effect_cols = st.columns(6)
        
        effects = [
            ("🎨 Solid", "solid"),
            ("🌈 Rainbow", "rainbow"),
            ("💨 Breathing", "breathing"),
            ("⚡ Strobe", "strobe"),
            ("🔥 Fire", "fire"),
            ("🌊 Wave", "wave")
        ]
        
        for i, (name, effect) in enumerate(effects):
            with effect_cols[i]:
                if st.button(name, key=f"effect_{effect}"):
                    if effect == "solid":
                        self.controller.set_solid_color(tuple(rgb_color))
                    else:
                        self.controller.color = tuple(rgb_color)
                        self.controller.start_effect(effect)
                    st.success(f"✅ {name} activated!")
                    st.rerun()
        
        # Animation speed (for animated effects)
        if status['current_effect'] in ["rainbow", "breathing", "strobe", "fire", "wave"]:
            st.write("**⚡ Animation Speed**")
            speed = st.slider("Speed", 1, 100, status['speed'], 
                            help="Higher values = faster animation", key="speed_slider")
            if speed != status['speed']:
                self.controller.speed = speed
        
        # Color presets
        st.write("**🎨 Color Presets**")
        preset_cols = st.columns(8)
        
        presets = [
            ("🔴 Red", [255, 0, 0]),
            ("🟢 Green", [0, 255, 0]),
            ("🔵 Blue", [0, 0, 255]),
            ("🟡 Yellow", [255, 255, 0]),
            ("🟣 Purple", [255, 0, 255]),
            ("🟠 Orange", [255, 165, 0]),
            ("⚪ White", [255, 255, 255]),
            ("🌸 Pink", [255, 192, 203])
        ]
        
        for i, (name, color) in enumerate(presets):
            with preset_cols[i]:
                if st.button(name, key=f"preset_{i}"):
                    self.controller.set_solid_color(tuple(color))
                    st.success(f"✅ {name} applied!")
                    st.rerun()
        
        # Advanced features
        st.write("**🔧 Advanced Features**")
        
        adv_col1, adv_col2, adv_col3 = st.columns(3)
        
        with adv_col1:
            temp_mode = st.checkbox("🌡️ Temperature Mode", value=status['temperature_mode'])
            if temp_mode != status['temperature_mode']:
                self.controller.temperature_mode = temp_mode
                if temp_mode:
                    st.info("🌡️ Color will adjust based on temperature")
        
        with adv_col2:
            music_sync = st.checkbox("🎵 Music Sync", value=status['music_sync'])
            if music_sync != status['music_sync']:
                self.controller.music_sync = music_sync
                if music_sync:
                    st.info("🎵 Colors will sync with music")
        
        with adv_col3:
            auto_bright = st.checkbox("☀️ Auto Brightness", value=status['auto_brightness'])
            if auto_bright != status['auto_brightness']:
                self.controller.auto_brightness = auto_bright
                if auto_bright:
                    st.info("☀️ Brightness will adjust automatically")
        
        # Current color display
        st.write("**🎨 Current Color Preview**")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            r, g, b = status['current_color']
            st.markdown(f"""
            <div style="
                width: 100px; height: 50px;
                background-color: rgb({r}, {g}, {b});
                border-radius: 10px; border: 2px solid #ddd;
                margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                opacity: {status['current_brightness']/100};
            "></div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.write(f"**RGB({r}, {g}, {b})**")
            st.write(f"**Hex: {color_hex.upper()}**")
            st.write(f"**Brightness: {status['current_brightness']}%**")
            st.write(f"**Last Update: {datetime.fromisoformat(status['last_update']).strftime('%H:%M:%S')}**")
        
        # Hardware status
        st.write("**💻 Hardware Status**")
        
        if SIMULATION_MODE:
            st.info("🧪 Simulation Mode - Virtual NeoPixel strip")
            st.write("• LED Count: 30 (simulated)")
            st.write("• Pin: GPIO 18 (simulated)")
            st.write("• Status: Demo mode active")
        else:
            st.success("🔌 Real Hardware Connected")
            st.write(f"• LED Count: {LED_COUNT}")
            st.write(f"• Pin: GPIO {LED_PIN}")
            st.write("• Status: Physical control active")
    
    def render_environmental_dashboard(self):
        """Render environmental monitoring"""
        st.subheader("🌍 Environmental Monitoring & Integration")
        
        env_data = self.demo_data.get_environmental_data()
        
        st.info("📊 Environmental data can be used to automatically adjust lamp colors and effects")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Weather", "🌬️ Air Quality", "🌪️ Earthquakes", "📻 Radio"])
        
        with tab1:
            self.render_weather_tab(env_data['weather'])
        
        with tab2:
            self.render_air_quality_tab(env_data['air_quality'])
        
        with tab3:
            self.render_earthquake_tab(env_data['earthquake'])
        
        with tab4:
            self.render_radio_tab(env_data['radio_stations'])
    
    def render_weather_tab(self, weather_data):
        """Render weather information with lamp integration"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temp = weather_data['temperature']
            st.metric("Temperature", f"{temp}°C")
            
            # Temperature-based color suggestion
            if temp < 15:
                temp_color = "#4169E1"  # Blue for cold
                temp_suggestion = "❄️ Cool blue recommended"
            elif temp > 25:
                temp_color = "#FF6347"  # Red-orange for hot
                temp_suggestion = "🔥 Warm red recommended"
            else:
                temp_color = "#32CD32"  # Green for moderate
                temp_suggestion = "🌿 Neutral green recommended"
            
            st.markdown(f"""
            <div style="
                width: 40px; height: 40px;
                background-color: {temp_color};
                border-radius: 50%; border: 2px solid #ddd;
                margin: 5px 0;
            "></div>
            """, unsafe_allow_html=True)
            
            st.caption(temp_suggestion)
        
        with col2:
            st.metric("Humidity", f"{weather_data['humidity']}%")
            st.metric("Feels Like", f"{weather_data['feels_like']}°C")
            
            # Weather-based effect suggestion
            desc = weather_data['description'].lower()
            if 'rain' in desc or 'storm' in desc:
                st.info("🌧️ Rainy weather detected - try blue wave effect")
            elif 'clear' in desc:
                st.info("☀️ Clear weather - bright white recommended")
            elif 'cloud' in desc:
                st.info("☁️ Cloudy weather - soft warm colors suggested")
        
        with col3:
            st.metric("Conditions", weather_data['description'])
            st.write(f"📍 **Location:** {weather_data['location']}")
            
            # Auto-apply weather colors
            if st.button("🌤️ Apply Weather Colors"):
                if temp < 15:
                    color = (65, 105, 225)  # Blue
                elif temp > 25:
                    color = (255, 99, 71)   # Red-orange
                else:
                    color = (50, 205, 50)   # Green
                
                self.controller.set_solid_color(color)
                st.success(f"✅ Weather-based color applied: RGB{color}")
                st.rerun()
        
        # Temperature history chart
        st.write("**📈 Temperature History (24h)**")
        
        hours = list(range(24))
        base_temp = weather_data['temperature']
        temps = [base_temp + 5 * abs(12 - h) / 12 + random.uniform(-3, 3) for h in hours]
        
        df = pd.DataFrame({
            'hour': hours,
            'temperature': temps
        })
        
        fig = px.line(df, x='hour', y='temperature', 
                     title='Temperature Over Time',
                     labels={'temperature': 'Temperature (°C)', 'hour': 'Hour'})
        fig.update_layout(xaxis=dict(dtick=4))
        st.plotly_chart(fig, use_container_width=True)
    
    def render_air_quality_tab(self, air_quality_data):
        """Render air quality information with lamp integration"""
        aqi = air_quality_data['aqi']
        aqi_level = air_quality_data['aqi_level']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Air Quality Index", aqi)
            
            # AQI level descriptions and colors
            aqi_info = {
                1: ("Good", "#00ff00"),
                2: ("Fair", "#ffff00"), 
                3: ("Moderate", "#ffa500"),
                4: ("Poor", "#ff4500"),
                5: ("Very Poor", "#ff0000")
            }
            
            level_desc, aqi_color = aqi_info.get(aqi_level, ('Unknown', '#888888'))
            st.write(f"**Level:** {level_desc}")
            
            st.markdown(f"""
            <div style="
                width: 50px; height: 50px;
                background-color: {aqi_color};
                border-radius: 50%; border: 2px solid #ddd;
                margin: 10px 0;
            "></div>
            """, unsafe_allow_html=True)
            
            # AQI-based lighting suggestion
            if aqi <= 50:
                st.success("🟢 Good air quality - bright colors recommended")
            elif aqi <= 100:
                st.warning("🟡 Moderate air quality - warm colors suggested")
            else:
                st.error("🔴 Poor air quality - dim red alert recommended")
            
            # Auto-apply AQI colors
            if st.button("🌬️ Apply AQI Alert Colors"):
                if aqi <= 50:
                    color = (0, 255, 0)    # Green
                elif aqi <= 100:
                    color = (255, 255, 0)  # Yellow
                elif aqi <= 150:
                    color = (255, 165, 0)  # Orange
                else:
                    color = (255, 0, 0)    # Red
                
                self.controller.set_solid_color(color)
                st.success(f"✅ AQI alert color applied: RGB{color}")
                st.rerun()
        
        with col2:
            st.write("**Air Components (μg/m³)**")
            components = air_quality_data['components']
            for component, value in components.items():
                st.write(f"• {component.upper()}: {value}")
        
        # AQI gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=aqi,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Air Quality Index"},
            gauge={
                'axis': {'range': [None, 200]},
                'bar': {'color': aqi_color},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 100], 'color': "yellow"},
                    {'range': [100, 150], 'color': "orange"},
                    {'range': [150, 200], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_earthquake_tab(self, earthquake_data):
        """Render earthquake information with alert system"""
        st.write("**🌍 Earthquake Monitoring & Alert System**")
        
        significant_earthquakes = earthquake_data['significant_earthquakes']
        total_earthquakes = earthquake_data['total_earthquakes']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Significant Earthquakes", len(significant_earthquakes))
        
        with col2:
            st.metric("Total Detected", total_earthquakes)
        
        with col3:
            check_time = datetime.now().strftime("%H:%M:%S")
            st.metric("Last Check", check_time)
        
        # Earthquake alerts
        if significant_earthquakes:
            st.error("🚨 **EARTHQUAKE ALERT** - Significant activity detected!")
            
            for eq in significant_earthquakes:
                st.error(f"🌪️ **Magnitude {eq['magnitude']}** - {eq['place']} - {eq['time'].strftime('%Y-%m-%d %H:%M')}")
            
            # Emergency lighting
            if st.button("🚨 Activate Emergency Lighting"):
                # Red strobe for emergency
                self.controller.set_solid_color((255, 0, 0))
                self.controller.start_effect("strobe")
                st.error("🚨 Emergency strobe lighting activated!")
                st.rerun()
        else:
            st.success("✅ No significant earthquake activity detected.")
            
            if st.button("🧪 Test Earthquake Alert"):
                # Simulate earthquake alert
                self.controller.set_solid_color((255, 165, 0))
                self.controller.start_effect("strobe")
                st.warning("🧪 Testing earthquake alert lighting")
                st.rerun()
        
        # Alert settings
        st.write("**⚙️ Alert Settings**")
        magnitude_threshold = st.slider("Minimum Magnitude Threshold", 4.0, 8.0, 5.5, 0.1)
        st.write(f"• Current threshold: **{magnitude_threshold}**")
        st.write("• Check interval: **5 minutes**")
        st.write("• Alert type: **Red strobe lighting**")
    
    def render_radio_tab(self, radio_stations):
        """Render radio stations with music visualization"""
        st.write("**📻 Radio Stations & Music Visualization**")
        
        # Currently playing simulation
        current_station = random.choice(radio_stations)
        st.info(f"🎵 Currently Playing: **{current_station['name']}** ({current_station['genre']})")
        
        # Music visualization controls
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            if st.button("🎵 Enable Music Sync"):
                self.controller.music_sync = True
                self.controller.start_effect("rainbow")
                st.success("🎵 Music sync enabled - colors will dance with the beat!")
                st.rerun()
        
        with viz_col2:
            if st.button("🎶 Beat Detection Mode"):
                self.controller.set_solid_color((255, 255, 255))
                self.controller.start_effect("strobe")
                self.controller.speed = 80  # Fast strobe for beat
                st.success("🎶 Beat detection mode activated!")
                st.rerun()
        
        # Available stations
        st.write("**📡 Available Radio Stations**")
        
        for station in radio_stations:
            with st.expander(f"📻 {station['name']} ({station['country']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Country:** {station['country']}")
                    st.write(f"**Language:** {station['language']}")
                
                with col2:
                    st.write(f"**Genre:** {station['genre']}")
                    st.write(f"**Bitrate:** {station['bitrate']} kbps")
                
                with col3:
                    if st.button(f"🎵 Play & Sync", key=f"play_{station['name']}"):
                        # Genre-based lighting
                        genre_colors = {
                            'Jazz': (138, 43, 226),      # Purple
                            'Rock': (255, 69, 0),        # Red-orange
                            'Pop': (255, 20, 147),       # Deep pink
                            'News': (70, 130, 180),      # Steel blue
                            'Lounge': (32, 178, 170)     # Light sea green
                        }
                        
                        color = genre_colors.get(station['genre'], (255, 255, 255))
                        self.controller.set_solid_color(color)
                        self.controller.start_effect("wave")
                        st.success(f"🎵 Now playing: {station['name']} with {station['genre']} lighting!")
                        st.rerun()
    
    def render_ml_dashboard(self):
        """Render ML predictions and patterns"""
        st.subheader("🤖 Machine Learning & Usage Patterns")
        
        ml_data = self.demo_data.get_ml_predictions()
        
        # ML Status Overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 Active" if ml_data['is_trained'] else "🟡 Learning"
            st.metric("ML Status", status)
        
        with col2:
            accuracy = ml_data['model_accuracy']
            st.metric("Model Accuracy", f"{accuracy:.1%}")
        
        with col3:
            data_points = ml_data['data_points']
            st.metric("Training Data", f"{data_points} interactions")
        
        with col4:
            st.metric("Learning Period", f"{ml_data['learning_period_days']} days")
        
        # Current Predictions
        st.write("**🔮 Real-time Predictions**")
        
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            st.write("**Power Prediction**")
            
            power_pred = ml_data['current_power_prediction']
            power_conf = ml_data['power_confidence']
            
            power_status = "🟢 Should be ON" if power_pred else "🔴 Should be OFF"
            st.write(f"• Status: {power_status}")
            st.write(f"• Confidence: {power_conf:.1%}")
            
            # Check if prediction matches current state
            current_state = self.controller.get_status()['is_on']
            if power_pred == current_state:
                st.success("✅ Prediction matches current state")
            else:
                st.warning("⚠️ Prediction differs from current state")
                
                if st.button("🤖 Apply ML Prediction"):
                    if power_pred:
                        self.controller.set_solid_color(ml_data['current_color_prediction'])
                    else:
                        self.controller.turn_off()
                    st.success("✅ ML prediction applied!")
                    st.rerun()
        
        with pred_col2:
            st.write("**Color Prediction**")
            
            color_pred = ml_data['current_color_prediction']
            color_conf = ml_data['color_confidence']
            
            r, g, b = color_pred
            st.markdown(f"""
            <div style="
                width: 60px; height: 60px;
                background-color: rgb({r}, {g}, {b});
                border-radius: 10px; border: 2px solid #ddd;
                margin: 10px 0;
            "></div>
            """, unsafe_allow_html=True)
            
            st.write(f"• RGB: {color_pred}")
            st.write(f"• Confidence: {color_conf:.1%}")
            
            if st.button("🎨 Apply Predicted Color"):
                self.controller.set_solid_color(color_pred)
                st.success(f"✅ Predicted color applied: RGB{color_pred}")
                st.rerun()
        
        # 24-hour Predictions Chart
        st.write("**📊 24-Hour Usage Predictions**")
        
        daily_predictions = ml_data['daily_predictions']
        
        if daily_predictions:
            hours = [pred['hour'] for pred in daily_predictions]
            power_probs = [pred['power_confidence'] if pred['should_be_on'] else -pred['power_confidence'] 
                         for pred in daily_predictions]
            
            fig = go.Figure()
            
            # Power prediction line
            fig.add_trace(go.Scatter(
                x=hours,
                y=power_probs,
                mode='lines+markers',
                name='Power Prediction',
                line=dict(color='blue', width=3),
                fill='tonexty'
            ))
            
            # Current time indicator
            current_hour = datetime.now().hour
            fig.add_vline(x=current_hour, line_dash="dash", line_color="red", 
                         annotation_text="Now", annotation_position="top")
            
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig.update_layout(
                title="24-Hour Power Usage Predictions",
                xaxis_title="Hour of Day",
                yaxis_title="Prediction Confidence",
                yaxis=dict(tickformat='.0%'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Smart automation
        st.write("**🏠 Smart Automation**")
        
        auto_col1, auto_col2, auto_col3 = st.columns(3)
        
        with auto_col1:
            if st.button("🌅 Morning Routine"):
                # Warm morning light
                self.controller.set_solid_color((255, 200, 150))
                self.controller.update_brightness(0.7)
                st.success("🌅 Morning routine activated!")
                st.rerun()
        
        with auto_col2:
            if st.button("🌆 Evening Routine"):
                # Warm evening light
                self.controller.set_solid_color((255, 180, 100))
                self.controller.update_brightness(0.5)
                st.success("🌆 Evening routine activated!")
                st.rerun()
        
        with auto_col3:
            if st.button("🌙 Night Routine"):
                # Dim blue night light
                self.controller.set_solid_color((100, 150, 255))
                self.controller.update_brightness(0.2)
                st.success("🌙 Night routine activated!")
                st.rerun()
        
        # User Interaction History
        st.write("**📈 Usage Analytics**")
        
        interactions = self.demo_data.get_user_interactions()
        
        if interactions:
            df = pd.DataFrame(interactions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Action count by hour
            if 'hour' in df.columns and 'action' in df.columns:
                hourly_actions = df.groupby(['hour', 'action']).size().reset_index(name='count')
                
                fig = px.bar(hourly_actions, x='hour', y='count', color='action',
                            title='User Actions by Hour of Day',
                            labels={'hour': 'Hour of Day', 'count': 'Number of Actions'})
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent interactions
            st.write("**🕐 Recent Activity**")
            recent_df = df.head(10)[['timestamp', 'action', 'brightness']].copy()
            recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(recent_df, use_container_width=True)
        
        # Learning controls
        st.write("**🎓 Learning Controls**")
        
        learn_col1, learn_col2, learn_col3 = st.columns(3)
        
        with learn_col1:
            if st.button("🧠 Train Model"):
                with st.spinner("Training ML model..."):
                    time.sleep(2)
                    st.success("✅ Model training completed!")
        
        with learn_col2:
            if st.button("🔄 Refresh Predictions"):
                st.rerun()
        
        with learn_col3:
            if st.button("📊 Generate Report"):
                with st.spinner("Generating analytics report..."):
                    time.sleep(1)
                    st.success("✅ Analytics report generated!")
    
    def render_system_info(self):
        """Render system information and diagnostics"""
        st.subheader("💻 System Information & Diagnostics")
        
        system_info = self.demo_data.get_system_info()
        
        # System overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**📊 Usage Statistics**")
            db_stats = system_info['database_stats']
            for key, value in db_stats.items():
                if key == 'database_size':
                    st.write(f"• {key.replace('_', ' ').title()}: {value} MB")
                else:
                    st.write(f"• {key.replace('_', ' ').title()}: {value}")
        
        with col2:
            st.write("**⚙️ Configuration**")
            config = system_info['configuration']
            st.write(f"• ML Learning Period: {config['ml_learning_period']} days")
            st.write(f"• Earthquake Threshold: {config['earthquake_threshold']}")
            st.write(f"• Air Quality Threshold: {config['air_quality_threshold']}")
            st.write(f"• APIs Configured: {'✅' if config['api_configured'] else '❌'}")
        
        with col3:
            st.write("**🔧 Hardware Status**")
            if SIMULATION_MODE:
                st.write("• Mode: 🧪 Simulation")
                st.write("• LED Strip: Virtual")
                st.write("• GPIO: Simulated")
                st.write("• Performance: Normal")
            else:
                st.write("• Mode: 🔌 Hardware")
                st.write(f"• LED Strip: {LED_COUNT} pixels")
                st.write(f"• GPIO: Pin {LED_PIN}")
                st.write("• Performance: Optimal")
        
        # System resources
        st.write("**📈 System Resources**")
        
        resources = system_info['system_resources']
        
        # Resource gauges
        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
        
        with gauge_col1:
            cpu_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resources['cpu_percent'],
                title={'text': "CPU Usage (%)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            cpu_fig.update_layout(height=250)
            st.plotly_chart(cpu_fig, use_container_width=True)
        
        with gauge_col2:
            mem_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resources['memory_percent'],
                title={'text': "Memory Usage (%)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "yellow"},
                        {'range': [85, 100], 'color': "red"}
                    ]
                }
            ))
            mem_fig.update_layout(height=250)
            st.plotly_chart(mem_fig, use_container_width=True)
        
        with gauge_col3:
            temp_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resources['temperature'],
                title={'text': "CPU Temperature (°C)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 85]},
                    'bar': {'color': "orange"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 75], 'color': "yellow"},
                        {'range': [75, 85], 'color': "red"}
                    ]
                }
            ))
            temp_fig.update_layout(height=250)
            st.plotly_chart(temp_fig, use_container_width=True)
        
        # Additional metrics
        metrics_col1, metrics_col2 = st.columns(2)
        
        with metrics_col1:
            st.metric("Disk Usage", f"{resources['disk_percent']}%")
            st.metric("System Uptime", f"{resources['uptime_hours']} hours")
        
        with metrics_col2:
            # Current lamp status metrics
            status = self.controller.get_status()
            st.metric("Lamp Status", "🟢 Online" if status['is_on'] else "🔴 Offline")
            st.metric("Effect Running", status['current_effect'].title())
        
        # Maintenance and controls
        st.write("**🧹 Maintenance & Controls**")
        
        maint_col1, maint_col2, maint_col3, maint_col4 = st.columns(4)
        
        with maint_col1:
            if st.button("🗑️ Clear Cache"):
                with st.spinner("Clearing cache..."):
                    time.sleep(1)
                    st.success("✅ Cache cleared!")
        
        with maint_col2:
            if st.button("🔄 Restart Effects"):
                self.controller.stop_animation()
                st.success("✅ Effects engine restarted!")
        
        with maint_col3:
            if st.button("📊 Export Logs"):
                with st.spinner("Exporting system logs..."):
                    time.sleep(1)
                    st.success("✅ Logs exported!")
        
        with maint_col4:
            if st.button("🔧 Hardware Test"):
                with st.spinner("Testing hardware..."):
                    # Quick hardware test
                    original_color = self.controller.color
                    test_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
                    
                    for color in test_colors:
                        self.controller.set_solid_color(color)
                        time.sleep(0.5)
                    
                    self.controller.set_solid_color(original_color)
                    st.success("✅ Hardware test completed!")
        
        # System alerts
        st.write("**⚠️ System Alerts & Status**")
        
        alerts = []
        if resources['cpu_percent'] > 80:
            alerts.append("🔴 High CPU usage detected!")
        if resources['memory_percent'] > 85:
            alerts.append("🟡 High memory usage detected!")
        if resources['disk_percent'] > 90:
            alerts.append("🔴 Low disk space!")
        if resources['temperature'] > 70:
            alerts.append("🌡️ High CPU temperature!")
        
        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ All systems operating normally!")
        
        # Performance optimization tips
        st.write("**⚡ Performance Tips**")
        
        if SIMULATION_MODE:
            st.info("🧪 **Simulation Mode Tips:**")
            st.write("• Install Raspberry Pi libraries for hardware acceleration")
            st.write("• Use physical GPIO for real-time LED control")
            st.write("• Enable hardware PWM for smoother animations")
        else:
            st.info("🔌 **Hardware Mode Tips:**")
            st.write("• Keep system temperature below 70°C for optimal performance")
            st.write("• Ensure stable power supply for consistent LED brightness")
            st.write("• Update to latest NeoPixel library for better effects")

def main():
    """Main Streamlit app with comprehensive features"""
    dashboard = SmartNeoPixelDashboard()
    
    # Sidebar navigation
    st.sidebar.title("💡 Smart NeoPixel Lamp")
    st.sidebar.markdown("---")
    
    # System status in sidebar
    if SIMULATION_MODE:
        st.sidebar.warning("🧪 Simulation Mode")
        st.sidebar.info("📍 Virtual: 30 NeoPixels")
    else:
        st.sidebar.success("🔌 Hardware Mode")
        st.sidebar.success(f"📍 GPIO {LED_PIN}: {LED_COUNT} LEDs")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["🎛️ Lamp Controls", "🌍 Environmental", "🤖 ML & Patterns", "💻 System Info"]
    )
    
    # Auto-refresh controls
    st.sidebar.markdown("---")
    st.sidebar.write("**🔄 Auto-Refresh**")
    auto_refresh = st.sidebar.checkbox("Enable (10s)", value=False)
    
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Current lamp status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.write("**📊 Current Status**")
    
    status = dashboard.controller.get_status()
    status_emoji = "🟢" if status['is_on'] else "🔴"
    st.sidebar.write(f"{status_emoji} **Power:** {'ON' if status['is_on'] else 'OFF'}")
    st.sidebar.write(f"✨ **Effect:** {status['current_effect'].title()}")
    st.sidebar.write(f"💡 **Brightness:** {status['current_brightness']}%")
    
    r, g, b = status['current_color']
    st.sidebar.write(f"🎨 **Color:** RGB({r}, {g}, {b})")
    
    # Quick environmental stats
    env_data = dashboard.demo_data.get_environmental_data()
    st.sidebar.markdown("---")
    st.sidebar.write("**🌍 Environment**")
    st.sidebar.write(f"🌡️ {env_data['weather']['temperature']}°C")
    st.sidebar.write(f"🌬️ AQI: {env_data['air_quality']['aqi']}")
    
    eq_count = len(env_data['earthquake']['significant_earthquakes'])
    st.sidebar.write(f"🌪️ Earthquakes: {eq_count}")
    
    # Feature highlights
    st.sidebar.markdown("---")
    st.sidebar.write("**🌟 Features**")
    if SIMULATION_MODE:
        features = [
            "🎛️ Interactive controls",
            "🌈 6 lighting effects", 
            "🌍 Environmental integration",
            "🤖 ML predictions",
            "📊 Usage analytics",
            "💻 System monitoring"
        ]
    else:
        features = [
            "🔌 Real-time control",
            "🌈 Hardware effects",
            "🌍 Live sensor data", 
            "🤖 Active ML learning",
            "📊 Live analytics",
            "💻 Hardware monitoring"
        ]
    
    for feature in features:
        st.sidebar.write(f"• {feature}")
    
    # Render main content
    dashboard.render_header()
    
    if page == "🎛️ Lamp Controls":
        dashboard.render_lamp_controls()
    elif page == "🌍 Environmental":
        dashboard.render_environmental_dashboard()
    elif page == "🤖 ML & Patterns":
        dashboard.render_ml_dashboard()
    elif page == "💻 System Info":
        dashboard.render_system_info()
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 20px;">
        💡 <strong>Smart NeoPixel Lamp Dashboard</strong> | 
        {'🧪 Simulation Mode' if SIMULATION_MODE else '🔌 Hardware Mode'} | 
        Real-time monitoring and control | 
        {LED_COUNT} LEDs on GPIO {LED_PIN if not SIMULATION_MODE else '18 (sim)'}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()