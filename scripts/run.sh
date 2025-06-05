#!/bin/bash

# Smart Lamp System - Main Startup Script
# VIP Project - Group E
# Team: Gabriel, Leyla, Chaw Khin Su, Shohruh, Mansurbek

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🏮 Smart Lamp System Startup${NC}"
echo -e "${BLUE}==============================${NC}"
echo "📁 Project directory: $PROJECT_DIR"
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

# Change to project directory
cd "$PROJECT_DIR"

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    log_info "Detected Raspberry Pi environment"
    RASPBERRY_PI=true
else
    log_warning "Not running on Raspberry Pi - some features may be simulated"
    RASPBERRY_PI=false
fi

# Check Python installation
if ! command_exists python3; then
    log_error "Python 3 is not installed!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_info "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_warning "Virtual environment not found"
    read -p "Create virtual environment? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_warning "Continuing without virtual environment"
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    log_info "Activating virtual environment..."
    source venv/bin/activate
    log_success "Virtual environment activated"
fi

# Check if requirements are installed
if [ ! -f ".requirements_installed" ]; then
    log_info "Installing Python dependencies..."
    if pip install -r requirements.txt; then
        touch .requirements_installed
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        exit 1
    fi
else
    log_info "Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_warning ".env file not found"
    if [ -f "env.example" ]; then
        log_info "Copying env.example to .env"
        cp env.example .env
        log_warning "Please edit .env file with your API keys and settings"
        read -p "Press Enter to continue after editing .env file..."
    else
        log_error "No env.example file found!"
        exit 1
    fi
fi

# Create necessary directories
log_info "Creating data directories..."
mkdir -p data/models
mkdir -p data/audio
mkdir -p data/logs
mkdir -p data/exports
log_success "Data directories created"

# Check GPIO permissions (Raspberry Pi only)
if [ "$RASPBERRY_PI" = true ]; then
    if ! groups | grep -q gpio; then
        log_warning "Current user is not in gpio group"
        log_info "Adding user to gpio group..."
        sudo usermod -a -G gpio $USER
        log_warning "Please log out and log back in for group changes to take effect"
    fi
fi

# Parse command line arguments
INTERACTIVE=false
NO_ML=false
NO_ENV=false
NO_AUDIO=false
TEST=false
DEBUG=false
WEB_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        --no-ml)
            NO_ML=true
            shift
            ;;
        --no-env)
            NO_ENV=true
            shift
            ;;
        --no-audio)
            NO_AUDIO=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --web-only)
            WEB_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Smart Lamp System Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -i, --interactive    Run in interactive mode"
            echo "  --no-ml             Disable machine learning features"
            echo "  --no-env            Disable environmental monitoring"
            echo "  --no-audio          Disable audio features"
            echo "  --test              Run system tests"
            echo "  --debug             Enable debug mode"
            echo "  --web-only          Run only web interface"
            echo "  -h, --help          Show this help message"
            echo ""
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run tests if requested
if [ "$TEST" = true ]; then
    log_info "Running system tests..."
    python3 main.py --test
    exit $?
fi

# Start web interface in background (unless web-only mode)
if [ "$WEB_ONLY" = false ]; then
    log_info "Starting web interface..."
    streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0 > data/logs/web.log 2>&1 &
    WEB_PID=$!
    sleep 3
    
    if kill -0 $WEB_PID 2>/dev/null; then
        log_success "Web interface started (PID: $WEB_PID)"
        echo "🌐 Web interface: http://localhost:8501"
    else
        log_error "Failed to start web interface"
    fi
fi

# Build main command
MAIN_CMD="python3 main.py"

if [ "$INTERACTIVE" = true ]; then
    MAIN_CMD="$MAIN_CMD --interactive"
fi

if [ "$NO_ML" = true ]; then
    MAIN_CMD="$MAIN_CMD --no-ml"
fi

if [ "$NO_ENV" = true ]; then
    MAIN_CMD="$MAIN_CMD --no-env"
fi

if [ "$NO_AUDIO" = true ]; then
    MAIN_CMD="$MAIN_CMD --no-audio"
fi

if [ "$DEBUG" = true ]; then
    MAIN_CMD="$MAIN_CMD --debug"
fi

# If web-only mode, just start web interface
if [ "$WEB_ONLY" = true ]; then
    log_info "Starting web interface only..."
    exec streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0
fi

# Start main Smart Lamp system
log_info "Starting Smart Lamp system..."
echo "💡 Command: $MAIN_CMD"
echo ""

# Trap function to handle cleanup on exit
cleanup() {
    log_info "Shutting down Smart Lamp system..."
    if [ ! -z "$WEB_PID" ] && kill -0 $WEB_PID 2>/dev/null; then
        log_info "Stopping web interface..."
        kill $WEB_PID
    fi
    log_success "Shutdown complete"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Execute main command
exec $MAIN_CMD
