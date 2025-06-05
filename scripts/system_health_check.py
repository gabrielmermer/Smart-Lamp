#!/usr/bin/env python3
"""
Smart Lamp System Health Check Script
VIP Project - Group E

Performs comprehensive health checks on the Smart Lamp system.
Team: Gabriel, Leyla, Chaw Khin Su, Shohruh, Mansurbek
"""

import os
import sys
import json
import time
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Any, Tuple
import subprocess

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import settings


class HealthChecker:
    """System health checker for Smart Lamp."""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        self.start_time = datetime.now()
    
    def add_check(self, name: str, status: str, message: str, details: Dict = None):
        """Add a health check result."""
        check = {
            'name': name,
            'status': status,  # 'pass', 'warn', 'fail'
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.checks.append(check)
        
        if status == 'warn':
            self.warnings.append(check)
        elif status == 'fail':
            self.errors.append(check)
    
    def check_python_environment(self) -> None:
        """Check Python environment and dependencies."""
        print("🐍 Checking Python Environment...")
        
        # Python version
        python_version = platform.python_version()
        if python_version >= "3.8.0":
            self.add_check(
                "Python Version", "pass",
                f"Python {python_version} is supported",
                {"version": python_version}
            )
        else:
            self.add_check(
                "Python Version", "fail",
                f"Python {python_version} is too old (minimum 3.8 required)",
                {"version": python_version}
            )
        
        # Required packages
        required_packages = [
            'streamlit', 'plotly', 'pandas', 'numpy', 'scikit-learn',
            'pygame', 'requests', 'python-dotenv', 'psutil'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.add_check(
                    f"Package: {package}", "pass",
                    f"{package} is installed"
                )
            except ImportError:
                missing_packages.append(package)
                self.add_check(
                    f"Package: {package}", "fail",
                    f"{package} is not installed"
                )
        
        if missing_packages:
            self.add_check(
                "Dependencies", "fail",
                f"Missing packages: {', '.join(missing_packages)}"
            )
    
    def check_system_resources(self) -> None:
        """Check system resources."""
        print("💻 Checking System Resources...")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent < 80:
            self.add_check(
                "CPU Usage", "pass",
                f"CPU usage is {cpu_percent}%",
                {"usage": cpu_percent}
            )
        elif cpu_percent < 95:
            self.add_check(
                "CPU Usage", "warn",
                f"CPU usage is high: {cpu_percent}%",
                {"usage": cpu_percent}
            )
        else:
            self.add_check(
                "CPU Usage", "fail",
                f"CPU usage is critical: {cpu_percent}%",
                {"usage": cpu_percent}
            )
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        if memory_percent < 80:
            self.add_check(
                "Memory Usage", "pass",
                f"Memory usage is {memory_percent}% ({memory_available_gb:.1f}GB available)",
                {"usage_percent": memory_percent, "available_gb": memory_available_gb}
            )
        elif memory_percent < 95:
            self.add_check(
                "Memory Usage", "warn",
                f"Memory usage is high: {memory_percent}%",
                {"usage_percent": memory_percent, "available_gb": memory_available_gb}
            )
        else:
            self.add_check(
                "Memory Usage", "fail",
                f"Memory usage is critical: {memory_percent}%",
                {"usage_percent": memory_percent, "available_gb": memory_available_gb}
            )
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        
        if disk_percent < 85:
            self.add_check(
                "Disk Usage", "pass",
                f"Disk usage is {disk_percent:.1f}% ({disk_free_gb:.1f}GB free)",
                {"usage_percent": disk_percent, "free_gb": disk_free_gb}
            )
        elif disk_percent < 95:
            self.add_check(
                "Disk Usage", "warn",
                f"Disk usage is high: {disk_percent:.1f}%",
                {"usage_percent": disk_percent, "free_gb": disk_free_gb}
            )
        else:
            self.add_check(
                "Disk Usage", "fail",
                f"Disk usage is critical: {disk_percent:.1f}%",
                {"usage_percent": disk_percent, "free_gb": disk_free_gb}
            )
    
    def check_raspberry_pi_hardware(self) -> None:
        """Check Raspberry Pi specific hardware."""
        print("🔌 Checking Raspberry Pi Hardware...")
        
        # Check if running on Raspberry Pi
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip('\x00')
            
            if 'Raspberry Pi' in model:
                self.add_check(
                    "Hardware Platform", "pass",
                    f"Running on {model}",
                    {"model": model}
                )
                
                # Check GPIO permissions
                try:
                    import RPi.GPIO
                    RPi.GPIO.setmode(RPi.GPIO.BCM)
                    self.add_check(
                        "GPIO Access", "pass",
                        "GPIO access is available"
                    )
                    RPi.GPIO.cleanup()
                except Exception as e:
                    self.add_check(
                        "GPIO Access", "fail",
                        f"GPIO access failed: {str(e)}"
                    )
                
                # Check CPU temperature
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        temp = int(f.read()) / 1000.0
                    
                    if temp < 70:
                        self.add_check(
                            "CPU Temperature", "pass",
                            f"CPU temperature is {temp:.1f}°C",
                            {"temperature": temp}
                        )
                    elif temp < 80:
                        self.add_check(
                            "CPU Temperature", "warn",
                            f"CPU temperature is elevated: {temp:.1f}°C",
                            {"temperature": temp}
                        )
                    else:
                        self.add_check(
                            "CPU Temperature", "fail",
                            f"CPU temperature is too high: {temp:.1f}°C",
                            {"temperature": temp}
                        )
                except Exception as e:
                    self.add_check(
                        "CPU Temperature", "warn",
                        f"Could not read CPU temperature: {str(e)}"
                    )
            
            else:
                self.add_check(
                    "Hardware Platform", "warn",
                    f"Not running on Raspberry Pi: {model}",
                    {"model": model}
                )
        
        except FileNotFoundError:
            self.add_check(
                "Hardware Platform", "warn",
                "Not running on Raspberry Pi (simulation mode)"
            )
    
    def check_configuration(self) -> None:
        """Check system configuration."""
        print("⚙️ Checking Configuration...")
        
        # Check .env file
        env_file = '.env'
        if os.path.exists(env_file):
            self.add_check(
                "Environment File", "pass",
                ".env file exists"
            )
        else:
            self.add_check(
                "Environment File", "warn",
                ".env file not found, using defaults"
            )
        
        # Check API keys
        if settings.api.openweather_api_key:
            self.add_check(
                "OpenWeather API Key", "pass",
                "API key is configured"
            )
        else:
            self.add_check(
                "OpenWeather API Key", "warn",
                "API key not configured - weather features disabled"
            )
        
        # Check data directories
        data_dirs = [
            os.path.dirname(settings.system.data_log_path),
            settings.system.model_save_path,
            settings.system.ambient_sounds_path
        ]
        
        for dir_path in data_dirs:
            if os.path.exists(dir_path):
                self.add_check(
                    f"Data Directory: {dir_path}", "pass",
                    "Directory exists"
                )
            else:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    self.add_check(
                        f"Data Directory: {dir_path}", "pass",
                        "Directory created"
                    )
                except Exception as e:
                    self.add_check(
                        f"Data Directory: {dir_path}", "fail",
                        f"Could not create directory: {str(e)}"
                    )
    
    def check_network_connectivity(self) -> None:
        """Check network connectivity."""
        print("🌐 Checking Network Connectivity...")
        
        # Check internet connectivity
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                self.add_check(
                    "Internet Connectivity", "pass",
                    "Internet connection is working"
                )
            else:
                self.add_check(
                    "Internet Connectivity", "warn",
                    f"Unexpected response: {response.status_code}"
                )
        except Exception as e:
            self.add_check(
                "Internet Connectivity", "fail",
                f"No internet connection: {str(e)}"
            )
        
        # Check OpenWeather API
        if settings.api.openweather_api_key:
            try:
                import requests
                url = f"{settings.api.openweather_base_url}/weather"
                params = {
                    'lat': settings.api.latitude,
                    'lon': settings.api.longitude,
                    'appid': settings.api.openweather_api_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    self.add_check(
                        "OpenWeather API", "pass",
                        "API is accessible"
                    )
                else:
                    self.add_check(
                        "OpenWeather API", "fail",
                        f"API error: {response.status_code}"
                    )
            except Exception as e:
                self.add_check(
                    "OpenWeather API", "fail",
                    f"API connection failed: {str(e)}"
                )
    
    def check_smart_lamp_components(self) -> None:
        """Check Smart Lamp specific components."""
        print("🏮 Checking Smart Lamp Components...")
        
        # Test imports
        components = [
            ('Hardware Controller', 'src.hardware', 'HardwareController'),
            ('Sensor Controller', 'src.sensors', 'SensorController'),
            ('Audio Controller', 'src.audio', 'AudioController'),
            ('ML Controller', 'src.ml', 'MLController'),
            ('Smart Lamp', 'src.lamp', 'SmartLamp'),
        ]
        
        for component_name, module_name, class_name in components:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.add_check(
                    f"Component: {component_name}", "pass",
                    f"{component_name} can be imported"
                )
            except Exception as e:
                self.add_check(
                    f"Component: {component_name}", "fail",
                    f"Import failed: {str(e)}"
                )
    
    def check_web_interface(self) -> None:
        """Check web interface components."""
        print("🌐 Checking Web Interface...")
        
        # Check Streamlit
        try:
            import streamlit as st
            self.add_check(
                "Streamlit", "pass",
                "Streamlit is available"
            )
        except Exception as e:
            self.add_check(
                "Streamlit", "fail",
                f"Streamlit import failed: {str(e)}"
            )
        
        # Check web files
        web_files = ['web/app.py', 'web/components.py']
        for file_path in web_files:
            if os.path.exists(file_path):
                self.add_check(
                    f"Web File: {file_path}", "pass",
                    "File exists"
                )
            else:
                self.add_check(
                    f"Web File: {file_path}", "fail",
                    "File missing"
                )
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        print("🔍 Starting Smart Lamp System Health Check")
        print("=" * 50)
        
        # Run checks
        self.check_python_environment()
        self.check_system_resources()
        self.check_raspberry_pi_hardware()
        self.check_configuration()
        self.check_network_connectivity()
        self.check_smart_lamp_components()
        self.check_web_interface()
        
        # Calculate summary
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c['status'] == 'pass'])
        warning_checks = len(self.warnings)
        failed_checks = len(self.errors)
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'total_checks': total_checks,
            'passed': passed_checks,
            'warnings': warning_checks,
            'failures': failed_checks,
            'overall_status': 'fail' if failed_checks > 0 else 'warn' if warning_checks > 0 else 'pass',
            'checks': self.checks
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print health check summary."""
        print("\n" + "=" * 50)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        # Overall status
        status_emoji = {
            'pass': '✅',
            'warn': '⚠️',
            'fail': '❌'
        }
        
        print(f"Overall Status: {status_emoji[summary['overall_status']]} {summary['overall_status'].upper()}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"❌ Failures: {summary['failures']}")
        
        # Show failures
        if self.errors:
            print("\n❌ FAILURES:")
            for error in self.errors:
                print(f"  • {error['name']}: {error['message']}")
        
        # Show warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning['name']}: {warning['message']}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if self.errors:
            print("  • Fix critical errors before running the Smart Lamp system")
        if self.warnings:
            print("  • Review warnings for optimal performance")
        if not self.errors and not self.warnings:
            print("  • System is healthy and ready to run!")
        
        print("\n🏮 Smart Lamp System Health Check Complete")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Lamp System Health Check')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--output', type=str, help='Save results to file')
    
    args = parser.parse_args()
    
    # Run health checks
    checker = HealthChecker()
    summary = checker.run_all_checks()
    
    if args.json:
        # JSON output
        json_output = json.dumps(summary, indent=2)
        print(json_output)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
    else:
        # Pretty print output
        checker.print_summary(summary)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json.dumps(summary, indent=2))
    
    # Exit with appropriate code
    exit_code = 0 if summary['overall_status'] == 'pass' else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
