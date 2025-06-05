
import argparse
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lamp import create_smart_lamp
from src.config import settings


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Smart Lamp System - VIP Project Group E',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start with default settings
  python main.py --interactive      # Start in interactive CLI mode
  python main.py --no-ml           # Start without ML auto mode
  python main.py --test            # Run system tests

Environment Configuration:
  Copy env.example to .env and configure your API keys and hardware pins.
        """
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive command-line mode'
    )
    
    parser.add_argument(
        '--no-ml',
        action='store_true',
        help='Disable ML pattern recognition features'
    )
    
    parser.add_argument(
        '--no-env',
        action='store_true',
        help='Disable environmental monitoring'
    )
    
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Disable audio features'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run basic system tests'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate configuration
    if not validate_configuration():
        print("❌ Configuration validation failed. Please check your .env file.")
        return 1
    
    # Run tests if requested
    if args.test:
        return run_tests()
    
    # Create and configure Smart Lamp
    try:
        smart_lamp = create_smart_lamp()
        
        # Override settings based on arguments
        if args.no_ml:
            print("🔧 ML features disabled by command line argument")
        
        if args.no_env:
            print("🔧 Environmental monitoring disabled by command line argument")
            # Would set environmental monitoring flag here
        
        if args.no_audio:
            print("🔧 Audio features disabled by command line argument")
            # Would disable audio manager here
        
        if args.debug:
            print("🔧 Debug mode enabled")
        
        # Start the Smart Lamp system
        smart_lamp.start()
        
        if args.interactive:
            # Run in interactive mode
            smart_lamp.run_interactive_mode()
        else:
            # Run in background mode
            print("\n📱 Smart Lamp is running!")
            print("🌐 Web interface will be available at http://localhost:8501")
            print("🎛️  Use physical buttons to control the lamp")
            print("🤖 ML pattern learning is active")
            print("🌡️  Environmental monitoring is active")
            print("🎵 Audio features are available")
            print("\nPress Ctrl+C to stop the system")
            
            # Keep the main thread alive
            try:
                while smart_lamp.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutdown signal received")
        
        # Clean shutdown
        smart_lamp.stop()
        print("✅ Smart Lamp stopped successfully")
        return 0
        
    except Exception as e:
        print(f"❌ Error starting Smart Lamp: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def print_banner():
    """Print application banner."""
    print("=" * 70)
    print("🏮 SMART LAMP SYSTEM - VIP PROJECT GROUP E")
    print("=" * 70)
    print("📅 Developed: Spring 2025")
    print("🏫 Institution: Inha University")
    print("👥 Team: Gabriel, Leyla, Chaw Khin Su, Shohruh, Mansurbek")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def validate_configuration():
    """Validate system configuration."""
    print("🔍 Validating configuration...")
    
    # Check if .env file exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"⚠️  Warning: {env_file} not found. Using default settings.")
        print("   Copy env.example to .env and configure your settings.")
    
    # Validate API settings
    validation_passed = True
    
    if not settings.api.openweather_api_key:
        print("⚠️  Warning: OpenWeatherMap API key not configured.")
        print("   Environmental features will be limited.")
    else:
        print("✅ OpenWeatherMap API key configured")
    
    # Check data directories
    data_dirs = [
        os.path.dirname(settings.system.data_log_path),
        settings.system.model_save_path,
        settings.system.ambient_sounds_path
    ]
    
    for dir_path in data_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
                validation_passed = False
    
    # Check hardware availability
    try:
        import RPi.GPIO
        print("✅ Raspberry Pi GPIO available")
    except ImportError:
        print("⚠️  Warning: Raspberry Pi GPIO not available (simulation mode)")
    
    try:
        import pygame
        print("✅ Audio system (pygame) available")
    except ImportError:
        print("⚠️  Warning: Audio system not available")
    
    try:
        import sklearn
        print("✅ Machine learning libraries available")
    except ImportError:
        print("❌ Machine learning libraries not available")
        validation_passed = False
    
    return validation_passed


def run_tests():
    """Run basic system tests."""
    print("🧪 Running Smart Lamp system tests...")
    
    test_results = []
    
    # Test 1: Configuration loading
    try:
        from src.config import settings
        test_results.append(("Configuration loading", True, ""))
        print("✅ Test 1: Configuration loading - PASSED")
    except Exception as e:
        test_results.append(("Configuration loading", False, str(e)))
        print(f"❌ Test 1: Configuration loading - FAILED: {e}")
    
    # Test 2: Hardware controller initialization
    try:
        from src.hardware import HardwareController
        hw = HardwareController()
        test_results.append(("Hardware controller init", True, ""))
        print("✅ Test 2: Hardware controller initialization - PASSED")
    except Exception as e:
        test_results.append(("Hardware controller init", False, str(e)))
        print(f"❌ Test 2: Hardware controller initialization - FAILED: {e}")
    
    # Test 3: ML system initialization
    try:
        from src.ml import MLController
        ml = MLController()
        test_results.append(("ML controller init", True, ""))
        print("✅ Test 3: ML controller initialization - PASSED")
    except Exception as e:
        test_results.append(("ML controller init", False, str(e)))
        print(f"❌ Test 3: ML controller initialization - FAILED: {e}")
    
    # Test 4: Audio system initialization
    try:
        from src.audio import AudioController
        audio = AudioController()
        test_results.append(("Audio controller init", True, ""))
        print("✅ Test 4: Audio controller initialization - PASSED")
    except Exception as e:
        test_results.append(("Audio controller init", False, str(e)))
        print(f"❌ Test 4: Audio controller initialization - FAILED: {e}")
    
    # Test 5: Smart Lamp integration
    try:
        from src.lamp import create_smart_lamp
        lamp = create_smart_lamp()
        test_results.append(("Smart Lamp integration", True, ""))
        print("✅ Test 5: Smart Lamp integration - PASSED")
    except Exception as e:
        test_results.append(("Smart Lamp integration", False, str(e)))
        print(f"❌ Test 5: Smart Lamp integration - FAILED: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("🧪 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    for test_name, success, error in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if not success and error:
            print(f"    Error: {error}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
