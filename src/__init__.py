
__version__ = "1.0.0"
__author__ = "VIP Project Group E"
__email__ = "smart-lamp-group-e@inha.edu"

# Core imports for external access
from .lamp import SmartLamp, create_smart_lamp
from .hardware import HardwareController
from .sensors import SensorController
from .audio import AudioController
from .ml import MLController
from .config import settings

__all__ = [
    "SmartLamp",
    "create_smart_lamp",
    "HardwareController", 
    "SensorController",
    "AudioController",
    "MLController",
    "settings"
]
