#!/bin/bash

# Smart Lamp System - Dependency Installation Script
# VIP Project - Group E
# Team: Gabriel, Leyla, Chaw Khin Su, Shohruh, Mansurbek

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Smart Lamp System - Dependency Installation${NC}"
echo -e "${BLUE}==============================================${NC}"
echo "⏰ Started at: $(date)"
echo ""

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        return 0
    else
        return 1
    fi
}

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    log_error "Cannot detect OS"
    exit 1
fi

log_info "Detected OS: $OS $VER"

if is_raspberry_pi; then
    log_info "Running on Raspberry Pi hardware"
    RASPBERRY_PI=true
else
    log_warning "Not running on Raspberry Pi - some packages may be different"
    RASPBERRY_PI=false
fi

# Update package lists
log_info "Updating package lists..."
sudo apt update

# Install system dependencies
log_info "Installing system dependencies..."

SYSTEM_PACKAGES=(
    "python3"
    "python3-pip"
    "python3-venv"
    "python3-dev"
    "git"
    "curl"
    "wget"
    "build-essential"
    "cmake"
    "pkg-config"
    "libjpeg-dev"
    "libtiff5-dev"
    "libpng-dev"
    "libavcodec-dev"
    "libavformat-dev"
    "libswscale-dev"
    "libv4l-dev"
    "libxvidcore-dev"
    "libx264-dev"
    "libfontconfig1-dev"
    "libcairo2-dev"
    "libgdk-pixbuf2.0-dev"
    "libpango1.0-dev"
    "libgtk2.0-dev"
    "libgtk-3-dev"
    "libatlas-base-dev"
    "gfortran"
    "libhdf5-dev"
    "libhdf5-serial-dev"
    "libhdf5-103"
    "libqtgui4"
    "libqtwebkit4"
    "libqt4-test"
    "python3-pyqt5"
    "libopenjp2-7"
    "libtiff5"
    "libjasper-dev"
    "libpng16-16"
    "libavformat58"
    "libavcodec58"
    "libavutil56"
    "libswscale5"
    "libgtk-3-0"
    "libcanberra-gtk-module"
    "libcanberra-gtk3-module"
)

# Audio packages
AUDIO_PACKAGES=(
    "alsa-utils"
    "pulseaudio"
    "pulseaudio-utils"
    "libportaudio2"
    "libportaudiocpp0"
    "portaudio19-dev"
    "libasound2-dev"
    "libmp3lame-dev"
    "libvorbis-dev"
    "libtheora-dev"
    "libspeex-dev"
    "libgsm1-dev"
)

# Raspberry Pi specific packages
if [ "$RASPBERRY_PI" = true ]; then
    RPI_PACKAGES=(
        "python3-rpi.gpio"
        "i2c-tools"
        "python3-smbus"
        "spi-tools"
        "python3-spidev"
        "python3-gpiozero"
        "raspi-config"
    )
    SYSTEM_PACKAGES+=("${RPI_PACKAGES[@]}")
fi

# Install packages
for package in "${SYSTEM_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package "; then
        log_info "Package $package is already installed"
    else
        log_info "Installing $package..."
        if sudo apt install -y "$package"; then
            log_success "Installed $package"
        else
            log_warning "Failed to install $package (continuing anyway)"
        fi
    fi
done

# Install audio packages
log_info "Installing audio packages..."
for package in "${AUDIO_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package "; then
        log_info "Audio package $package is already installed"
    else
        log_info "Installing audio package $package..."
        if sudo apt install -y "$package"; then
            log_success "Installed $package"
        else
            log_warning "Failed to install $package (continuing anyway)"
        fi
    fi
done

# Install Python pip if not available
if ! command_exists pip3; then
    log_info "Installing pip3..."
    sudo apt install -y python3-pip
fi

# Upgrade pip
log_info "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python virtual environment if not available
if ! python3 -c "import venv" 2>/dev/null; then
    log_info "Installing python3-venv..."
    sudo apt install -y python3-venv
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip in virtual environment
log_info "Upgrading pip in virtual environment..."
pip install --upgrade pip wheel setuptools

# Install Python dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    log_info "Installing Python dependencies from requirements.txt..."
    
    # Install basic dependencies first
    pip install numpy scipy
    
    # Install the rest
    if pip install -r requirements.txt; then
        log_success "Python dependencies installed successfully"
    else
        log_error "Failed to install some Python dependencies"
        log_info "Trying to install dependencies individually..."
        
        # Try installing packages individually
        while IFS= read -r line; do
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
                continue  # Skip comments and empty lines
            fi
            
            package=$(echo "$line" | sed 's/[>=<].*$//')
            log_info "Installing $package..."
            
            if pip install "$package"; then
                log_success "Installed $package"
            else
                log_warning "Failed to install $package"
            fi
        done < requirements.txt
    fi
else
    log_warning "requirements.txt not found, installing basic packages..."
    
    # Install essential packages manually
    PYTHON_PACKAGES=(
        "streamlit"
        "plotly"
        "pandas"
        "numpy"
        "scikit-learn"
        "requests"
        "python-dotenv"
        "psutil"
        "pygame"
    )
    
    for package in "${PYTHON_PACKAGES[@]}"; do
        log_info "Installing $package..."
        if pip install "$package"; then
            log_success "Installed $package"
        else
            log_warning "Failed to install $package"
        fi
    done
fi

# Install Raspberry Pi specific Python packages
if [ "$RASPBERRY_PI" = true ]; then
    log_info "Installing Raspberry Pi specific packages..."
    
    RPI_PYTHON_PACKAGES=(
        "RPi.GPIO"
        "adafruit-circuitpython-dht"
        "adafruit-circuitpython-mcp3xxx"
        "gpiozero"
        "w1thermsensor"
    )
    
    for package in "${RPI_PYTHON_PACKAGES[@]}"; do
        log_info "Installing $package..."
        if pip install "$package"; then
            log_success "Installed $package"
        else
            log_warning "Failed to install $package (may not be critical)"
        fi
    done
fi

# Configure Raspberry Pi settings
if [ "$RASPBERRY_PI" = true ]; then
    log_info "Configuring Raspberry Pi settings..."
    
    # Enable I2C
    if ! lsmod | grep -q i2c_dev; then
        log_info "Enabling I2C..."
        sudo raspi-config nonint do_i2c 0
        sudo modprobe i2c-dev
    fi
    
    # Enable SPI
    if ! lsmod | grep -q spi_bcm2835; then
        log_info "Enabling SPI..."
        sudo raspi-config nonint do_spi 0
        sudo modprobe spi_bcm2835
    fi
    
    # Enable GPIO
    log_info "Setting up GPIO permissions..."
    sudo usermod -a -G gpio $USER
    
    # Enable audio
    log_info "Enabling audio..."
    sudo raspi-config nonint do_audio 0
fi

# Create necessary directories
log_info "Creating project directories..."
mkdir -p data/models
mkdir -p data/audio
mkdir -p data/logs
mkdir -p data/exports
log_success "Project directories created"

# Set up audio permissions
log_info "Setting up audio permissions..."
sudo usermod -a -G audio $USER

# Install Node.js for potential web development (optional)
if ! command_exists node; then
    log_info "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    log_success "Node.js installed"
fi

# Clean up
log_info "Cleaning up package cache..."
sudo apt autoremove -y
sudo apt autoclean

# Create a flag file to indicate dependencies are installed
touch .dependencies_installed

# Final system check
log_info "Running basic system verification..."

# Check Python
if python3 --version >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python check passed: $PYTHON_VERSION"
else
    log_error "Python check failed"
fi

# Check pip
if pip --version >/dev/null 2>&1; then
    PIP_VERSION=$(pip --version)
    log_success "Pip check passed: $PIP_VERSION"
else
    log_error "Pip check failed"
fi

# Check virtual environment
if [ -d "venv" ]; then
    log_success "Virtual environment exists"
else
    log_warning "Virtual environment not found"
fi

# Check key Python packages
source venv/bin/activate
REQUIRED_PACKAGES=("streamlit" "plotly" "pandas" "numpy" "requests")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        log_success "Package $package is available"
    else
        log_warning "Package $package is not available"
    fi
done

echo ""
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo -e "${GREEN}========================${NC}"
echo ""
echo "Next steps:"
echo "1. Copy env.example to .env and configure your settings"
echo "2. Run the system health check: python3 scripts/system_health_check.py"
echo "3. Start the Smart Lamp system: ./scripts/run.sh"
echo ""

if [ "$RASPBERRY_PI" = true ]; then
    log_warning "Please reboot your Raspberry Pi for all changes to take effect:"
    log_warning "sudo reboot"
fi

log_success "Smart Lamp dependencies installation completed successfully!"
