__version__ = "1.0.0"
__author__ = "Smart Lamp VIP Team"
__description__ = "Intelligent IoT lamp with machine learning and environmental monitoring"

# Import main components for easy access
from .lamp import smart_lamp
from .hardware import hardware_controller
from .sensors import sensor_controller
from .ml import ml_controller
from .database import db_manager
from .utils import get_logger

# Package metadata
__all__ = [
    "smart_lamp",
    "hardware_controller", 
    "sensor_controller",
    "ml_controller",
    "db_manager",
    "get_logger"
]

# Initialize logging when package is imported
logger = get_logger(__name__)
logger.info(f"Smart Lamp v{__version__} package initialized")


# src/config/__init__.py
"""
Smart Lamp Configuration Module
Centralized configuration management for all components
"""

from .settings import settings, Settings
from .hardware_config import hardware_config, HardwareConfig

__all__ = [
    "settings",
    "Settings",
    "hardware_config", 
    "HardwareConfig"
]

# Validate configuration on import
if not settings.validate_config():
    raise RuntimeError("Invalid configuration detected. Please check your .env file.")

if not hardware_config.validate_hardware_config():
    raise RuntimeError("Invalid hardware configuration detected. Please check GPIO pin assignments.")


# tests/__init__.py
"""
Smart Lamp Test Suite
Comprehensive tests for all components
"""

import sys
import os

# Add src directory to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

__version__ = "1.0.0"
__description__ = "Test suite for Smart Lamp components"


# web/__init__.py
"""
Smart Lamp Web Interface
Streamlit-based dashboard and control interface
"""

__version__ = "1.0.0"
__description__ = "Web dashboard for Smart Lamp control and monitoring"

# Import main app for easy access
from .app import main as run_app

__all__ = ["run_app"]

# data/__init__.py
"""
Smart Lamp Data Storage
Database and model storage directory
"""

__version__ = "1.0.0"
__description__ = "Data storage for Smart Lamp system"


# data/models/__init__.py
"""
Smart Lamp ML Models
Trained machine learning models storage
"""

__version__ = "1.0.0"
__description__ = "Machine learning models for Smart Lamp pattern recognition"



# scripts/__init__.py
"""
Smart Lamp Utility Scripts
Setup, maintenance, and diagnostic scripts
"""

__version__ = "1.0.0"
__description__ = "Utility scripts for Smart Lamp system management"



# docs/__init__.py
"""
Smart Lamp Documentation
Project documentation and guides
"""

__version__ = "1.0.0"
__description__ = "Documentation for Smart Lamp project"


# logs/__init__.py
"""
Smart Lamp Logging
Application logs storage
"""

__version__ = "1.0.0"
__description__ = "Log files for Smart Lamp system"