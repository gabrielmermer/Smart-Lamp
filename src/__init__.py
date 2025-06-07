"""
Smart Lamp Source Package

This package contains all the core modules for the Smart Lamp project.
Each module is independent and can be used separately.
"""

# Import all main classes for easy access
from .hardware import HardwareController
from .sensors import SensorManager
from .lamp import LampController
from .ml import MLManager
from .database import DatabaseManager
from .utils import Utils

# Version info
__version__ = "1.0.0"
__author__ = "Group E - VIP Smart Lamp Team"

# Make everything easily accessible
__all__ = [
    'HardwareController',
    'SensorManager', 
    'LampController',
    'MLManager',
    'DatabaseManager',
    'Utils'
]