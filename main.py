"""
Smart Lamp Main Application

This is the main entry point for the Smart Lamp system.
Starts all components and manages the application lifecycle.

Usage:
    python main.py              # Start with default settings
    python main.py --debug      # Start with debug logging
    python main.py --no-web     # Start without web interface
    python main.py --setup      # Run setup first
"""

import os
import sys
import signal
import time
import logging
import argparse
import threading
import subprocess
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings
from src.lamp import LampController
from src.utils import Utils

class SmartLampApp:
    """Main Smart Lamp application"""
    
    def __init__(self, debug=False, enable_web=True):
        self.debug = debug
        self.enable_web = enable_web
        self.utils = Utils()
        
        # Setup logging
        log_level = "DEBUG" if debug else settings.LOG_LEVEL
        self.utils.setup_logging(settings.LOG_FILE_PATH, log_level)
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.lamp_controller = None
        self.web_process = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Smart Lamp Application initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
    
    def check_setup(self):
        """Check if system is properly set up"""
        self.logger.info("Checking system setup...")
        
        required_files = ['.env']
        required_dirs = ['data', 'logs', 'models']
        
        issues = []
        
        # Check required files
        for file_path in required_files:
            if not os.path.exists(file_path):
                issues.append(f"Missing file: {file_path}")
        
        # Check required directories
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                issues.append(f"Missing directory: {dir_path}")
        
        # Check database
        if not os.path.exists(settings.DATABASE_PATH):
            issues.append("Database not initialized")
        
        if issues:
            self.logger.error("Setup issues found:")
            for issue in issues:
                self.logger.error(f"  - {issue}")
            self.logger.error("Run 'python setup.py' to fix these issues")
            return False
        
        self.logger.info("✓ System setup verification passed")
        return True
    
    def start_lamp_controller(self):
        """Initialize and start the lamp controller"""
        self.logger.info("Starting lamp controller...")
        
        try:
            self.lamp_controller = LampController()
            self.lamp_controller.start_automation()
            
            self.logger.info("✓ Lamp controller started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start lamp controller: {e}")
            return False
    
    def start_web_interface(self):
        """Start the Streamlit web interface"""
        if not self.enable_web:
            self.logger.info("Web interface disabled")
            return True
        
        self.logger.info("Starting web interface...")
        
        try:
            web_app_path = os.path.join('web', 'app.py')
            
            if not os.path.exists(web_app_path):
                self.logger.warning(f"Web app not found at {web_app_path}")
                return False
            
            # Start Streamlit in a subprocess
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 
                web_app_path,
                '--server.port', str(settings.STREAMLIT_PORT),
                '--server.address', '0.0.0.0',
                '--server.headless', 'true',
                '--logger.level', 'warning'
            ]
            
            self.web_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            if self.web_process.poll() is None:
                self.logger.info(f"✓ Web interface started on port {settings.STREAMLIT_PORT}")
                self.logger.info(f"  Access at: http://localhost:{settings.STREAMLIT_PORT}")
                return True
            else:
                self.logger.error("Web interface failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start web interface: {e}")
            return False
    
    def monitor_system(self):
        """Monitor system health and performance"""
        self.logger.info("Starting system monitoring...")
        
        monitoring_thread = threading.Thread(target=self._monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()
    
    def _monitoring_loop(self):
        """System monitoring loop"""
        last_health_check = 0
        last_cleanup = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Health check every 5 minutes
                if current_time - last_health_check > 300:
                    self._health_check()
                    last_health_check = current_time
                
                # Cleanup old data every day
                if current_time - last_cleanup > 86400:
                    self._cleanup_old_data()
                    last_cleanup = current_time
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _health_check(self):
        """Perform system health check"""
        try:
            # Check system resources
            sys_info = self.utils.get_system_info()
            
            # Log warnings for high resource usage
            if sys_info.get('cpu_percent', 0) > 80:
                self.logger.warning(f"High CPU usage: {sys_info['cpu_percent']:.1f}%")
            
            if sys_info.get('memory_percent', 0) > 80:
                self.logger.warning(f"High memory usage: {sys_info['memory_percent']:.1f}%")
            
            if sys_info.get('disk_percent', 0) > 90:
                self.logger.warning(f"Low disk space: {sys_info['disk_percent']:.1f}% used")
            
            # Check lamp controller status
            if self.lamp_controller:
                status = self.lamp_controller.get_status()
                self.logger.debug(f"Lamp status: {status['lamp']}")
            
            # Check web interface
            if self.web_process and self.web_process.poll() is not None:
                self.logger.warning("Web interface process has stopped")
        
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data to save space"""
        try:
            if self.lamp_controller:
                self.lamp_controller.db.cleanup_old_data(30)  # Keep 30 days
                self.logger.info("Cleaned up old database records")
        
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
    
    def display_startup_info(self):
        """Display startup information"""
        print("\n" + "=" * 60)
        print("🏮 SMART LAMP SYSTEM")
        print("=" * 60)
        print(f"🔧 Configuration:")
        print(f"   • Database: {settings.DATABASE_PATH}")
        print(f"   • Log file: {settings.LOG_FILE_PATH}")
        print(f"   • ML model: {settings.ML_MODEL_PATH}")
        print(f"   • Web port: {settings.STREAMLIT_PORT}")
        print(f"   • Debug mode: {self.debug}")
        print(f"   • Web interface: {'Enabled' if self.enable_web else 'Disabled'}")
        
        if settings.is_api_key_valid():
            print(f"   • APIs: Weather and Air Quality configured")
        else:
            print(f"   • APIs: Only earthquake monitoring (no API key)")
        
        print(f"\n🎯 Features:")
        print(f"   • Manual controls (buttons, potentiometer)")
        print(f"   • Environmental monitoring (earthquake, weather, air quality)")
        print(f"   • Machine learning (user pattern recognition)")
        print(f"   • Web dashboard (real-time status and controls)")
        print(f"   • State persistence (remembers settings)")
        
        print(f"\n📱 Access:")
        if self.enable_web:
            print(f"   • Web Interface: http://localhost:{settings.STREAMLIT_PORT}")
        print(f"   • Logs: {settings.LOG_FILE_PATH}")
        print(f"   • Press Ctrl+C to shutdown gracefully")
        print("=" * 60)
    
    def run(self):
        """Run the Smart Lamp application"""
        self.logger.info("Starting Smart Lamp Application...")
        
        # Display startup information
        self.display_startup_info()
        
        # Check system setup
        if not self.check_setup():
            print("\n❌ System setup verification failed!")
            print("Run 'python setup.py' to fix setup issues.")
            return False
        
        # Start lamp controller
        if not self.start_lamp_controller():
            print("\n❌ Failed to start lamp controller!")
            return False
        
        # Start web interface
        if not self.start_web_interface() and self.enable_web:
            print("\n⚠️  Web interface failed to start, continuing without it...")
        
        # Start system monitoring
        self.monitor_system()
        
        # Mark as running
        self.running = True
        
        print(f"\n✅ Smart Lamp system started successfully!")
        if self.enable_web:
            print(f"🌐 Web interface: http://localhost:{settings.STREAMLIT_PORT}")
        print(f"📝 Logs: tail -f {settings.LOG_FILE_PATH}")
        print(f"⏹️  Press Ctrl+C to stop\n")
        
        # Main application loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        
        return True
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        if not self.running:
            return
        
        self.logger.info("Shutting down Smart Lamp Application...")
        self.running = False
        
        print("\n🔄 Shutting down Smart Lamp...")
        
        # Stop lamp controller
        if self.lamp_controller:
            print("  • Stopping lamp controller...")
            self.lamp_controller.cleanup()
        
        # Stop web interface
        if self.web_process:
            print("  • Stopping web interface...")
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.web_process.kill()
        
        print("✅ Smart Lamp shutdown completed")
        self.logger.info("Smart Lamp Application shutdown completed")

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Smart Lamp Control System')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-web', action='store_true', help='Disable web interface')
    parser.add_argument('--setup', action='store_true', help='Run setup before starting')
    parser.add_argument('--version', action='version', version='Smart Lamp v1.0.0')
    
    args = parser.parse_args()
    
    try:
        # Run setup if requested
        if args.setup:
            print("Running setup first...")
            setup_result = os.system('python setup.py')
            if setup_result != 0:
                print("❌ Setup failed!")
                sys.exit(1)
            print("✅ Setup completed, starting application...\n")
        
        # Create and run application
        app = SmartLampApp(debug=args.debug, enable_web=not args.no_web)
        success = app.run()
        
        if not success:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Application interrupted")
    except Exception as e:
        print(f"\n💥 Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()