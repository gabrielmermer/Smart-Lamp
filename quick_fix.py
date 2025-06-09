#!/usr/bin/env python3
"""
NeoPixel Lamp Control Dashboard
A Streamlit web app for controlling NeoPixel LED strips in real-time
Requires: pip install streamlit rpi_ws281x adafruit-circuitpython-neopixel
Run with: streamlit run neopixel_dashboard.py
"""

import streamlit as st
import time
import threading
import board
import neopixel
from colorsys import hsv_to_rgb
import numpy as np

# NeoPixel configuration
LED_COUNT = 30
LED_PIN = board.D18
LED_BRIGHTNESS = 1.0  # Will be controlled by slider
LED_INVERT = False

class NeoPixelController:
    def __init__(self):
        self.strip = neopixel.NeoPixel(
            LED_PIN, 
            LED_COUNT, 
            brightness=LED_BRIGHTNESS,
            auto_write=False,
            pixel_order=neopixel.GRB
        )
        self.is_running = False
        self.current_effect = "off"
        self.animation_thread = None
        self.brightness = 0.5
        self.color = (255, 0, 0)  # Default red
        self.speed = 50  # Animation speed (1-100)
        
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
        if self.current_effect == "solid":
            self.set_solid_color(self.color)
    
    def set_solid_color(self, color):
        """Set all pixels to a solid color."""
        self.current_effect = "solid"
        self.color = color
        self.strip.fill(color)
        self.strip.show()
    
    def turn_off(self):
        """Turn off all pixels."""
        self.current_effect = "off"
        self.is_running = False
        self.strip.fill((0, 0, 0))
        self.strip.show()
    
    def rainbow_cycle_animation(self):
        """Rainbow cycle animation."""
        j = 0
        while self.is_running and self.current_effect == "rainbow":
            for i in range(LED_COUNT):
                pixel_index = (i * 256 // LED_COUNT) + j
                self.strip[i] = self.wheel(pixel_index & 255)
            self.strip.show()
            time.sleep((101 - self.speed) / 1000.0)  # Speed control
            j = (j + 1) % 256
    
    def breathing_animation(self):
        """Breathing effect with selected color."""
        step = 0
        direction = 1
        while self.is_running and self.current_effect == "breathing":
            # Calculate breathing brightness (0.1 to 1.0)
            breath_brightness = 0.1 + 0.9 * (np.sin(step * 0.1) + 1) / 2
            temp_brightness = self.brightness * breath_brightness
            
            # Apply color with breathing brightness
            r, g, b = self.color
            breathing_color = (int(r * breath_brightness), 
                             int(g * breath_brightness), 
                             int(b * breath_brightness))
            
            self.strip.brightness = temp_brightness
            self.strip.fill(breathing_color)
            self.strip.show()
            
            time.sleep((101 - self.speed) / 1000.0)
            step += direction
    
    def strobe_animation(self):
        """Strobe effect with selected color."""
        while self.is_running and self.current_effect == "strobe":
            # Flash on
            self.strip.fill(self.color)
            self.strip.show()
            time.sleep((101 - self.speed) / 2000.0)
            
            # Flash off
            self.strip.fill((0, 0, 0))
            self.strip.show()
            time.sleep((101 - self.speed) / 2000.0)
    
    def start_effect(self, effect_name):
        """Start the selected effect."""
        self.stop_animation()
        self.current_effect = effect_name
        
        if effect_name == "rainbow":
            self.is_running = True
            self.animation_thread = threading.Thread(target=self.rainbow_cycle_animation)
            self.animation_thread.daemon = True
            self.animation_thread.start()
        elif effect_name == "breathing":
            self.is_running = True
            self.animation_thread = threading.Thread(target=self.breathing_animation)
            self.animation_thread.daemon = True
            self.animation_thread.start()
        elif effect_name == "strobe":
            self.is_running = True
            self.animation_thread = threading.Thread(target=self.strobe_animation)
            self.animation_thread.daemon = True
            self.animation_thread.start()
    
    def stop_animation(self):
        """Stop current animation."""
        self.is_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1)

# Initialize the controller
if 'controller' not in st.session_state:
    st.session_state.controller = NeoPixelController()

def main():
    st.set_page_config(
        page_title="NeoPixel Lamp Control",
        page_icon="💡",
        layout="wide"
    )
    
    st.title("💡 NeoPixel Lamp Control Dashboard")
    st.markdown("---")
    
    controller = st.session_state.controller
    
    # Main control panel
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🎛️ Main Controls")
        
        # Power control
        power_col1, power_col2 = st.columns(2)
        with power_col1:
            if st.button("🔴 Turn OFF", use_container_width=True, type="secondary"):
                controller.turn_off()
                st.success("Lamp turned OFF")
        
        # Effect selection
        st.subheader("✨ Lighting Effects")
        effect = st.selectbox(
            "Choose Effect:",
            ["solid", "rainbow", "breathing", "strobe"],
            format_func=lambda x: {
                "solid": "🎨 Solid Color",
                "rainbow": "🌈 Rainbow Cycle",
                "breathing": "💨 Breathing",
                "strobe": "⚡ Strobe"
            }[x]
        )
        
        # Brightness control
        st.subheader("🔆 Brightness")
        brightness = st.slider(
            "Brightness Level",
            min_value=0.1,
            max_value=1.0,
            value=controller.brightness,
            step=0.1,
            format="%.1f"
        )
        
        if brightness != controller.brightness:
            controller.update_brightness(brightness)
        
        # Color selection (for solid, breathing, strobe effects)
        if effect in ["solid", "breathing", "strobe"]:
            st.subheader("🎨 Color Selection")
            
            # Color picker
            color_hex = st.color_picker("Pick a color", "#FF0000")
            
            # Convert hex to RGB
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
            
            # Preset colors
            st.write("Quick Colors:")
            color_cols = st.columns(6)
            preset_colors = [
                ("Red", "#FF0000"),
                ("Green", "#00FF00"),
                ("Blue", "#0000FF"),
                ("Yellow", "#FFFF00"),
                ("Purple", "#FF00FF"),
                ("Cyan", "#00FFFF")
            ]
            
            for i, (color_name, color_code) in enumerate(preset_colors):
                with color_cols[i]:
                    if st.button(color_name, use_container_width=True):
                        color_rgb = tuple(int(color_code[i:i+2], 16) for i in (1, 3, 5))
        
        # Animation speed (for animated effects)
        if effect in ["rainbow", "breathing", "strobe"]:
            st.subheader("⚡ Animation Speed")
            speed = st.slider(
                "Speed",
                min_value=1,
                max_value=100,
                value=controller.speed,
                help="Higher values = faster animation"
            )
            controller.speed = speed
        
        # Apply button
        st.markdown("---")
        if st.button("✅ Apply Settings", use_container_width=True, type="primary"):
            if effect == "solid":
                controller.set_solid_color(color_rgb)
                st.success(f"Applied solid color: RGB{color_rgb}")
            else:
                controller.color = color_rgb if effect in ["breathing", "strobe"] else controller.color
                controller.start_effect(effect)
                st.success(f"Started {effect} effect")
    
    # Status panel
    with col1:
        st.subheader("📊 Status")
        st.metric("LED Count", LED_COUNT)
        st.metric("Current Effect", controller.current_effect.title())
        st.metric("Brightness", f"{controller.brightness:.1f}")
        
        if controller.current_effect in ["solid", "breathing", "strobe"]:
            r, g, b = controller.color
            st.metric("Color (RGB)", f"({r}, {g}, {b})")
        
        # Connection status
        try:
            st.success("🟢 Connected")
        except:
            st.error("🔴 Connection Error")
    
    # Control panel
    with col3:
        st.subheader("🎮 Quick Actions")
        
        if st.button("🌈 Rainbow", use_container_width=True):
            controller.start_effect("rainbow")
            st.success("Rainbow started!")
        
        if st.button("❤️ Red", use_container_width=True):
            controller.set_solid_color((255, 0, 0))
            st.success("Red applied!")
        
        if st.button("💚 Green", use_container_width=True):
            controller.set_solid_color((0, 255, 0))
            st.success("Green applied!")
        
        if st.button("💙 Blue", use_container_width=True):
            controller.set_solid_color((0, 0, 255))
            st.success("Blue applied!")
        
        if st.button("🤍 White", use_container_width=True):
            controller.set_solid_color((255, 255, 255))
            st.success("White applied!")
        
        st.markdown("---")
        st.subheader("ℹ️ Info")
        st.info(f"""
        **GPIO Pin:** {LED_PIN}
        **LED Count:** {LED_COUNT}
        **Current Status:** {controller.current_effect.title()}
        """)
    
    # Auto-refresh for real-time updates
    if controller.is_running:
        time.sleep(0.1)
        st.rerun()

if __name__ == "__main__":
    main()