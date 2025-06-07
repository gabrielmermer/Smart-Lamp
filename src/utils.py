"""
Utility Functions for Smart Lamp

Helper functions and utilities:
- File operations (JSON, logging)
- Color conversions and calculations
- Time and date helpers
- System monitoring
- General purpose utilities

Independent module - provides common functionality.
"""

import os
import json
import logging
import time
import colorsys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import psutil

class Utils:
    """Utility functions for Smart Lamp project"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # File Operations
    def ensure_directory(self, path: str):
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def save_json(self, filepath: str, data: Dict):
        """Save data to JSON file"""
        try:
            # Ensure directory exists
            self.ensure_directory(os.path.dirname(filepath))
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON to {filepath}: {e}")
            return False
    
    def load_json(self, filepath: str) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load JSON from {filepath}: {e}")
            return None
    
    def append_to_file(self, filepath: str, text: str):
        """Append text to file"""
        try:
            self.ensure_directory(os.path.dirname(filepath))
            
            with open(filepath, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {text}\n")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to append to {filepath}: {e}")
            return False
    
    # Color Utilities
    def rgb_to_hsv(self, r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSV"""
        r, g, b = r/255.0, g/255.0, b/255.0
        return colorsys.rgb_to_hsv(r, g, b)
    
    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r*255), int(g*255), int(b*255)
    
    def blend_colors(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
        """Blend two RGB colors with given ratio (0.0 to 1.0)"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)
        
        return (r, g, b)
    
    def adjust_brightness(self, color: Tuple[int, int, int], brightness: float) -> Tuple[int, int, int]:
        """Adjust color brightness (0.0 to 1.0)"""
        r, g, b = color
        return (int(r * brightness), int(g * brightness), int(b * brightness))
    
    def get_dominant_color(self, r: int, g: int, b: int) -> str:
        """Get dominant color name from RGB values"""
        if r > g and r > b:
            return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        elif r == g and r > b:
            return "yellow"
        elif r == b and r > g:
            return "magenta"
        elif g == b and g > r:
            return "cyan"
        else:
            return "white"
    
    def generate_color_palette(self, base_color: Tuple[int, int, int], count: int = 5) -> List[Tuple[int, int, int]]:
        """Generate color palette based on base color"""
        r, g, b = base_color
        h, s, v = self.rgb_to_hsv(r, g, b)
        
        palette = []
        for i in range(count):
            # Vary hue slightly
            new_h = (h + (i * 0.1)) % 1.0
            new_r, new_g, new_b = self.hsv_to_rgb(new_h, s, v)
            palette.append((new_r, new_g, new_b))
        
        return palette
    
    # Time Utilities
    def get_current_hour(self) -> int:
        """Get current hour (0-23)"""
        return datetime.now().hour
    
    def get_current_day_of_week(self) -> int:
        """Get current day of week (0=Monday, 6=Sunday)"""
        return datetime.now().weekday()
    
    def is_daytime(self, sunrise_hour: int = 6, sunset_hour: int = 22) -> bool:
        """Check if it's currently daytime"""
        current_hour = self.get_current_hour()
        return sunrise_hour <= current_hour < sunset_hour
    
    def time_to_string(self, timestamp: float = None) -> str:
        """Convert timestamp to readable string"""
        if timestamp is None:
            timestamp = time.time()
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    def days_ago(self, days: int) -> datetime:
        """Get datetime object for N days ago"""
        return datetime.now() - timedelta(days=days)
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    # System Monitoring
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'temperature': self.get_cpu_temperature(),
                'uptime': time.time() - psutil.boot_time()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi)"""
        try:
            # Try Raspberry Pi method
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return temp
        except:
            try:
                # Try alternative method
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
            except:
                pass
        return None
    
    def check_disk_space(self, path: str = '/') -> Dict:
        """Check available disk space"""
        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to check disk space: {e}")
            return {}
    
    # Data Processing
    def clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))
    
    def map_range(self, value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
        """Map value from one range to another"""
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def smooth_value(self, new_value: float, old_value: float, smoothing: float = 0.1) -> float:
        """Smooth value transition using exponential moving average"""
        return old_value * (1 - smoothing) + new_value * smoothing
    
    def calculate_average(self, values: List[float]) -> float:
        """Calculate average of list of values"""
        return sum(values) / len(values) if values else 0.0
    
    def find_pattern_in_data(self, data: List[Dict], key: str) -> Dict:
        """Find patterns in time-series data"""
        if not data:
            return {}
        
        try:
            values = [item.get(key, 0) for item in data if key in item]
            
            if not values:
                return {}
            
            return {
                'average': self.calculate_average(values),
                'minimum': min(values),
                'maximum': max(values),
                'count': len(values),
                'trend': 'increasing' if values[-1] > values[0] else 'decreasing' if values[-1] < values[0] else 'stable'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to find pattern: {e}")
            return {}
    
    # Validation
    def is_valid_rgb(self, r: int, g: int, b: int) -> bool:
        """Check if RGB values are valid"""
        return all(0 <= val <= 255 for val in [r, g, b])
    
    def is_valid_percentage(self, value: float) -> bool:
        """Check if value is valid percentage (0-100)"""
        return 0 <= value <= 100
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        return filename[:200]
    
    # Logging Helpers
    def setup_logging(self, log_file: str = None, level: str = "INFO"):
        """Setup logging configuration"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup file handler if specified
        handlers = [console_handler]
        if log_file:
            self.ensure_directory(os.path.dirname(log_file))
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers
        )
    
    def log_performance(self, func_name: str, duration: float):
        """Log performance timing"""
        self.logger.debug(f"Performance: {func_name} took {self.format_duration(duration)}")
    
    # Configuration Helpers
    def merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Merge configuration dictionaries"""
        result = default.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_nested_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    # Helper decorators (as methods)
    def retry_on_failure(self, max_retries: int = 3, delay: float = 1.0):
        """Decorator method for retrying failed operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
            return wrapper
        return decorator

# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    utils = Utils()
    
    print("Testing utility functions...")
    
    # Test color utilities
    print("\nColor utilities:")
    color = (255, 100, 150)
    hsv = utils.rgb_to_hsv(*color)
    back_to_rgb = utils.hsv_to_rgb(*hsv)
    print(f"RGB {color} -> HSV {hsv} -> RGB {back_to_rgb}")
    
    blended = utils.blend_colors((255, 0, 0), (0, 255, 0), 0.5)
    print(f"Blended red + green: {blended}")
    
    palette = utils.generate_color_palette((255, 100, 100), 3)
    print(f"Color palette: {palette}")
    
    # Test time utilities
    print("\nTime utilities:")
    print(f"Current hour: {utils.get_current_hour()}")
    print(f"Day of week: {utils.get_current_day_of_week()}")
    print(f"Is daytime: {utils.is_daytime()}")
