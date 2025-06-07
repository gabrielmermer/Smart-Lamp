"""
Setup script for Smart Lamp Project

This script sets up the project environment:
- Creates necessary directories
- Initializes database
- Sets up logging
- Validates configuration
- Prepares the system for first run

Run this once before using the Smart Lamp system.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings, hardware
from src.database import DatabaseManager
from src.utils import Utils

class SmartLampSetup:
    """Setup manager for Smart Lamp project"""
    
    def __init__(self):
        self.utils = Utils()
        self.logger = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for setup process"""
        self.utils.setup_logging(level="INFO")
        self.logger = logging.getLogger(__name__)
        self.logger.info("Smart Lamp Setup Started")
    
    def create_directories(self):
        """Create all necessary directories"""
        directories = [
            'data',
            'logs', 
            'models',
            'audio',
            os.path.dirname(settings.DATABASE_PATH),
            os.path.dirname(settings.LOG_FILE_PATH),
            os.path.dirname(settings.ML_MODEL_PATH),
            os.path.dirname(settings.STATE_FILE_PATH)
        ]
        
        self.logger.info("Creating project directories...")
        
        for directory in directories:
            if directory:  # Skip empty paths
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"✓ Created directory: {directory}")
                except Exception as e:
                    self.logger.error(f"✗ Failed to create directory {directory}: {e}")
                    return False
        
        return True
    
    def validate_environment(self):
        """Validate .env configuration"""
        self.logger.info("Validating environment configuration...")
        
        issues = []
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            issues.append("❌ .env file not found! Copy .env.example to .env and configure it.")
        
        # Check API configuration
        if not settings.is_api_key_valid():
            issues.append("⚠️  OpenWeatherMap API key not configured - weather/air quality features will not work")
        
        # Check critical settings
        required_settings = [
            ('LOCATION_LAT', settings.LOCATION_LAT),
            ('LOCATION_LON', settings.LOCATION_LON),
            ('EARTHQUAKE_MIN_MAGNITUDE', settings.EARTHQUAKE_MIN_MAGNITUDE),
            ('ML_LEARNING_PERIOD_DAYS', settings.ML_LEARNING_PERIOD_DAYS)
        ]
        
        for name, value in required_settings:
            if value is None:
                issues.append(f"❌ Missing required setting: {name}")
        
        # Check hardware pin assignments
        try:
            for led_num in [1, 2, 3]:
                pins = hardware.get_rgb_led_pins(led_num)
                if any(pin is None for pin in pins):
                    issues.append(f"❌ Invalid RGB LED {led_num} pin configuration")
        except Exception as e:
            issues.append(f"❌ Hardware configuration error: {e}")
        
        # Report validation results
        if issues:
            self.logger.warning("Configuration issues found:")
            for issue in issues:
                self.logger.warning(f"  {issue}")
            return False
        else:
            self.logger.info("✓ Environment configuration is valid")
            return True
    
    def initialize_database(self):
        """Initialize the database"""
        self.logger.info("Initializing database...")
        
        try:
            db = DatabaseManager()
            
            # Test database operations
            db.log_user_action("SETUP_TEST", (255, 255, 255), 50)
            db.log_environmental_data("setup", 1.0, {"test": "initialization"})
            
            stats = db.get_stats()
            self.logger.info(f"✓ Database initialized successfully")
            self.logger.info(f"  Database location: {settings.DATABASE_PATH}")
            self.logger.info(f"  Tables created: {len(stats)} tables")
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Database initialization failed: {e}")
            return False
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        self.logger.info("Checking Python dependencies...")
        
        required_packages = [
            'numpy',
            'pandas', 
            'scikit-learn',
            'requests',
            'python-dotenv',
            'streamlit',
            'plotly',
            'psutil'
        ]
        
        # Raspberry Pi specific packages (optional)
        raspberry_pi_packages = [
            'RPi.GPIO',
            'spidev',
            'rpi-ws281x',
            'pygame'
        ]
        
        missing_packages = []
        optional_missing = []
        
        # Check required packages
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.logger.info(f"✓ {package}")
            except ImportError:
                missing_packages.append(package)
                self.logger.error(f"✗ {package} - REQUIRED")
        
        # Check optional Raspberry Pi packages
        for package in raspberry_pi_packages:
            try:
                __import__(package.replace('-', '_'))
                self.logger.info(f"✓ {package}")
            except ImportError:
                optional_missing.append(package)
                self.logger.warning(f"⚠️  {package} - OPTIONAL (for Raspberry Pi)")
        
        if missing_packages:
            self.logger.error("Missing required packages. Install with:")
            self.logger.error(f"pip install {' '.join(missing_packages)}")
            return False
        
        if optional_missing:
            self.logger.warning("Missing optional packages. For Raspberry Pi, install with:")
            self.logger.warning(f"pip install {' '.join(optional_missing)}")
        
        self.logger.info("✓ All required dependencies are available")
        return True
    
    def create_sample_env(self):
        """Create .env file from .env.example if it doesn't exist"""
        if os.path.exists('.env'):
            return True
        
        if os.path.exists('.env.example'):
            try:
                import shutil
                shutil.copy('.env.example', '.env')
                self.logger.info("✓ Created .env file from .env.example")
                self.logger.warning("⚠️  Please edit .env file and add your API keys!")
                return True
            except Exception as e:
                self.logger.error(f"✗ Failed to create .env file: {e}")
                return False
        else:
            self.logger.error("✗ No .env.example file found to copy from")
            return False
    
    def test_hardware_simulation(self):
        """Test hardware in simulation mode"""
        self.logger.info("Testing hardware simulation...")
        
        try:
            from src.hardware import HardwareController
            
            hw = HardwareController()
            
            # Test basic operations
            hw.turn_on_leds(255, 0, 0)  # Red
            hw.set_led_strip(0, 255, 0)  # Green
            hw.turn_off_all_leds()
            
            status = hw.get_status()
            self.logger.info(f"✓ Hardware simulation test passed")
            self.logger.info(f"  Raspberry Pi mode: {status['raspberry_pi']}")
            
            hw.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Hardware simulation test failed: {e}")
            return False
    
    def test_sensors(self):
        """Test sensor APIs"""
        self.logger.info("Testing sensor APIs...")
        
        try:
            from src.sensors import SensorManager
            
            sensors = SensorManager()
            
            # Test individual sensors
            earthquake_ok = sensors.check_earthquakes()
            self.logger.info(f"✓ Earthquake API: {'OK' if earthquake_ok else 'Failed'}")
            
            if settings.is_api_key_valid():
                air_ok = sensors.check_air_quality()
                weather_ok = sensors.check_weather()
                self.logger.info(f"✓ Air Quality API: {'OK' if air_ok else 'Failed'}")
                self.logger.info(f"✓ Weather API: {'OK' if weather_ok else 'Failed'}")
            else:
                self.logger.warning("⚠️  Skipping weather APIs - no API key configured")
            
            stations = sensors.get_radio_stations(3)
            self.logger.info(f"✓ Radio API: Found {len(stations)} stations")
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Sensor test failed: {e}")
            return False
    
    def show_system_info(self):
        """Display system information"""
        self.logger.info("System Information:")
        
        try:
            # Python version
            self.logger.info(f"  Python version: {sys.version}")
            
            # System info
            sys_info = self.utils.get_system_info()
            for key, value in sys_info.items():
                if key == 'uptime':
                    uptime_str = self.utils.format_duration(value)
                    self.logger.info(f"  {key}: {uptime_str}")
                elif key == 'temperature' and value:
                    self.logger.info(f"  {key}: {value:.1f}°C")
                else:
                    self.logger.info(f"  {key}: {value}")
            
            # Disk space
            disk_info = self.utils.check_disk_space()
            if disk_info:
                free_gb = disk_info['free'] / (1024**3)
                self.logger.info(f"  Free disk space: {free_gb:.1f} GB")
            
        except Exception as e:
            self.logger.warning(f"Could not get system info: {e}")
    
    def run_setup(self):
        """Run complete setup process"""
        self.logger.info("=" * 50)
        self.logger.info("SMART LAMP PROJECT SETUP")
        self.logger.info("=" * 50)
        
        setup_steps = [
            ("Creating .env file", self.create_sample_env),
            ("Checking dependencies", self.check_dependencies),
            ("Creating directories", self.create_directories),
            ("Validating environment", self.validate_environment),
            ("Initializing database", self.initialize_database),
            ("Testing hardware simulation", self.test_hardware_simulation),
            ("Testing sensors", self.test_sensors)
        ]
        
        failed_steps = []
        
        for step_name, step_function in setup_steps:
            self.logger.info(f"\n--- {step_name} ---")
            try:
                success = step_function()
                if not success:
                    failed_steps.append(step_name)
            except Exception as e:
                self.logger.error(f"✗ {step_name} failed with exception: {e}")
                failed_steps.append(step_name)
        
        # Show system information
        self.logger.info(f"\n--- System Information ---")
        self.show_system_info()
        
        # Final results
        self.logger.info("\n" + "=" * 50)
        self.logger.info("SETUP RESULTS")
        self.logger.info("=" * 50)
        
        if failed_steps:
            self.logger.error(f"❌ Setup completed with {len(failed_steps)} issues:")
            for step in failed_steps:
                self.logger.error(f"  - {step}")
            self.logger.warning("\n⚠️  Please fix the issues above before running the Smart Lamp")
            return False
        else:
            self.logger.info("✅ Setup completed successfully!")
            self.logger.info("\nNext steps:")
            self.logger.info("1. Edit .env file with your API keys (if needed)")
            self.logger.info("2. Run: python main.py")
            self.logger.info("3. Access web interface at: http://localhost:8501")
            return True

def main():
    """Main setup function"""
    try:
        setup = SmartLampSetup()
        success = setup.run_setup()
        
        if success:
            print("\n🎉 Smart Lamp setup completed successfully!")
            print("Run 'python main.py' to start the Smart Lamp system.")
        else:
            print("\n❌ Setup failed. Please check the logs and fix the issues.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()