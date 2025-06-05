#!/usr/bin/env python3
"""
Smart Lamp - Main Entry Point
Raspberry Pi-based intelligent lamp with ML pattern recognition and environmental monitoring

Usage:
    python main.py                    # Start normal operation
    python main.py --debug            # Start with debug logging
    python main.py --mock             # Start in mock mode (no hardware)
    python main.py --setup            # Run initial setup
    python main.py --status           # Show system status
    python main.py --train-ml         # Train ML model
    python main.py --backup           # Backup data
"""

import sys
import os
import signal
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import smart_lamp, get_logger
from src.config import settings
from src.database import db_manager
from src.ml import ml_controller
from src.utils import check_system_health, get_raspberry_pi_info
from src.hardware import hardware_controller
from src.sensors import sensor_controller

# Global variables for signal handling
shutdown_event = asyncio.Event()
logger = None


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # On Unix systems, also handle SIGHUP
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Smart Lamp - Intelligent IoT Lamp System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                     # Normal operation
    python main.py --debug             # Debug mode
    python main.py --mock              # Mock hardware mode
    python main.py --setup             # Initial setup
    python main.py --status            # System status
    python main.py --train-ml          # Train ML model
    
For more information, see docs/setup_guide.md
        """
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--mock", 
        action="store_true",
        help="Run in mock mode without hardware"
    )
    
    parser.add_argument(
        "--setup", 
        action="store_true",
        help="Run initial system setup"
    )
    
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show system status and exit"
    )
    
    parser.add_argument(
        "--train-ml", 
        action="store_true",
        help="Train ML model and exit"
    )
    
    parser.add_argument(
        "--backup", 
        action="store_true",
        help="Backup system data and exit"
    )
    
    parser.add_argument(
        "--version", 
        action="store_true",
        help="Show version information and exit"
    )
    
    parser.add_argument(
        "--config-check", 
        action="store_true",
        help="Validate configuration and exit"
    )
    
    return parser.parse_args()


def show_version():
    """Show version and system information"""
    from src import __version__, __author__, __description__
    
    print(f"""
Smart Lamp System v{__version__}
{__description__}
Created by: {__author__}

System Information:
- Python: {sys.version.split()[0]}
- Platform: {sys.platform}
- Working Directory: {os.getcwd()}
- Configuration: {"Mock Mode" if settings.MOCK_GPIO else "Hardware Mode"}
    """)


def validate_configuration():
    """Validate system configuration"""
    print("🔧 Validating Configuration...")
    
    # Check config files
    config_valid = settings.validate_config()
    hardware_valid = hardware_controller.is_initialized
    
    # Check critical files
    critical_files = [
        ".env",
        "src/config/settings.py",
        "src/config/hardware_config.py"
    ]
    
    missing_files = [f for f in critical_files if not os.path.exists(f)]
    
    # Report results
    if config_valid and hardware_valid and not missing_files:
        print("✅ Configuration is valid!")
        return True
    else:
        print("❌ Configuration issues detected:")
        if not config_valid:
            print("  - Invalid settings configuration")
        if not hardware_valid:
            print("  - Hardware configuration issues")
        if missing_files:
            print(f"  - Missing files: {', '.join(missing_files)}")
        return False


def show_system_status():
    """Show comprehensive system status"""
    print("📊 Smart Lamp System Status")
    print("=" * 50)
    
    # Get system status
    status = smart_lamp.get_status()
    health = check_system_health()
    
    # System health
    print(f"🏥 System Health: {'✅ Healthy' if health['healthy'] else '⚠️ Issues Detected'}")
    if not health['healthy']:
        for issue in health['issues']:
            print(f"   - {issue}")
    
    # Component status
    print("\n🔧 Components:")
    components = status.get('system', {}).get('components', {})
    for component, status_ok in components.items():
        symbol = "✅" if status_ok else "❌"
        print(f"   {symbol} {component.title()}: {'OK' if status_ok else 'Failed'}")
    
    # Lamp status
    lamp_status = status.get('lamp', {})
    print(f"\n💡 Lamp Status:")
    print(f"   State: {'🟢 ON' if lamp_status.get('is_on') else '🔴 OFF'}")
    print(f"   Brightness: {lamp_status.get('brightness', 0)}%")
    print(f"   Color: RGB({lamp_status.get('color', {}).get('r', 0)}, {lamp_status.get('color', {}).get('g', 0)}, {lamp_status.get('color', {}).get('b', 0)})")
    print(f"   Mode: {lamp_status.get('mode', 'unknown').title()}")
    
    # Database info
    db_info = status.get('database', {})
    if 'total_records' in db_info:
        print(f"\n💾 Database:")
        print(f"   Total Records: {db_info['total_records']:,}")
        print(f"   Size: {db_info.get('database_size_mb', 0):.1f} MB")
    
    # ML info
    ml_info = status.get('ml', {})
    if 'is_trained' in ml_info:
        print(f"\n🧠 Machine Learning:")
        print(f"   Model Trained: {'✅ Yes' if ml_info['is_trained'] else '❌ No'}")
        if ml_info['is_trained']:
            print(f"   Accuracy: {ml_info.get('model_accuracy', 0):.1%}")
            print(f"   Interactions: {ml_info.get('total_interactions', 0):,}")
    
    # Raspberry Pi info (if available)
    try:
        pi_info = get_raspberry_pi_info()
        if 'model' in pi_info and pi_info['model'] != 'Unknown':
            print(f"\n🍓 Raspberry Pi:")
            print(f"   Model: {pi_info['model']}")
            if pi_info.get('temperature'):
                print(f"   CPU Temperature: {pi_info['temperature']:.1f}°C")
    except:
        pass


async def run_initial_setup():
    """Run initial system setup"""
    print("🚀 Smart Lamp Initial Setup")
    print("=" * 40)
    
    # Check if setup already completed
    setup_marker = Path("data/.setup_complete")
    if setup_marker.exists():
        response = input("Setup already completed. Run again? (y/N): ")
        if response.lower() != 'y':
            return
    
    print("\n1. Validating configuration...")
    if not validate_configuration():
        print("❌ Setup failed: Configuration validation errors")
        return
    
    print("\n2. Initializing database...")
    try:
        db_info = db_manager.get_database_info()
        print(f"✅ Database initialized: {db_info['total_records']} records")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    print("\n3. Testing hardware components...")
    if settings.MOCK_GPIO:
        print("⚠️ Running in mock mode - hardware not tested")
    else:
        if hardware_controller.is_initialized:
            print("✅ Hardware initialized successfully")
        else:
            print("⚠️ Hardware initialization issues detected")
    
    print("\n4. Testing sensor connections...")
    try:
        sensor_status = sensor_controller.get_sensor_status()
        if sensor_status.get('api_key_configured', False):
            print("✅ Sensor APIs configured")
        else:
            print("⚠️ API keys not configured - sensors will use mock data")
    except Exception as e:
        print(f"⚠️ Sensor test failed: {e}")
    
    print("\n5. Creating initial ML training data...")
    try:
        # Create some sample interaction data for ML training
        sample_interactions = [
            {"action": "turn_on", "hour": 19, "day_of_week": 1, "is_weekend": False},
            {"action": "turn_off", "hour": 23, "day_of_week": 1, "is_weekend": False},
            {"action": "turn_on", "hour": 8, "day_of_week": 6, "is_weekend": True},
        ]
        
        for interaction in sample_interactions:
            interaction.update({
                "timestamp": datetime.now().isoformat(),
                "value": {},
                "minute": 0
            })
            db_manager.log_interaction(interaction)
        
        print("✅ Sample ML data created")
    except Exception as e:
        print(f"⚠️ ML setup failed: {e}")
    
    # Mark setup as complete
    try:
        setup_marker.parent.mkdir(exist_ok=True)
        setup_marker.touch()
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python main.py' to start the system")
        print("2. Run 'streamlit run web/app.py' for the web interface")
        print("3. Check docs/setup_guide.md for more information")
    except Exception as e:
        print(f"⚠️ Could not mark setup complete: {e}")


async def train_ml_model():
    """Train the ML model"""
    print("🧠 Training Machine Learning Model...")
    
    try:
        # Get current stats
        stats = ml_controller.get_model_stats()
        print(f"Current interactions: {stats.get('total_interactions', 0)}")
        
        if stats.get('total_interactions', 0) < settings.ML_MIN_DATA_POINTS:
            print(f"⚠️ Not enough data for training (minimum: {settings.ML_MIN_DATA_POINTS})")
            return
        
        # Train model
        success = ml_controller.train_model(force_retrain=True)
        
        if success:
            stats = ml_controller.get_model_stats()
            print(f"✅ Model trained successfully!")
            print(f"   Accuracy: {stats.get('model_accuracy', 0):.1%}")
            print(f"   Training data: {stats.get('total_interactions', 0)} interactions")
        else:
            print("❌ Model training failed")
            
    except Exception as e:
        print(f"❌ Error training model: {e}")


async def backup_system_data():
    """Backup system data"""
    print("💾 Backing up system data...")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup database
        backup_success = db_manager.backup_database(f"data/smart_lamp_backup_{timestamp}.db")
        
        if backup_success:
            print(f"✅ Database backed up: smart_lamp_backup_{timestamp}.db")
        else:
            print("❌ Database backup failed")
        
        # Backup configuration
        import shutil
        try:
            shutil.copy2("src/config/lamp_state.json", f"data/lamp_state_backup_{timestamp}.json")
            print(f"✅ Lamp state backed up: lamp_state_backup_{timestamp}.json")
        except Exception as e:
            print(f"⚠️ Lamp state backup failed: {e}")
        
        print("✅ Backup completed!")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")


async def main():
    """Main application entry point"""
    global logger
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging level based on arguments
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Initialize logger
    logger = get_logger(__name__)
    
    # Handle mock mode
    if args.mock:
        os.environ['MOCK_GPIO'] = 'True'
        os.environ['MOCK_SENSORS'] = 'True'
        logger.info("Running in mock mode")
    
    # Handle version command
    if args.version:
        show_version()
        return
    
    # Handle config check command
    if args.config_check:
        if validate_configuration():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Handle status command
    if args.status:
        show_system_status()
        return
    
    # Handle setup command
    if args.setup:
        await run_initial_setup()
        return
    
    # Handle ML training command
    if args.train_ml:
        await train_ml_model()
        return
    
    # Handle backup command
    if args.backup:
        await backup_system_data()
        return
    
    # Normal operation - start Smart Lamp system
    try:
        # Show startup banner
        show_version()
        print("\n🚀 Starting Smart Lamp System...")
        
        # Validate configuration
        if not validate_configuration():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        # Start the Smart Lamp system
        logger.info("Initializing Smart Lamp system...")
        
        # Start smart lamp in background task
        lamp_task = asyncio.create_task(smart_lamp.start())
        
        # Wait for shutdown signal or lamp completion
        try:
            await asyncio.wait([
                asyncio.create_task(shutdown_event.wait()),
                lamp_task
            ], return_when=asyncio.FIRST_COMPLETED)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        # Graceful shutdown
        logger.info("Initiating graceful shutdown...")
        await smart_lamp.shutdown()
        
        # Cancel remaining tasks
        if not lamp_task.done():
            lamp_task.cancel()
            try:
                await lamp_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Smart Lamp system shut down successfully")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Smart Lamp system stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)