"""
Smart Lamp Utilities
Common functions, logging setup, validators, and helper functions
"""

import os
import json
import logging
import logging.handlers
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import psutil

from src.config import settings


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    """Setup centralized logging system"""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                settings.settings.LOG_FILE_PATH,
                maxBytes=settings.settings.LOG_MAX_SIZE_MB * 1024 * 1024,
                backupCount=settings.settings.LOG_BACKUP_COUNT
            ),
            # Console handler for development
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("smart_lamp")


def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return logging.getLogger(f"smart_lamp.{name}")


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def load_json_file(file_path: str, default: Any = None) -> Any:
    """Load JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            return default or {}
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return default or {}


def save_json_file(file_path: str, data: Any) -> bool:
    """Save data to JSON file with error handling"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error saving JSON file {file_path}: {e}")
        return False


def backup_file(file_path: str, backup_suffix: str = None) -> bool:
    """Create backup of file"""
    try:
        if not os.path.exists(file_path):
            return False
        
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = f"{file_path}.backup_{backup_suffix}"
        
        import shutil
        shutil.copy2(file_path, backup_path)
        
        logger = get_logger("utils")
        logger.info(f"File backed up: {file_path} -> {backup_path}")
        return True
        
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error backing up file {file_path}: {e}")
        return False


# =============================================================================
# DATA VALIDATION
# =============================================================================

def validate_color(color: Dict[str, int]) -> bool:
    """Validate RGB color dictionary"""
    if not isinstance(color, dict):
        return False
    
    required_keys = ['r', 'g', 'b']
    if not all(key in color for key in required_keys):
        return False
    
    for key in required_keys:
        value = color[key]
        if not isinstance(value, int) or not (0 <= value <= 255):
            return False
    
    return True


def validate_brightness(brightness: Union[int, float]) -> bool:
    """Validate brightness value (0-100)"""
    try:
        brightness = float(brightness)
        return 0 <= brightness <= 100
    except (ValueError, TypeError):
        return False


def validate_volume(volume: Union[int, float]) -> bool:
    """Validate volume value (0.0-1.0)"""
    try:
        volume = float(volume)
        return 0.0 <= volume <= 1.0
    except (ValueError, TypeError):
        return False


def validate_gpio_pin(pin: int) -> bool:
    """Validate GPIO pin number for Raspberry Pi"""
    # Valid GPIO pins on Raspberry Pi
    valid_pins = list(range(2, 28))  # GPIO 2-27
    return pin in valid_pins


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    return filename[:255] if filename else "unnamed"


# =============================================================================
# TIME UTILITIES
# =============================================================================

def get_time_category(timestamp: datetime = None) -> str:
    """Get time category for given timestamp"""
    if timestamp is None:
        timestamp = datetime.now()
    
    hour = timestamp.hour
    
    if 5 <= hour < 8:
        return "early_morning"
    elif 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 20:
        return "evening"
    elif 20 <= hour < 23:
        return "night"
    else:
        return "late_night"


def is_business_hours(timestamp: datetime = None) -> bool:
    """Check if timestamp is during business hours"""
    if timestamp is None:
        timestamp = datetime.now()
    
    # Business hours: Monday-Friday, 9 AM - 6 PM
    return (timestamp.weekday() < 5 and 9 <= timestamp.hour < 18)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object"""
    try:
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return None
        
    except Exception:
        return None


# =============================================================================
# SYSTEM UTILITIES
# =============================================================================

def get_system_stats() -> Dict[str, Any]:
    """Get system resource statistics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error getting system stats: {e}")
        return {"error": str(e)}


def check_system_health() -> Dict[str, Any]:
    """Check system health against configured thresholds"""
    stats = get_system_stats()
    
    if "error" in stats:
        return {"healthy": False, "issues": ["Cannot read system stats"]}
    
    issues = []
    
    if stats["cpu_percent"] > settings.settings.MAX_CPU_USAGE_PERCENT:
        issues.append(f"High CPU usage: {stats['cpu_percent']:.1f}%")
    
    if stats["memory_percent"] > settings.settings.MAX_MEMORY_USAGE_PERCENT:
        issues.append(f"High memory usage: {stats['memory_percent']:.1f}%")
    
    if stats["disk_percent"] > 90:  # Hard-coded disk threshold
        issues.append(f"High disk usage: {stats['disk_percent']:.1f}%")
    
    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }


def get_raspberry_pi_info() -> Dict[str, Any]:
    """Get Raspberry Pi specific information"""
    try:
        info = {"model": "Unknown", "temperature": None}
        
        # Try to read Pi model
        try:
            with open('/proc/device-tree/model', 'r') as f:
                info["model"] = f.read().strip()
        except:
            pass
        
        # Try to read CPU temperature
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
                info["temperature"] = temp
        except:
            pass
        
        return info
        
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error getting Pi info: {e}")
        return {"error": str(e)}


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string"""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> Dict[str, int]:
    """Convert hex color string to RGB dictionary"""
    try:
        hex_color = hex_color.lstrip('#')
        return {
            'r': int(hex_color[0:2], 16),
            'g': int(hex_color[2:4], 16),
            'b': int(hex_color[4:6], 16)
        }
    except (ValueError, IndexError):
        return {'r': 255, 'g': 255, 'b': 255}  # Default to white


def adjust_brightness(color: Dict[str, int], brightness_percent: float) -> Dict[str, int]:
    """Adjust color brightness by percentage"""
    factor = max(0, min(1, brightness_percent / 100.0))
    return {
        'r': int(color['r'] * factor),
        'g': int(color['g'] * factor),
        'b': int(color['b'] * factor)
    }


def blend_colors(color1: Dict[str, int], color2: Dict[str, int], ratio: float = 0.5) -> Dict[str, int]:
    """Blend two colors with given ratio (0.0 = color1, 1.0 = color2)"""
    ratio = max(0, min(1, ratio))
    return {
        'r': int(color1['r'] * (1 - ratio) + color2['r'] * ratio),
        'g': int(color1['g'] * (1 - ratio) + color2['g'] * ratio),
        'b': int(color1['b'] * (1 - ratio) + color2['b'] * ratio)
    }


# =============================================================================
# ERROR HANDLING
# =============================================================================

class SmartLampException(Exception):
    """Base exception for Smart Lamp errors"""
    pass


class HardwareException(SmartLampException):
    """Hardware-related errors"""
    pass


class SensorException(SmartLampException):
    """Sensor-related errors"""
    pass


class MLException(SmartLampException):
    """Machine learning-related errors"""
    pass


class ConfigException(SmartLampException):
    """Configuration-related errors"""
    pass


def safe_execute(func, *args, default=None, **kwargs):
    """Execute function safely with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error executing {func.__name__}: {e}")
        logger.debug(traceback.format_exc())
        return default


def retry_operation(func, max_retries: int = 3, delay: float = 1.0, *args, **kwargs):
    """Retry operation with exponential backoff"""
    import time
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            logger = get_logger("utils")
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def get_config_value(key: str, default=None, cast_type=None):
    """Get configuration value with type casting"""
    try:
        value = getattr(settings.settings, key, default)
        
        if cast_type and value is not None:
            if cast_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            else:
                return cast_type(value)
        
        return value
        
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error getting config value {key}: {e}")
        return default


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error creating directory {path}: {e}")
        return False


# =============================================================================
# DEBUGGING UTILITIES
# =============================================================================

def debug_dump(obj, name: str = "object") -> str:
    """Create debug dump of object"""
    try:
        import pprint
        return f"=== {name} ===\n{pprint.pformat(obj, width=80, depth=3)}\n"
    except Exception as e:
        return f"Error dumping {name}: {e}"


def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger("debug")
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised: {e}")
            raise
    
    return wrapper


# Initialize logging when module is imported
setup_logging()