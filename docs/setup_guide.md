# Smart Lamp System Setup Guide

**VIP Project - Group E**  
**Team:** Gabriel Mermer, Khamidova Leyla, Chaw Khin Su, Shokulov Shohruh, Kakhorjonov Mansurbek

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Hardware Setup](#hardware-setup)
4. [Software Installation](#software-installation)
5. [Configuration](#configuration)
6. [System Verification](#system-verification)
7. [Running the System](#running-the-system)
8. [Troubleshooting](#troubleshooting)

## Overview

The Smart Lamp System is an IoT project built on Raspberry Pi that provides:
- Manual lamp controls via physical buttons and potentiometer
- Environmental monitoring (temperature, humidity, air quality, earthquake detection)
- Machine learning pattern recognition for automated behavior
- Audio features (internet radio, ambient sounds)
- Web interface for remote control
- Data logging and analytics

## Prerequisites

### Hardware Requirements

**Raspberry Pi Setup:**
- Raspberry Pi 4 Model B (4GB RAM recommended)
- MicroSD card (32GB minimum, Class 10)
- Power supply (5V, 3A)
- HDMI cable and monitor (for initial setup)
- Keyboard and mouse (for initial setup)

**Smart Lamp Components:**
- LED strip (WS2812B/NeoPixel, 60 LEDs recommended)
- Push buttons (3x) for manual controls
- Rotary encoder or potentiometer for brightness control
- DHT22 temperature/humidity sensor
- MQ-135 air quality sensor
- Speaker for audio output
- Breadboard and jumper wires
- Resistors (10kΩ for buttons)

### Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- Internet connection for package installation and API access

## Hardware Setup

### 1. Raspberry Pi Preparation

1. **Flash Raspberry Pi OS:**
   ```bash
   # Download Raspberry Pi Imager from official website
   # Flash Raspberry Pi OS to SD card
   # Enable SSH and configure WiFi if needed
   ```

2. **Initial Boot:**
   ```bash
   # Insert SD card and boot Raspberry Pi
   # Complete initial setup wizard
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   ```

### 2. GPIO Pin Configuration

Connect hardware components according to this pin layout:

```
GPIO Pin Layout:
├── LED Strip Data Pin: GPIO 18 (PWM0)
├── Main Button: GPIO 2 (SDA1)
├── Color Button: GPIO 3 (SCL1)
├── Mode Button: GPIO 4 (GPCLK0)
├── Brightness Potentiometer: GPIO 14 (TXD0)
├── DHT22 Sensor: GPIO 22
├── Air Quality Sensor: GPIO 27
├── Speaker: Audio Jack (3.5mm)
└── Power: 5V and GND pins
```

### 3. Wiring Diagram

```
Raspberry Pi 4 Pin Layout:

     +3.3V (1) (2) +5V
       SDA (3) (4) +5V
       SCL (5) (6) GND
      GPIO4 (7) (8) GPIO14
        GND (9) (10) GPIO15
     GPIO17 (11) (12) GPIO18 ← LED Strip
     GPIO27 (13) (14) GND
     GPIO22 (15) (16) GPIO23
      +3.3V (17) (18) GPIO24
     GPIO10 (19) (20) GND
      GPIO9 (21) (22) GPIO25
     GPIO11 (23) (24) GPIO8
        GND (25) (26) GPIO7
     GPIO0 (27) (28) GPIO1
      GPIO5 (29) (30) GND
      GPIO6 (31) (32) GPIO12
     GPIO13 (33) (34) GND
     GPIO19 (35) (36) GPIO16
     GPIO26 (37) (38) GPIO20
        GND (39) (40) GPIO21
```

**Component Connections:**

1. **LED Strip (WS2812B):**
   - VCC → 5V (Pin 2)
   - GND → GND (Pin 6)
   - Data → GPIO 18 (Pin 12)

2. **Buttons:**
   - Main Button: GPIO 2 (Pin 3) → GND via 10kΩ resistor
   - Color Button: GPIO 3 (Pin 5) → GND via 10kΩ resistor
   - Mode Button: GPIO 4 (Pin 7) → GND via 10kΩ resistor

3. **DHT22 Sensor:**
   - VCC → 3.3V (Pin 1)
   - Data → GPIO 22 (Pin 15)
   - GND → GND (Pin 9)

4. **MQ-135 Air Quality Sensor:**
   - VCC → 5V (Pin 4)
   - Analog Out → GPIO 27 (Pin 13) via ADC
   - GND → GND (Pin 14)

5. **Speaker:**
   - Connect to 3.5mm audio jack or USB audio device

### 4. Enable Required Interfaces

```bash
# Enable I2C, SPI, and GPIO
sudo raspi-config

# Navigate to:
# 3 Interface Options
#   → P2 SSH (Enable)
#   → P4 SPI (Enable)
#   → P5 I2C (Enable)
#   → P6 Serial (Enable)
```

## Software Installation

### 1. Clone Repository

```bash
# Clone the Smart Lamp repository
git clone https://github.com/your-username/Smart-Lamp.git
cd Smart-Lamp
```

### 2. Run Installation Script

```bash
# Make installation script executable
chmod +x scripts/install_dependencies.sh

# Run installation (this may take 15-30 minutes)
./scripts/install_dependencies.sh

# If running on Raspberry Pi, reboot after installation
sudo reboot
```

### 3. Manual Installation (Alternative)

If the installation script fails, install dependencies manually:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libjpeg-dev libtiff5-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libgtk2.0-dev libgtk-3-dev
sudo apt install -y libatlas-base-dev gfortran
sudo apt install -y alsa-utils pulseaudio portaudio19-dev

# Raspberry Pi specific packages
sudo apt install -y python3-rpi.gpio i2c-tools python3-smbus
sudo apt install -y python3-gpiozero raspi-config

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

```bash
# Copy environment template
cp env.example .env

# Edit configuration file
nano .env
```

Configure the following variables in `.env`:

```bash
# API Configuration
OPENWEATHER_API_KEY=your_openweather_api_key_here
EARTHQUAKE_API_URL=https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson
LOCATION_LATITUDE=41.2995
LOCATION_LONGITUDE=69.2401
LOCATION_NAME=Tashkent

# Hardware Configuration
MAIN_BUTTON_PIN=2
COLOR_BUTTON_PIN=3
MODE_BUTTON_PIN=4
LED_STRIP_PIN=18
LED_STRIP_COUNT=60
AUDIO_DEVICE=default
SPEAKER_VOLUME=70

# System Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8501
DEBUG_MODE=false
DEFAULT_BRIGHTNESS=50
DEFAULT_COLOR_R=255
DEFAULT_COLOR_G=255
DEFAULT_COLOR_B=255

# Radio Stations (JSON format)
RADIO_STATIONS={
  "BBC World Service": "http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk",
  "Jazz FM": "http://ice-the.musicradio.com/JazzFMMP3",
  "Classical FM": "http://media-ice.musicradio.com/ClassicFMMP3"
}

# Ambient Sounds Path
AMBIENT_SOUNDS_PATH=data/audio/ambient
```

### 2. API Keys Setup

1. **OpenWeatherMap API:**
   - Visit: https://openweathermap.org/api
   - Sign up for free account
   - Get API key
   - Add to `.env` file

2. **Location Configuration:**
   - Find your latitude/longitude coordinates
   - Update `LOCATION_LATITUDE` and `LOCATION_LONGITUDE` in `.env`

### 3. Hardware Pin Verification

```bash
# Test GPIO pins
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
print('GPIO test successful')
GPIO.cleanup()
"

# Test I2C
sudo i2cdetect -y 1

# Test SPI
ls /dev/spi*
```

## System Verification

### 1. Run System Health Check

```bash
# Run comprehensive system check
python3 scripts/system_health_check.py

# Run with detailed output
python3 scripts/system_health_check.py --verbose

# Generate JSON report
python3 scripts/system_health_check.py --json > health_report.json
```

### 2. Test Individual Components

```bash
# Test database
python3 -c "from src.database import get_database; db = get_database(); print('Database OK')"

# Test hardware (if on Raspberry Pi)
python3 -c "from src.hardware import HardwareController; hw = HardwareController(); print('Hardware OK')"

# Test ML model
python3 -c "from src.ml import PatternRecognition; ml = PatternRecognition(); print('ML OK')"

# Test audio
python3 -c "from src.audio import AudioController; audio = AudioController(); print('Audio OK')"
```

### 3. Verify Web Interface

```bash
# Start web interface
streamlit run web/app.py

# Access via browser
# http://your-pi-ip:8501
```

## Running the System

### 1. Quick Start

```bash
# Run with default settings
./scripts/run.sh

# Run in simulation mode (no hardware)
./scripts/run.sh --simulate

# Run with debug output
./scripts/run.sh --debug
```

### 2. Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Start main application
python3 main.py

# Start web interface (in separate terminal)
streamlit run web/app.py
```

### 3. Service Installation (Auto-start)

```bash
# Create systemd service
sudo nano /etc/systemd/system/smart-lamp.service
```

Add the following content:

```ini
[Unit]
Description=Smart Lamp System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Smart-Lamp
Environment=PATH=/home/pi/Smart-Lamp/venv/bin
ExecStart=/home/pi/Smart-Lamp/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable smart-lamp.service

# Start service
sudo systemctl start smart-lamp.service

# Check status
sudo systemctl status smart-lamp.service
```

## Testing

### 1. Run Unit Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test modules
python3 -m pytest tests/test_database.py -v
python3 -m pytest tests/test_hardware.py -v

# Generate coverage report
python3 -m pytest tests/ --cov=src --cov-report=html
```

### 2. Integration Testing

```bash
# Run integration tests
python3 main.py --test

# Test web interface
python3 -c "
import requests
import time
time.sleep(5)  # Wait for server start
response = requests.get('http://localhost:8501/_stcore/health')
print('Web interface:', 'OK' if response.status_code == 200 else 'FAILED')
"
```

## Data Management

### 1. Database Backup

```bash
# Create backup
python3 scripts/backup_data.py

# List available backups
python3 scripts/backup_data.py --list

# Restore from backup
python3 scripts/backup_data.py --restore backup_file.tar.gz
```

### 2. Log Management

```bash
# View system logs
tail -f data/logs/smart_lamp.log

# View web interface logs
tail -f data/logs/web_interface.log

# Clear old logs
find data/logs -name "*.log" -mtime +30 -delete
```

## Performance Optimization

### 1. Raspberry Pi Optimization

```bash
# Increase GPU memory split
sudo raspi-config
# Advanced Options → Memory Split → 128

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# Optimize boot
sudo nano /boot/config.txt
# Add: disable_splash=1
# Add: boot_delay=0
```

### 2. Python Optimization

```bash
# Compile Python modules for faster loading
python3 -m compileall src/

# Use faster JSON library
pip install ujson

# Optimize database
python3 -c "
from src.database import get_database
db = get_database()
db.conn.execute('VACUUM')
db.conn.execute('REINDEX')
"
```

## Security Considerations

### 1. Network Security

```bash
# Change default passwords
sudo passwd pi

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8501/tcp  # Streamlit port

# Disable SSH password authentication
sudo nano /etc/ssh/sshd_config
# Change: PasswordAuthentication no
sudo systemctl restart ssh
```

### 2. File Permissions

```bash
# Set proper permissions
chmod 600 .env
chmod 755 scripts/*.sh
chmod 644 src/*.py
```

## Maintenance

### 1. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Update repository
git pull origin main
```

### 2. System Monitoring

```bash
# Monitor system resources
htop

# Check disk usage
df -h

# Monitor temperature (Raspberry Pi)
vcgencmd measure_temp

# Check system logs
journalctl -u smart-lamp.service -f
```

## Next Steps

After successful setup:

1. **Customize Settings:** Adjust lamp behavior in the web interface
2. **Add Audio Content:** Upload ambient sounds to `data/audio/ambient/`
3. **Configure Automation:** Set up ML pattern recognition
4. **Monitor Performance:** Use system health checks regularly
5. **Backup Data:** Schedule regular backups

## Support

For additional help:
- Check the [Troubleshooting Guide](troubleshooting.md)
- Review [API Documentation](api_documentation.md)
- Examine [Hardware Wiring Guide](hardware_wiring.md)

**Project Team:**
- Gabriel Mermer - Hardware integration
- Khamidova Leyla - Temperature and audio features
- Chaw Khin Su - Manual controls
- Shokulov Shohruh - ML pattern recognition
- Kakhorjonov Mansurbek - Environmental sensors
