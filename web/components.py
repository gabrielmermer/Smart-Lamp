import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json


def show_notification(message: str, notification_type: str = "info"):
    """Add a notification to the session state."""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    st.session_state.notifications.append({
        "message": message,
        "type": notification_type,
        "timestamp": datetime.now()
    })


def render_control_panel():
    """Render the main control panel for the Smart Lamp."""
    st.markdown("### 💡 Lamp Controls")
    
    # On/Off Toggle
    col1, col2 = st.columns(2)
    with col1:
        lamp_on = st.toggle("💡 Lamp Power", value=True, key="lamp_power")
    
    with col2:
        auto_mode = st.toggle("🤖 Auto Mode", value=st.session_state.get('auto_mode', False), key="auto_mode")
        st.session_state.auto_mode = auto_mode
    
    st.markdown("---")
    
    # Brightness Control
    st.markdown("#### 🔆 Brightness")
    brightness = st.slider(
        "Brightness Level",
        min_value=0,
        max_value=100,
        value=st.session_state.get('current_brightness', 50),
        key="brightness_slider"
    )
    st.session_state.current_brightness = brightness
    
    # Color Temperature Control
    st.markdown("#### 🌡️ Color Temperature")
    color_temp = st.slider(
        "Color Temperature (K)",
        min_value=2000,
        max_value=6500,
        value=st.session_state.get('current_color_temp', 4000),
        step=100,
        key="color_temp_slider"
    )
    st.session_state.current_color_temp = color_temp
    
    # Color Preview
    temp_rgb = kelvin_to_rgb(color_temp)
    st.markdown(
        f'<div style="width: 100%; height: 30px; background-color: rgb{temp_rgb}; '
        f'border: 1px solid #ccc; border-radius: 5px; margin: 10px 0;"></div>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # RGB Color Control
    st.markdown("#### 🎨 RGB Color")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        red = st.slider("Red", 0, 255, st.session_state.get('current_rgb', (255, 255, 255))[0], key="rgb_red")
    with col2:
        green = st.slider("Green", 0, 255, st.session_state.get('current_rgb', (255, 255, 255))[1], key="rgb_green")
    with col3:
        blue = st.slider("Blue", 0, 255, st.session_state.get('current_rgb', (255, 255, 255))[2], key="rgb_blue")
    
    st.session_state.current_rgb = (red, green, blue)
    
    # RGB Color Preview
    st.markdown(
        f'<div style="width: 100%; height: 30px; background-color: rgb({red}, {green}, {blue}); '
        f'border: 1px solid #ccc; border-radius: 5px; margin: 10px 0;"></div>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Preset Modes
    st.markdown("#### 🎭 Preset Modes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌅 Sunrise", use_container_width=True):
            apply_preset("sunrise")
    
    with col2:
        if st.button("🌆 Sunset", use_container_width=True):
            apply_preset("sunset")
    
    with col3:
        if st.button("🌙 Sleep", use_container_width=True):
            apply_preset("sleep")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Reading", use_container_width=True):
            apply_preset("reading")
    
    with col2:
        if st.button("💻 Work", use_container_width=True):
            apply_preset("work")
    
    with col3:
        if st.button("🎉 Party", use_container_width=True):
            apply_preset("party")


def render_status_display():
    """Render system status display."""
    st.markdown("### 📊 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔋 Power",
            value="Online" if st.session_state.get('lamp_connected', False) else "Offline",
            delta="Connected" if st.session_state.get('lamp_connected', False) else "Disconnected"
        )
    
    with col2:
        st.metric(
            label="💡 Brightness",
            value=f"{st.session_state.get('current_brightness', 0)}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="🌡️ Color Temp",
            value=f"{st.session_state.get('current_color_temp', 4000)}K",
            delta=None
        )
    
    with col4:
        mode = "Auto" if st.session_state.get('auto_mode', False) else "Manual"
        st.metric(
            label="🎛️ Mode",
            value=mode,
            delta=None
        )


def render_environmental_dashboard():
    """Render environmental monitoring dashboard."""
    # Simulate environmental data
    current_temp = 22.5
    current_humidity = 45.2
    current_air_quality = 85
    current_light = 350
    
    st.markdown("### 🌡️ Current Conditions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ Temperature",
            value=f"{current_temp}°C",
            delta=f"{current_temp - 22:.1f}°C"
        )
    
    with col2:
        st.metric(
            label="💧 Humidity",
            value=f"{current_humidity}%",
            delta=f"{current_humidity - 45:.1f}%"
        )
    
    with col3:
        st.metric(
            label="🌬️ Air Quality",
            value=current_air_quality,
            delta=f"{current_air_quality - 80}"
        )
    
    with col4:
        st.metric(
            label="☀️ Light Level",
            value=f"{current_light} lux",
            delta=f"{current_light - 300} lux"
        )
    
    st.markdown("---")
    
    # Environmental trends
    st.markdown("### 📈 Environmental Trends")
    
    # Generate sample data
    hours = list(range(24))
    temp_data = [20 + 5 * (h/24) + 2 * (h % 6) for h in hours]
    humidity_data = [40 + 15 * (h/24) + 5 * (h % 4) for h in hours]
    air_quality_data = [75 + 20 * (h/24) + 10 * (h % 3) for h in hours]
    
    # Temperature and Humidity Chart
    fig_temp_humid = go.Figure()
    fig_temp_humid.add_trace(go.Scatter(
        x=hours, y=temp_data, mode='lines+markers',
        name='Temperature (°C)', line=dict(color='red', width=2)
    ))
    fig_temp_humid.add_trace(go.Scatter(
        x=hours, y=humidity_data, mode='lines+markers',
        name='Humidity (%)', yaxis='y2', line=dict(color='blue', width=2)
    ))
    
    fig_temp_humid.update_layout(
        title="Temperature and Humidity Over 24 Hours",
        xaxis_title="Hour of Day",
        yaxis=dict(title="Temperature (°C)", side="left"),
        yaxis2=dict(title="Humidity (%)", side="right", overlaying="y"),
        height=400
    )
    
    st.plotly_chart(fig_temp_humid, use_container_width=True)
    
    # Air Quality Chart
    fig_air = go.Figure(data=go.Scatter(
        x=hours, y=air_quality_data, mode='lines+markers',
        name='Air Quality Index', line=dict(color='green', width=2),
        fill='tonexty'
    ))
    
    fig_air.update_layout(
        title="Air Quality Index Over 24 Hours",
        xaxis_title="Hour of Day",
        yaxis_title="Air Quality Index",
        height=300
    )
    
    st.plotly_chart(fig_air, use_container_width=True)
    
    # Earthquake Alert Section
    st.markdown("### 🌍 Earthquake Monitoring")
    
    earthquake_detected = False  # Simulate earthquake detection
    
    if earthquake_detected:
        st.error("🚨 **EARTHQUAKE DETECTED!** Emergency lighting activated.")
    else:
        st.success("✅ No seismic activity detected. All systems normal.")
    
    # Earthquake sensitivity slider
    earthquake_sensitivity = st.slider(
        "Earthquake Detection Sensitivity",
        min_value=1,
        max_value=10,
        value=5,
        help="Higher values detect smaller earthquakes"
    )


def render_ml_insights():
    """Render machine learning insights dashboard."""
    st.markdown("### 🤖 Pattern Recognition")
    
    # Usage prediction
    st.markdown("#### 📊 Usage Predictions")
    
    # Generate sample prediction data
    hours = list(range(24))
    predicted_usage = [5 + 20 * max(0, 1 - abs(h - 12)/8) + 10 * max(0, 1 - abs(h - 20)/4) for h in hours]
    actual_usage = [p + (h % 3 - 1) * 3 for h, p in enumerate(predicted_usage)]
    
    fig_prediction = go.Figure()
    fig_prediction.add_trace(go.Scatter(
        x=hours, y=predicted_usage, mode='lines',
        name='Predicted Usage', line=dict(color='blue', dash='dash')
    ))
    fig_prediction.add_trace(go.Scatter(
        x=hours, y=actual_usage, mode='lines+markers',
        name='Actual Usage', line=dict(color='red')
    ))
    
    fig_prediction.update_layout(
        title="Usage Pattern Prediction vs Actual",
        xaxis_title="Hour of Day",
        yaxis_title="Usage Intensity",
        height=400
    )
    
    st.plotly_chart(fig_prediction, use_container_width=True)
    
    # ML Model Status
    st.markdown("#### 🧠 Model Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🎯 Accuracy",
            value="87.3%",
            delta="2.1%"
        )
    
    with col2:
        st.metric(
            label="📚 Training Samples",
            value="1,247",
            delta="156"
        )
    
    with col3:
        st.metric(
            label="⏱️ Last Updated",
            value="2 hours ago",
            delta=None
        )
    
    # Learning recommendations
    st.markdown("#### 💡 Smart Recommendations")
    
    recommendations = [
        "🌅 Consider increasing brightness 30 minutes before your usual wake-up time",
        "📚 Reading mode automatically suggested for 8-10 PM based on your patterns",
        "🌙 Sleep mode recommended after 10:30 PM on weekdays",
        "☀️ Natural light simulation suggested for better circadian rhythm",
    ]
    
    for rec in recommendations:
        st.info(rec)


def render_audio_controls():
    """Render audio control interface."""
    st.markdown("### 🎵 Audio System")
    
    # Audio Status
    col1, col2 = st.columns(2)
    
    with col1:
        audio_playing = st.toggle("🎵 Audio Enable", value=False, key="audio_enable")
    
    with col2:
        volume = st.slider("🔊 Volume", 0, 100, 50, key="audio_volume")
    
    st.markdown("---")
    
    # Audio Source Selection
    st.markdown("#### 📻 Audio Sources")
    
    audio_source = st.selectbox(
        "Select Audio Source",
        [
            "🌊 Ocean Waves",
            "🌧️ Rain Sounds",
            "🔥 Fireplace Crackling",
            "🎵 Relaxing Music",
            "📻 Internet Radio",
            "🎧 Custom Playlist"
        ]
    )
    
    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Play", use_container_width=True):
            show_notification(f"🎵 Playing {audio_source}", "info")
    
    with col2:
        if st.button("⏸️ Pause", use_container_width=True):
            show_notification("⏸️ Audio paused", "info")
    
    with col3:
        if st.button("⏹️ Stop", use_container_width=True):
            show_notification("⏹️ Audio stopped", "info")
    
    with col4:
        if st.button("⏭️ Next", use_container_width=True):
            show_notification("⏭️ Next track", "info")
    
    st.markdown("---")
    
    # Internet Radio Stations
    st.markdown("#### 📡 Internet Radio Stations")
    
    radio_stations = [
        "🎵 Lofi Hip Hop Radio",
        "🎼 Classical Music 24/7",
        "🌙 Sleep Stories",
        "🎧 Ambient Soundscapes",
        "📻 Local News Radio"
    ]
    
    selected_station = st.selectbox("Choose Radio Station", radio_stations)
    
    if st.button(f"📻 Listen to {selected_station}", use_container_width=True):
        show_notification(f"📻 Tuned to {selected_station}", "info")
    
    # Timer and Sleep Features
    st.markdown("#### ⏰ Sleep Timer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sleep_timer = st.selectbox(
            "Sleep Timer",
            ["Off", "15 minutes", "30 minutes", "1 hour", "2 hours"]
        )
    
    with col2:
        if st.button("💤 Start Sleep Timer", use_container_width=True):
            if sleep_timer != "Off":
                show_notification(f"💤 Sleep timer set for {sleep_timer}", "info")


def render_system_logs():
    """Render system logs and diagnostics."""
    st.markdown("### 📋 System Logs")
    
    # Log level filter
    log_level = st.selectbox(
        "Log Level Filter",
        ["All", "INFO", "WARNING", "ERROR", "DEBUG"]
    )
    
    # Sample log entries
    log_entries = [
        {"timestamp": "2025-01-20 10:30:15", "level": "INFO", "message": "Smart Lamp system started", "module": "main"},
        {"timestamp": "2025-01-20 10:30:16", "level": "INFO", "message": "Hardware controller initialized", "module": "hardware"},
        {"timestamp": "2025-01-20 10:30:17", "level": "INFO", "message": "Sensors calibrated successfully", "module": "sensors"},
        {"timestamp": "2025-01-20 10:35:22", "level": "INFO", "message": "Brightness adjusted to 75%", "module": "lamp"},
        {"timestamp": "2025-01-20 10:40:05", "level": "WARNING", "message": "Temperature sensor reading high", "module": "sensors"},
        {"timestamp": "2025-01-20 10:45:30", "level": "INFO", "message": "ML model prediction completed", "module": "ml"},
        {"timestamp": "2025-01-20 10:50:12", "level": "ERROR", "message": "Network connection timeout", "module": "api"},
        {"timestamp": "2025-01-20 10:55:08", "level": "INFO", "message": "Audio playback started", "module": "audio"},
    ]
    
    # Filter logs
    if log_level != "All":
        filtered_logs = [log for log in log_entries if log["level"] == log_level]
    else:
        filtered_logs = log_entries
    
    # Display logs
    for log in reversed(filtered_logs):  # Show newest first
        level_color = {
            "INFO": "🔵",
            "WARNING": "🟡", 
            "ERROR": "🔴",
            "DEBUG": "⚫"
        }.get(log["level"], "⚪")
        
        st.code(f"{level_color} {log['timestamp']} [{log['level']}] {log['module']}: {log['message']}")
    
    st.markdown("---")
    
    # System diagnostics
    st.markdown("### 🔧 System Diagnostics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            show_notification("📋 Logs refreshed", "info")
    
    with col2:
        if st.button("💾 Export Logs", use_container_width=True):
            show_notification("💾 Logs exported to file", "success")
    
    # System health metrics
    st.markdown("#### 💊 System Health")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🖥️ CPU Usage", "23%", "-2%")
    
    with col2:
        st.metric("💾 Memory Usage", "456 MB", "+12 MB")
    
    with col3:
        st.metric("🌡️ System Temp", "42°C", "+1°C")
    
    with col4:
        st.metric("⏱️ Uptime", "2d 5h 23m", None)


def render_settings_panel():
    """Render system settings configuration."""
    st.markdown("### ⚙️ System Settings")
    
    # General Settings
    st.markdown("#### 🔧 General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_start = st.checkbox("🚀 Auto-start on boot", value=True)
        debug_mode = st.checkbox("🐛 Debug mode", value=False)
        
    with col2:
        update_interval = st.selectbox(
            "📊 Data update interval",
            ["1 second", "5 seconds", "10 seconds", "30 seconds"]
        )
        
        log_level_setting = st.selectbox(
            "📋 Log level",
            ["DEBUG", "INFO", "WARNING", "ERROR"]
        )
    
    st.markdown("---")
    
    # Hardware Settings
    st.markdown("#### 🔌 Hardware Configuration")
    
    st.text_input("💡 LED Strip Pin", value="18", help="GPIO pin for LED strip control")
    st.text_input("🔘 Button Pin", value="21", help="GPIO pin for physical button")
    st.text_input("🎛️ Potentiometer Pin", value="MCP3008 Channel 0", help="ADC channel for potentiometer")
    
    st.markdown("---")
    
    # Network Settings
    st.markdown("#### 🌐 Network Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("📡 WiFi SSID", value="SmartLamp_Network")
        st.text_input("🔐 API Key (OpenWeather)", type="password")
    
    with col2:
        st.number_input("🌐 Web Port", value=8501, min_value=1000, max_value=9999)
        st.checkbox("🔒 Enable HTTPS", value=False)
    
    st.markdown("---")
    
    # Machine Learning Settings
    st.markdown("#### 🧠 ML Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ml_enabled = st.checkbox("🤖 Enable ML predictions", value=True)
        training_frequency = st.selectbox(
            "📚 Model training frequency",
            ["Daily", "Weekly", "Monthly", "Manual"]
        )
    
    with col2:
        prediction_confidence = st.slider(
            "🎯 Minimum prediction confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )
        
        max_training_samples = st.number_input(
            "📊 Max training samples",
            value=10000,
            min_value=100,
            max_value=100000
        )
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", use_container_width=True):
            show_notification("💾 Settings saved successfully", "success")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            show_notification("🔄 Settings reset to defaults", "info")
    
    with col3:
        if st.button("📤 Export Config", use_container_width=True):
            show_notification("📤 Configuration exported", "success")


def apply_preset(preset_name: str):
    """Apply a lighting preset."""
    presets = {
        "sunrise": {"brightness": 80, "color_temp": 3000, "rgb": (255, 200, 100)},
        "sunset": {"brightness": 60, "color_temp": 2500, "rgb": (255, 150, 50)},
        "sleep": {"brightness": 5, "color_temp": 2000, "rgb": (255, 100, 50)},
        "reading": {"brightness": 90, "color_temp": 4000, "rgb": (255, 255, 240)},
        "work": {"brightness": 85, "color_temp": 5000, "rgb": (255, 255, 255)},
        "party": {"brightness": 100, "color_temp": 6500, "rgb": (255, 0, 255)},
    }
    
    if preset_name in presets:
        preset = presets[preset_name]
        st.session_state.current_brightness = preset["brightness"]
        st.session_state.current_color_temp = preset["color_temp"]
        st.session_state.current_rgb = preset["rgb"]
        
        show_notification(f"🎭 {preset_name.title()} mode activated", "success")


def kelvin_to_rgb(temperature: int) -> Tuple[int, int, int]:
    """Convert color temperature in Kelvin to RGB values."""
    temperature = max(1000, min(40000, temperature))
    temp = temperature / 100
    
    if temp <= 66:
        red = 255
        green = temp
        green = 99.4708025861 * (green ** 0.5) - 161.1195681661
        green = max(0, min(255, green))
        
        if temp >= 19:
            blue = temp - 10
            blue = 138.5177312231 * (blue ** 0.5) - 305.0447927307
            blue = max(0, min(255, blue))
        else:
            blue = 0
    else:
        red = temp - 60
        red = 329.698727446 * (red ** -0.1332047592)
        red = max(0, min(255, red))
        
        green = temp - 60  
        green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))
        
        blue = 255
    
    return (int(red), int(green), int(blue))
