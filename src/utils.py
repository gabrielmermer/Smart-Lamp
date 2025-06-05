
import os
import json
import time
import math
import logging
import threading
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
from contextlib import contextmanager
import colorsys


class ColorUtils:
    """Utility functions for color manipulation and conversion."""
    
    @staticmethod
    def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSV color space."""
        return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    
    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB color space."""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)
    
    @staticmethod
    def kelvin_to_rgb(temperature: int) -> Tuple[int, int, int]:
        """Convert color temperature in Kelvin to RGB values."""
        # Clamp temperature to reasonable range
        temperature = max(1000, min(40000, temperature))
        
        # Convert to RGB using simplified algorithm
        temp = temperature / 100
        
        if temp <= 66:
            red = 255
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
            green = max(0, min(255, green))
            
            if temp >= 19:
                blue = temp - 10
                blue = 138.5177312231 * math.log(blue) - 305.0447927307
                blue = max(0, min(255, blue))
            else:
                blue = 0
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0, min(255, red))
            
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
            green = max(0, min(255, green))
            
            blue = 255
        
        return int(red), int(green), int(blue)
    
    @staticmethod
    def rgb_to_kelvin(r: int, g: int, b: int) -> int:
        """Approximate color temperature in Kelvin from RGB values."""
        # Simplified approximation - not perfectly accurate
        # Based on the ratio of red to blue components
        if b == 0:
            return 3000  # Very warm
        
        ratio = r / b
        if ratio >= 2.0:
            return 2000  # Candle light
        elif ratio >= 1.5:
            return 2700  # Incandescent
        elif ratio >= 1.2:
            return 3000  # Warm white
        elif ratio >= 1.0:
            return 4000  # Cool white
        elif ratio >= 0.8:
            return 5000  # Daylight
        else:
            return 6500  # Cool daylight
    
    @staticmethod
    def blend_colors(color1: Tuple[int, int, int], color2: Tuple[int, int, int], 
                    factor: float) -> Tuple[int, int, int]:
        """Blend two RGB colors with given factor (0.0 to 1.0)."""
        factor = max(0.0, min(1.0, factor))
        
        r = int(color1[0] * (1 - factor) + color2[0] * factor)
        g = int(color1[1] * (1 - factor) + color2[1] * factor)
        b = int(color1[2] * (1 - factor) + color2[2] * factor)
        
        return (r, g, b)
    
    @staticmethod
    def get_complementary_color(r: int, g: int, b: int) -> Tuple[int, int, int]:
        """Get complementary color of given RGB color."""
        return (255 - r, 255 - g, 255 - b)
    
    @staticmethod
    def adjust_brightness(r: int, g: int, b: int, factor: float) -> Tuple[int, int, int]:
        """Adjust brightness of RGB color by factor."""
        factor = max(0.0, factor)  # No upper limit for overbrightening
        
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return (r, g, b)


class TimeUtils:
    """Utility functions for time and scheduling operations."""
    
    @staticmethod
    def get_time_of_day_category() -> str:
        """Get current time category (morning, afternoon, evening, night)."""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def is_business_hours() -> bool:
        """Check if current time is within business hours (9 AM - 6 PM)."""
        hour = datetime.now().hour
        return 9 <= hour < 18
    
    @staticmethod
    def get_sleep_hours() -> Tuple[int, int]:
        """Get typical sleep hours (start, end)."""
        return (22, 7)  # 10 PM to 7 AM
    
    @staticmethod
    def is_sleep_time() -> bool:
        """Check if current time is within typical sleep hours."""
        hour = datetime.now().hour
        sleep_start, sleep_end = TimeUtils.get_sleep_hours()
        
        if sleep_start > sleep_end:  # Overnight sleep
            return hour >= sleep_start or hour < sleep_end
        else:  # Same day sleep (unusual)
            return sleep_start <= hour < sleep_end
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human readable string."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
    
    @staticmethod
    def parse_time_string(time_str: str) -> Optional[datetime]:
        """Parse time string in various formats."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%H:%M:%S",
            "%H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def get_sunset_sunrise_estimate(latitude: float = 37.5, longitude: float = 127.0) -> Tuple[datetime, datetime]:
        """Get estimated sunrise and sunset times (simplified calculation)."""
        # This is a very simplified calculation - for production use proper astronomy library
        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        
        # Simplified calculation for Seoul, South Korea (default coordinates)
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        lat_rad = math.radians(latitude)
        
        hour_angle = math.degrees(math.acos(-math.tan(lat_rad) * math.tan(math.radians(declination))))
        
        sunrise_hour = 12 - (hour_angle / 15)
        sunset_hour = 12 + (hour_angle / 15)
        
        sunrise = now.replace(hour=int(sunrise_hour), minute=int((sunrise_hour % 1) * 60), second=0, microsecond=0)
        sunset = now.replace(hour=int(sunset_hour), minute=int((sunset_hour % 1) * 60), second=0, microsecond=0)
        
        return sunrise, sunset


class MathUtils:
    """Mathematical utility functions."""
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))
    
    @staticmethod
    def lerp(start: float, end: float, factor: float) -> float:
        """Linear interpolation between start and end."""
        return start + (end - start) * factor
    
    @staticmethod
    def smooth_step(edge0: float, edge1: float, x: float) -> float:
        """Smooth step function for gradual transitions."""
        t = MathUtils.clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)
    
    @staticmethod
    def moving_average(values: List[float], window_size: int) -> List[float]:
        """Calculate moving average of values."""
        if not values or window_size <= 0:
            return values
        
        result = []
        for i in range(len(values)):
            start_idx = max(0, i - window_size + 1)
            window = values[start_idx:i + 1]
            result.append(sum(window) / len(window))
        
        return result
    
    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range."""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
    
    @staticmethod
    def scale(value: float, old_min: float, old_max: float, 
             new_min: float, new_max: float) -> float:
        """Scale value from one range to another."""
        normalized = MathUtils.normalize(value, old_min, old_max)
        return new_min + normalized * (new_max - new_min)


class FileUtils:
    """File and path utility functions."""
    
    @staticmethod
    def ensure_dir(path: str) -> bool:
        """Ensure directory exists, create if necessary."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_json_load(file_path: str, default: Any = None) -> Any:
        """Safely load JSON file with default value on error."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default
    
    @staticmethod
    def safe_json_save(data: Any, file_path: str) -> bool:
        """Safely save data to JSON file."""
        try:
            FileUtils.ensure_dir(os.path.dirname(file_path))
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """Get MD5 hash of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_days: int, pattern: str = "*") -> int:
        """Remove files older than specified age."""
        try:
            import glob
            pattern_path = os.path.join(directory, pattern)
            files = glob.glob(pattern_path)
            
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            removed_count = 0
            
            for file_path in files:
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    removed_count += 1
            
            return removed_count
        except Exception:
            return 0


class LogUtils:
    """Logging utility functions."""
    
    @staticmethod
    def setup_logger(name: str, log_file: Optional[str] = None, 
                    level: int = logging.INFO) -> logging.Logger:
        """Set up a logger with file and console handlers."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            FileUtils.ensure_dir(os.path.dirname(log_file))
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger


class ThreadUtils:
    """Threading utility functions."""
    
    @staticmethod
    @contextmanager
    def timeout_context(seconds: float):
        """Context manager for operations with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        
        # Set up the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))
        
        try:
            yield
        finally:
            # Clean up
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    @staticmethod
    def run_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
        """Run function with timeout using threading."""
        import threading
        import queue
        
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        
        def worker():
            try:
                result = func(*args, **kwargs)
                result_queue.put(result)
            except Exception as e:
                exception_queue.put(e)
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Force thread termination (not recommended but necessary for timeout)
            raise TimeoutError(f"Function timed out after {timeout} seconds")
        
        if not exception_queue.empty():
            raise exception_queue.get()
        
        if not result_queue.empty():
            return result_queue.get()
        
        return None


class ValidationUtils:
    """Data validation utility functions."""
    
    @staticmethod
    def is_valid_rgb(r: int, g: int, b: int) -> bool:
        """Check if RGB values are valid."""
        return all(0 <= val <= 255 for val in [r, g, b])
    
    @staticmethod
    def is_valid_brightness(value: int) -> bool:
        """Check if brightness value is valid (0-100)."""
        return 0 <= value <= 100
    
    @staticmethod
    def is_valid_color_temp(value: int) -> bool:
        """Check if color temperature is valid (1000-10000K)."""
        return 1000 <= value <= 10000
    
    @staticmethod
    def is_valid_pin(pin: int) -> bool:
        """Check if GPIO pin number is valid for Raspberry Pi."""
        # Valid GPIO pins for Raspberry Pi 4
        valid_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 
                     18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        return pin in valid_pins
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """Sanitize string for safe storage/display."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove potentially harmful characters
        text = text.replace('\x00', '')  # Remove null bytes
        text = text.strip()
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text


class DebugUtils:
    """Debugging and diagnostics utility functions."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information for debugging."""
        import platform
        import psutil
        
        try:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    @staticmethod
    def profile_function(func: Callable) -> Callable:
        """Decorator to profile function execution time."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger = logging.getLogger(__name__)
            logger.debug(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    def memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent()
            }
        except Exception:
            return {'error': 'Unable to get memory usage'}


class ConfigUtils:
    """Configuration utility functions."""
    
    @staticmethod
    def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigUtils.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ConfigUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


# Commonly used color constants
class Colors:
    """Common color constants."""
    WHITE = (255, 255, 255)
    WARM_WHITE = (255, 245, 230)
    COOL_WHITE = (230, 245, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 192, 203)
    BLACK = (0, 0, 0)
