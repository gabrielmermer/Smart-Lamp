"""
Smart Lamp Web Dashboard

Streamlit web interface for monitoring and controlling the Smart Lamp.
Works on any system with demo data when not on Raspberry Pi.

Access: http://localhost:8501
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Page configuration
st.set_page_config(
    page_title="Smart Lamp Dashboard",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if running on Raspberry Pi
RASPBERRY_PI = os.path.exists('/sys/class/thermal/thermal_zone0/temp')

class DemoDataGenerator:
    """Generate realistic demo data for development/demo purposes"""
    
    @staticmethod
    def get_lamp_state():
        """Get current lamp state (demo or real)"""
        if 'lamp_state' not in st.session_state:
            st.session_state.lamp_state = {
                'is_on': True,
                'current_color': [255, 180, 100],  # Warm orange
                'current_brightness': 75,
                'mode': 'AUTO',
                'last_update': datetime.now().isoformat()
            }
        return st.session_state.lamp_state
    
    @staticmethod
    def get_environmental_data():
        """Generate realistic environmental data"""
        now = datetime.now()
        
        # Temperature based on time of day (realistic pattern)
        hour = now.hour
        base_temp = 20 + 8 * abs(12 - hour) / 12  # Warmer midday, cooler at night
        temperature = base_temp + random.uniform(-2, 2)
        
        # Air quality (varies throughout day)
        base_aqi = 60 + 20 * (hour > 7 and hour < 19)  # Higher during day
        aqi = max(20, min(150, base_aqi + random.uniform(-15, 15)))
        
        # Simulate some earthquake activity (rare)
        earthquakes = []
        if random.random() < 0.1:  # 10% chance of earthquake data
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
                'location': 'Incheon, South Korea',
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
        
        # Realistic power predictions based on time
        if 6 <= hour <= 22:  # Daytime
            power_on_prob = 0.8 - 0.3 * abs(14 - hour) / 8  # Peak at 2 PM
        else:  # Nighttime
            power_on_prob = 0.2
        
        power_on_prob = max(0.1, min(0.9, power_on_prob + random.uniform(-0.1, 0.1)))
        
        # Color predictions based on time of day
        if 6 <= hour <= 10:  # Morning - warm colors
            predicted_color = (255, 200, 150)
        elif 11 <= hour <= 16:  # Afternoon - bright white
            predicted_color = (255, 255, 255)
        elif 17 <= hour <= 21:  # Evening - warm orange
            predicted_color = (255, 180, 100)
        else:  # Night - dim blue
            predicted_color = (100, 150, 255)
        
        # Add some randomness
        predicted_color = tuple(max(50, min(255, c + random.randint(-30, 30))) for c in predicted_color)
        
        # Generate 24-hour predictions
        daily_predictions = []
        for h in range(24):
            if 6 <= h <= 22:
                should_be_on = True
                confidence = 0.7 + 0.2 * random.random()
            else:
                should_be_on = False
                confidence = 0.6 + 0.3 * random.random()
            
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
        
        # Generate last 7 days of data
        for day in range(7):
            date = now - timedelta(days=day)
            
            # Morning interactions
            if random.random() < 0.8:  # 80% chance of morning use
                morning_time = date.replace(hour=random.randint(6, 9), minute=random.randint(0, 59))
                interactions.append({
                    'timestamp': morning_time.isoformat(),
                    'action': 'TURN_ON',
                    'color': (255, 200, 150),  # Warm morning light
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
            if random.random() < 0.9:  # 90% chance of evening turn off
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
                'database_size': 2.4  # MB
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

class SmartLampDashboard:
    """Main dashboard class"""
    
    def __init__(self):
        self.demo_data = DemoDataGenerator()
        
    def render_header(self):
        """Render page header with status"""
        st.title("🏮 Smart Lamp Dashboard")
        
        if not RASPBERRY_PI:
            st.info("🖥️ **Demo Mode** - Running on development system with simulated data")
        
        st.markdown("---")
        
        # Get current lamp state
        lamp_state = self.demo_data.get_lamp_state()
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 ON" if lamp_state['is_on'] else "🔴 OFF"
            st.metric("Lamp Status", status)
        
        with col2:
            mode = lamp_state.get('mode', 'MANUAL')
            st.metric("Mode", f"🔧 {mode}")
        
        with col3:
            brightness = lamp_state.get('current_brightness', 50)
            st.metric("Brightness", f"{brightness}%")
        
        with col4:
            st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    def render_lamp_controls(self):
        """Render lamp control panel"""
        st.subheader("🎛️ Lamp Controls")
        
        lamp_state = self.demo_data.get_lamp_state()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Power control
            st.write("**Power Control**")
            current_state = lamp_state['is_on']
            
            if st.button("🔴 Turn OFF" if current_state else "🟢 Turn ON", key="power_btn"):
                st.session_state.lamp_state['is_on'] = not current_state
                st.session_state.lamp_state['last_update'] = datetime.now().isoformat()
                st.rerun()
            
            # Mode control
            st.write("**Mode Control**")
            current_mode = lamp_state.get('mode', 'MANUAL')
            new_mode = st.selectbox("Mode", ["MANUAL", "AUTO"], 
                                  index=0 if current_mode == "MANUAL" else 1)
            
            if new_mode != current_mode:
                st.session_state.lamp_state['mode'] = new_mode
                st.rerun()
        
        with col2:
            # Color control
            st.write("**Color Control**")
            current_color = lamp_state['current_color']
            
            new_color = st.color_picker("Select Color", 
                                      value=f"#{current_color[0]:02x}{current_color[1]:02x}{current_color[2]:02x}")
            
            # Convert hex to RGB
            hex_color = new_color.lstrip('#')
            rgb_color = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            
            if rgb_color != current_color:
                st.session_state.lamp_state['current_color'] = rgb_color
                st.session_state.lamp_state['last_update'] = datetime.now().isoformat()
            
            # Brightness control
            st.write("**Brightness Control**")
            current_brightness = lamp_state['current_brightness']
            
            new_brightness = st.slider("Brightness", 0, 100, current_brightness)
            
            if new_brightness != current_brightness:
                st.session_state.lamp_state['current_brightness'] = new_brightness
                st.session_state.lamp_state['last_update'] = datetime.now().isoformat()
        
        # Color presets
        st.write("**Color Presets**")
        preset_cols = st.columns(6)
        
        presets = [
            ("🔴 Red", [255, 0, 0]),
            ("🟢 Green", [0, 255, 0]),
            ("🔵 Blue", [0, 0, 255]),
            ("🟡 Yellow", [255, 255, 0]),
            ("🟣 Purple", [255, 0, 255]),
            ("⚪ White", [255, 255, 255])
        ]
        
        for i, (name, color) in enumerate(presets):
            with preset_cols[i]:
                if st.button(name, key=f"preset_{i}"):
                    st.session_state.lamp_state['current_color'] = color
                    st.session_state.lamp_state['last_update'] = datetime.now().isoformat()
                    st.rerun()
        
        # Current color display
        st.write("**Current Color Preview**")
        r, g, b = lamp_state['current_color']
        st.markdown(f"""
        <div style="
            width: 100px;
            height: 50px;
            background-color: rgb({r}, {g}, {b});
            border-radius: 10px;
            border: 2px solid #ddd;
            margin: 10px 0;
        "></div>
        """, unsafe_allow_html=True)
        
        st.write(f"RGB({r}, {g}, {b})")
    
    def render_environmental_dashboard(self):
        """Render environmental monitoring"""
        st.subheader("🌍 Environmental Monitoring")
        
        env_data = self.demo_data.get_environmental_data()
        
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
        """Render weather information"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temp = weather_data['temperature']
            st.metric("Temperature", f"{temp}°C")
            
            # Temperature color indicator
            if temp < 18:
                temp_color = "#ff8c00"  # Orange for cold
            elif temp > 28:
                temp_color = "#00bfff"  # Blue for hot
            else:
                temp_color = "#ffffff"  # White for normal
            
            st.markdown(f"""
            <div style="
                width: 30px; height: 30px;
                background-color: {temp_color};
                border-radius: 50%; border: 2px solid #ddd;
                margin: 5px 0;
            "></div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric("Humidity", f"{weather_data['humidity']}%")
            st.metric("Feels Like", f"{weather_data['feels_like']}°C")
        
        with col3:
            st.metric("Conditions", weather_data['description'])
            st.write(f"📍 **Location:** {weather_data['location']}")
        
        # Generate temperature history chart
        st.write("**Temperature History (24h)**")
        
        # Create sample temperature data
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
        """Render air quality information"""
        aqi = air_quality_data['aqi']
        aqi_level = air_quality_data['aqi_level']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Air Quality Index", aqi)
            
            # AQI level description
            aqi_descriptions = {
                1: "Good",
                2: "Fair", 
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }
            
            level_desc = aqi_descriptions.get(aqi_level, 'Unknown')
            st.write(f"**Level:** {level_desc}")
            
            # Color indicator
            if aqi <= 50:
                aqi_color = "#00ff00"  # Green
            elif aqi <= 100:
                aqi_color = "#ffff00"  # Yellow
            elif aqi <= 150:
                aqi_color = "#ffa500"  # Orange
            else:
                aqi_color = "#ff0000"  # Red
            
            st.markdown(f"""
            <div style="
                width: 40px; height: 40px;
                background-color: {aqi_color};
                border-radius: 50%; border: 2px solid #ddd;
                margin: 10px 0;
            "></div>
            """, unsafe_allow_html=True)
        
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
        """Render earthquake information"""
        st.write("**Recent Earthquake Monitoring**")
        
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
        
        if significant_earthquakes:
            st.write("**Significant Earthquakes (≥5.5 magnitude)**")
            
            for eq in significant_earthquakes:
                st.error(f"🚨 **Magnitude {eq['magnitude']}** - {eq['place']} - {eq['time'].strftime('%Y-%m-%d %H:%M')}")
        else:
            st.success("✅ No significant earthquake activity detected.")
        
        # Settings display
        st.write("**Settings**")
        st.write("• Minimum magnitude threshold: **5.5**")
        st.write("• Check interval: **5 minutes**")
    
    def render_radio_tab(self, radio_stations):
        """Render radio stations"""
        st.write("**Available Radio Stations**")
        
        for station in radio_stations:
            with st.expander(f"📻 {station['name']} ({station['country']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Country:** {station['country']}")
                    st.write(f"**Language:** {station['language']}")
                
                with col2:
                    st.write(f"**Genre:** {station['genre']}")
                    st.write(f"**Bitrate:** {station['bitrate']} kbps")
                
                if st.button(f"🎵 Play {station['name']}", key=f"play_{station['name']}"):
                    st.success(f"🎵 Now playing: {station['name']}")
    
    def render_ml_dashboard(self):
        """Render ML predictions and patterns"""
        st.subheader("🤖 Machine Learning & Patterns")
        
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
            st.metric("Learning Period", "7 days")
        
        # Current Predictions
        st.write("**🔮 Current Predictions**")
        
        pred_col1, pred_col2 = st.columns(2)
        
        with pred_col1:
            st.write("**Power Prediction**")
            power_pred = ml_data['current_power_prediction']
            power_conf = ml_data['power_confidence']
            
            power_status = "🟢 Should be ON" if power_pred else "🔴 Should be OFF"
            st.write(f"• Status: {power_status}")
            st.write(f"• Confidence: {power_conf:.1%}")
            
            # Show if prediction matches current state
            current_state = self.demo_data.get_lamp_state()['is_on']
            if power_pred == current_state:
                st.success("✅ Prediction matches current state")
            else:
                st.warning("⚠️ Prediction differs from current state")
        
        with pred_col2:
            st.write("**Color Prediction**")
            color_pred = ml_data['current_color_prediction']
            color_conf = ml_data['color_confidence']
            
            r, g, b = color_pred
            st.markdown(f"""
            <div style="
                width: 50px; height: 50px;
                background-color: rgb({r}, {g}, {b});
                border-radius: 10px; border: 2px solid #ddd;
                margin: 10px 0;
            "></div>
            """, unsafe_allow_html=True)
            
            st.write(f"• RGB: {color_pred}")
            st.write(f"• Confidence: {color_conf:.1%}")
        
        # 24-hour Predictions Chart
        st.write("**📊 24-Hour Predictions**")
        
        daily_predictions = ml_data['daily_predictions']
        
        hours = [pred['hour'] for pred in daily_predictions]
        power_probs = [pred['power_confidence'] if pred['should_be_on'] else -pred['power_confidence'] 
                     for pred in daily_predictions]
        
        # Create prediction chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=power_probs,
            mode='lines+markers',
            name='Power Prediction',
            line=dict(color='blue'),
            fill='tonexty'
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="24-Hour Power Predictions",
            xaxis_title="Hour of Day",
            yaxis_title="Prediction Confidence",
            yaxis=dict(tickformat='.0%'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # User Interaction History
        st.write("**📈 User Interaction History**")
        
        interactions = self.demo_data.get_user_interactions()
        
        if interactions:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(interactions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Action count by hour
            hourly_actions = df.groupby(['hour', 'action']).size().reset_index(name='count')
            
            fig = px.bar(hourly_actions, x='hour', y='count', color='action',
                        title='User Actions by Hour of Day',
                        labels={'hour': 'Hour of Day', 'count': 'Number of Actions'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent interactions table
            st.write("**Recent Interactions**")
            recent_df = df.head(10)[['timestamp', 'action', 'brightness']].copy()
            recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(recent_df, use_container_width=True)
        
        # Manual controls
        st.write("**🔧 Manual Controls**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎓 Train Model Now"):
                with st.spinner("Training ML model..."):
                    time.sleep(2)  # Simulate training
                    st.success("✅ Model training completed!")
        
        with col2:
            if st.button("🔄 Refresh Predictions"):
                st.rerun()
    
    def render_system_info(self):
        """Render system information"""
        st.subheader("💻 System Information")
        
        system_info = self.demo_data.get_system_info()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**📊 Database Statistics**")
            db_stats = system_info['database_stats']
            for key, value in db_stats.items():
                if key == 'database_size':
                    st.write(f"• {key}: {value} MB")
                else:
                    st.write(f"• {key}: {value}")
        
        with col2:
            st.write("**⚙️ Configuration**")
            config = system_info['configuration']
            st.write(f"• ML Learning Period: {config['ml_learning_period']} days")
            st.write(f"• Earthquake Threshold: {config['earthquake_threshold']}")
            st.write(f"• Air Quality Threshold: {config['air_quality_threshold']}")
            st.write(f"• API Key Configured: {'✅' if config['api_configured'] else '❌'}")
        
        with col3:
            st.write("**💻 System Resources**")
            resources = system_info['system_resources']
            
            st.write(f"• CPU Usage: {resources['cpu_percent']}%")
            st.write(f"• Memory Usage: {resources['memory_percent']}%")
            st.write(f"• Disk Usage: {resources['disk_percent']}%")
            st.write(f"• CPU Temperature: {resources['temperature']}°C")
            st.write(f"• Uptime: {resources['uptime_hours']} hours")
        
        # System resource charts
        st.write("**📈 System Resources Chart**")
        
        # Create gauge charts for system resources
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
            disk_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resources['disk_percent'],
                title={'text': "Disk Usage (%)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "purple"},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 90], 'color': "yellow"},
                        {'range': [90, 100], 'color': "red"}
                    ]
                }
            ))
            disk_fig.update_layout(height=250)
            st.plotly_chart(disk_fig, use_container_width=True)
        
        # Maintenance controls
        st.write("**🧹 Maintenance**")
        
        maint_col1, maint_col2, maint_col3 = st.columns(3)
        
        with maint_col1:
            if st.button("🗑️ Cleanup Old Data"):
                with st.spinner("Cleaning up old data..."):
                    time.sleep(1)
                    st.success("✅ Old data cleaned up!")
        
        with maint_col2:
            if st.button("🔄 Force Sensor Check"):
                with st.spinner("Checking all sensors..."):
                    time.sleep(2)
                    st.success("✅ All sensors checked!")
        
        with maint_col3:
            if st.button("📊 Generate Report"):
                with st.spinner("Generating system report..."):
                    time.sleep(1)
                    st.success("✅ Report generated!")
        
        # System alerts
        st.write("**⚠️ System Alerts**")
        
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

def main():
    """Main Streamlit app"""
    dashboard = SmartLampDashboard()
    
    # Sidebar navigation
    st.sidebar.title("🏮 Smart Lamp")
    st.sidebar.markdown("---")
    
    # System status in sidebar
    if RASPBERRY_PI:
        st.sidebar.success("🍓 Running on Raspberry Pi")
    else:
        st.sidebar.info("🖥️ Demo Mode")
    
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["🎛️ Lamp Controls", "🌍 Environmental", "🤖 ML & Patterns", "💻 System Info"]
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (10s)", value=False)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Current status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.write("**Current Status:**")
    
    lamp_state = dashboard.demo_data.get_lamp_state()
    status_color = "🟢" if lamp_state['is_on'] else "🔴"
    st.sidebar.write(f"{status_color} Lamp: {'ON' if lamp_state['is_on'] else 'OFF'}")
    st.sidebar.write(f"🔧 Mode: {lamp_state.get('mode', 'MANUAL')}")
    st.sidebar.write(f"💡 Brightness: {lamp_state.get('current_brightness', 50)}%")
    
    r, g, b = lamp_state['current_color']
    st.sidebar.write(f"🎨 Color: RGB({r}, {g}, {b})")
    
    # Quick stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.write("**Quick Stats:**")
    
    env_data = dashboard.demo_data.get_environmental_data()
    st.sidebar.write(f"🌡️ Temperature: {env_data['weather']['temperature']}°C")
    st.sidebar.write(f"🌬️ AQI: {env_data['air_quality']['aqi']}")
    
    eq_count = len(env_data['earthquake']['significant_earthquakes'])
    st.sidebar.write(f"🌪️ Earthquakes: {eq_count}")
    
    # Demo data info
    st.sidebar.markdown("---")
    st.sidebar.write("**Demo Features:**")
    st.sidebar.write("• 🎛️ Interactive lamp controls")
    st.sidebar.write("• 📊 Real-time environmental data")
    st.sidebar.write("• 🤖 ML pattern predictions")
    st.sidebar.write("• 📈 Usage analytics")
    st.sidebar.write("• 💻 System monitoring")
    
    # Render header
    dashboard.render_header()
    
    # Render selected page
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
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        🏮 <strong>Smart Lamp Dashboard</strong> | 
        Real-time monitoring and control | 
        VIP Project 2025
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
