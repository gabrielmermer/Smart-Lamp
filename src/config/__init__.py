"""
Smart Lamp Configuration Package

This package contains all configuration files for the Smart Lamp project.
All settings are loaded from the .env file to make changes easy.
"""

from .hardware_config import HardwareConfig
from .settings import Settings

# Make configs easily accessible
hardware = HardwareConfig()
settings = Settings()

__all__ = ['hardware', 'settings', 'HardwareConfig', 'Settings']