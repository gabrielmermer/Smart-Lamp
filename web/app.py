import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components import (
    render_control_panel, render_status_display, render_environmental_dashboard,
    render_ml_insights, render_audio_controls, render_system_logs,
    render_settings_panel, show_notification
)

# Page configuration
st.set_page_config(
    page_title="Smart Lamp Control Center",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
    
    .control-button {
        width: 100%;
        margin: 0.25rem 0;
        border-radius: 20px;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'lamp_connected' not in st.session_state:
        st.session_state.lamp_connected = False
    
    if 'lamp_controller' not in st.session_state:
        st.session_state.lamp_controller = None
    
    if 'current_brightness' not in st.session_state:
        st.session_state.current_brightness = 50
    
    if 'current_color_temp' not in st.session_state:
        st.session_state.current_color_temp = 4000
    
    if 'current_rgb' not in st.session_state:
        st.session_state.current_rgb = (255, 255, 255)
    
    if 'auto_mode' not in st.session_state:
        st.session_state.auto_mode = False
    
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []


def connect_to_lamp():
    """Attempt to connect to the Smart Lamp system."""
    try:
        # Import and initialize the Smart Lamp
        from src.lamp import create_smart_lamp
        
        if st.session_state.lamp_controller is None:
            with st.spinner("Connecting to Smart Lamp..."):
                st.session_state.lamp_controller = create_smart_lamp()
                st.session_state.lamp_controller.start()
                st.session_state.lamp_connected = True
                show_notification("✅ Successfully connected to Smart Lamp!", "success")
        
    except Exception as e:
        st.session_state.lamp_connected = False
        show_notification(f"❌ Failed to connect: {str(e)}", "error")


def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏮 Smart Lamp Control Center</h1>
        <p>VIP Project Group E - Intelligent Lighting System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
        # Connection status
        if st.session_state.lamp_connected:
            st.success("🟢 Lamp Connected")
        else:
            st.error("🔴 Lamp Disconnected")
            if st.button("🔌 Connect to Lamp", key="connect_btn"):
                connect_to_lamp()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📱 Navigation")
        page = st.selectbox(
            "Select Page",
            [
                "🏠 Dashboard",
                "🎛️ Manual Control", 
                "🌡️ Environmental Monitor",
                "🤖 ML Insights",
                "🎵 Audio Control",
                "📊 System Logs",
                "⚙️ Settings"
            ]
        )
        
        st.markdown("---")
        
        # Quick controls
        if st.session_state.lamp_connected:
            st.markdown("### ⚡ Quick Controls")
            
            if st.button("💡 Toggle Lamp", key="quick_toggle"):
                toggle_lamp()
            
            if st.button("🌙 Night Mode", key="night_mode"):
                set_night_mode()
            
            if st.button("☀️ Day Mode", key="day_mode"):
                set_day_mode()
            
            if st.button("🚨 Emergency", key="emergency"):
                set_emergency_mode()
    
    # Main content area
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "🎛️ Manual Control":
        render_manual_control()
    elif page == "🌡️ Environmental Monitor":
        render_environmental_monitor()
    elif page == "🤖 ML Insights":
        render_ml_dashboard()
    elif page == "🎵 Audio Control":
        render_audio_dashboard()
    elif page == "📊 System Logs":
        render_logs_dashboard()
    elif page == "⚙️ Settings":
        render_settings_dashboard()
    
    # Display notifications
    display_notifications()


def render_dashboard():
    """Render main dashboard page."""
    st.markdown("## 📊 System Overview")
    
    if not st.session_state.lamp_connected:
        st.warning("Please connect to the Smart Lamp to view dashboard data.")
        return
    
    # Status cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "🟢 Online" if st.session_state.lamp_connected else "🔴 Offline"
        st.metric("System Status", status)
    
    with col2:
        st.metric("Current Brightness", f"{st.session_state.current_brightness}%")
    
    with col3:
        st.metric("Color Temperature", f"{st.session_state.current_color_temp}K")
    
    with col4:
        mode = "🤖 Auto" if st.session_state.auto_mode else "👤 Manual"
        st.metric("Control Mode", mode)
    
    st.markdown("---")
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Environmental Data")
        render_environmental_chart()
    
    with col2:
        st.markdown("### 💡 Usage Patterns")
        render_usage_chart()
    
    # Recent activity
    st.markdown("### 📋 Recent Activity")
    render_recent_activity()


def render_manual_control():
    """Render manual control interface."""
    st.markdown("## 🎛️ Manual Control")
    
    if not st.session_state.lamp_connected:
        st.warning("Please connect to the Smart Lamp to access controls.")
        return
    
    render_control_panel()


def render_environmental_monitor():
    """Render environmental monitoring dashboard."""
    st.markdown("## 🌡️ Environmental Monitor")
    
    if not st.session_state.lamp_connected:
        st.warning("Please connect to the Smart Lamp to view environmental data.")
        return
    
    render_environmental_dashboard()


def render_ml_dashboard():
    """Render ML insights dashboard."""
    st.markdown("## 🤖 Machine Learning Insights")
    
    if not st.session_state.lamp_connected:
        st.warning("Please connect to the Smart Lamp to view ML data.")
        return
    
    render_ml_insights()


def render_audio_dashboard():
    """Render audio control dashboard."""
    st.markdown("## 🎵 Audio Control")
    
    if not st.session_state.lamp_connected:
        st.warning("Please connect to the Smart Lamp to access audio controls.")
        return
    
    render_audio_controls()


def render_logs_dashboard():
    """Render system logs dashboard."""
    st.markdown("## 📊 System Logs")
    render_system_logs()


def render_settings_dashboard():
    """Render settings dashboard."""
    st.markdown("## ⚙️ Settings")
    render_settings_panel()


def render_environmental_chart():
    """Render environmental data chart."""
    # Generate sample data for demonstration
    hours = list(range(24))
    temperature = [20 + 5 * (h/24) + 2 * (h % 6) for h in hours]
    humidity = [45 + 10 * (h/24) + 5 * (h % 4) for h in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=temperature, mode='lines', name='Temperature (°C)', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=hours, y=humidity, mode='lines', name='Humidity (%)', yaxis='y2', line=dict(color='blue')))
    
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis=dict(title="Temperature (°C)", side="left"),
        yaxis2=dict(title="Humidity (%)", side="right", overlaying="y"),
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_usage_chart():
    """Render usage patterns chart."""
    # Generate sample usage data
    hours = list(range(24))
    usage = [5 + 20 * max(0, 1 - abs(h - 12)/8) + 10 * max(0, 1 - abs(h - 20)/4) for h in hours]
    
    fig = go.Figure(data=go.Bar(x=hours, y=usage, marker_color='lightblue'))
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Usage Count",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_recent_activity():
    """Render recent activity log."""
    # Sample activity data
    activities = [
        {"time": "2 minutes ago", "event": "Brightness adjusted to 75%", "type": "info"},
        {"time": "15 minutes ago", "event": "Color temperature changed to 3000K", "type": "info"},
        {"time": "1 hour ago", "event": "Auto mode enabled", "type": "success"},
        {"time": "2 hours ago", "event": "Earthquake sensor triggered", "type": "warning"},
        {"time": "3 hours ago", "event": "Audio playback started", "type": "info"},
    ]
    
    for activity in activities:
        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(activity["type"], "ℹ️")
        st.write(f"{icon} **{activity['time']}** - {activity['event']}")


def toggle_lamp():
    """Toggle lamp on/off."""
    try:
        if st.session_state.lamp_controller:
            # Toggle lamp state
            show_notification("💡 Lamp toggled", "info")
    except Exception as e:
        show_notification(f"Error toggling lamp: {str(e)}", "error")


def set_night_mode():
    """Set lamp to night mode."""
    try:
        if st.session_state.lamp_controller:
            st.session_state.current_brightness = 10
            st.session_state.current_color_temp = 2700
            show_notification("🌙 Night mode activated", "info")
    except Exception as e:
        show_notification(f"Error setting night mode: {str(e)}", "error")


def set_day_mode():
    """Set lamp to day mode."""
    try:
        if st.session_state.lamp_controller:
            st.session_state.current_brightness = 80
            st.session_state.current_color_temp = 5000
            show_notification("☀️ Day mode activated", "info")
    except Exception as e:
        show_notification(f"Error setting day mode: {str(e)}", "error")


def set_emergency_mode():
    """Set lamp to emergency mode."""
    try:
        if st.session_state.lamp_controller:
            st.session_state.current_brightness = 100
            st.session_state.current_rgb = (255, 0, 0)  # Red
            show_notification("🚨 Emergency mode activated", "warning")
    except Exception as e:
        show_notification(f"Error setting emergency mode: {str(e)}", "error")


def display_notifications():
    """Display notification messages."""
    if st.session_state.notifications:
        # Show the most recent notification
        notification = st.session_state.notifications[-1]
        
        if notification["type"] == "success":
            st.success(notification["message"])
        elif notification["type"] == "warning":
            st.warning(notification["message"])
        elif notification["type"] == "error":
            st.error(notification["message"])
        else:
            st.info(notification["message"])
        
        # Auto-clear after showing
        time.sleep(0.1)
        if st.session_state.notifications:
            st.session_state.notifications.pop()


if __name__ == "__main__":
    main()
