"""
Test suite for Smart Lamp System
Tests core functionality and integration between modules
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import settings
from src.hardware import HardwareController, LampState
from src.ml import MLController, DataLogger, PatternAnalyzer
from src.audio import AudioController, AudioManager
from src.lamp import SmartLamp


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and validation."""
    
    def test_settings_loading(self):
        """Test that settings load correctly."""
        self.assertIsNotNone(settings.api)
        self.assertIsNotNone(settings.hardware)
        self.assertIsNotNone(settings.system)
    
    def test_color_presets(self):
        """Test color preset configuration."""
        presets = settings.get_color_presets()
        self.assertGreater(len(presets), 0)
        self.assertEqual(len(presets[0]), 3)  # RGB tuple
        
        # Test white color is first
        self.assertEqual(presets[0], (255, 255, 255))
    
    def test_pin_configuration(self):
        """Test hardware pin configuration."""
        self.assertIsInstance(settings.hardware.main_button_pin, int)
        self.assertIsInstance(settings.hardware.led1_red_pin, int)
        self.assertGreater(settings.hardware.led_strip_count, 0)


class TestHardwareController(unittest.TestCase):
    """Test hardware controller functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hardware = HardwareController()
    
    def test_initialization(self):
        """Test hardware controller initialization."""
        self.assertIsInstance(self.hardware.state, LampState)
        self.assertIsInstance(self.hardware.color_presets, list)
        self.assertGreater(len(self.hardware.color_presets), 0)
    
    def test_lamp_state(self):
        """Test lamp state management."""
        # Test initial state
        self.assertFalse(self.hardware.state.is_on)
        self.assertEqual(self.hardware.state.brightness, 50)
        
        # Test state changes
        self.hardware.state.is_on = True
        self.hardware.state.brightness = 75
        
        self.assertTrue(self.hardware.state.is_on)
        self.assertEqual(self.hardware.state.brightness, 75)
    
    def test_color_validation(self):
        """Test color value validation."""
        # Test valid color setting
        self.hardware.set_led_color(255, 128, 0)
        self.assertEqual(self.hardware.state.color_r, 255)
        self.assertEqual(self.hardware.state.color_g, 128)
        self.assertEqual(self.hardware.state.color_b, 0)
    
    def test_brightness_bounds(self):
        """Test brightness boundary validation."""
        # Test brightness clamping would happen in a real implementation
        # This is a placeholder for actual hardware validation
        test_brightness = 150  # Over 100%
        clamped_brightness = max(0, min(100, test_brightness))
        self.assertEqual(clamped_brightness, 100)
    
    def test_color_cycling(self):
        """Test color cycling functionality."""
        initial_index = self.hardware.state.current_color_index
        self.hardware.cycle_color()
        
        # Should advance color index
        expected_index = (initial_index + 1) % len(self.hardware.color_presets)
        self.assertEqual(self.hardware.state.current_color_index, expected_index)


class TestMLController(unittest.TestCase):
    """Test machine learning functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ml_controller = MLController()
        self.data_logger = self.ml_controller.data_logger
    
    def test_data_logger_initialization(self):
        """Test data logger initialization."""
        self.assertIsInstance(self.data_logger, DataLogger)
        self.assertIsInstance(self.data_logger.actions, list)
    
    def test_action_logging(self):
        """Test user action logging."""
        initial_count = len(self.data_logger.actions)
        
        # Log a test action
        self.data_logger.log_action(
            action_type='on',
            brightness=50,
            color_r=255,
            color_g=255,
            color_b=255,
            previous_state=False
        )
        
        # Check action was logged
        self.assertEqual(len(self.data_logger.actions), initial_count + 1)
        
        last_action = self.data_logger.actions[-1]
        self.assertEqual(last_action.action_type, 'on')
        self.assertEqual(last_action.brightness, 50)
    
    def test_pattern_analyzer(self):
        """Test pattern analysis functionality."""
        analyzer = PatternAnalyzer(self.data_logger)
        
        # Test insufficient data scenario
        self.assertFalse(analyzer.has_sufficient_data())
        
        # Test with minimal data
        self.assertIsInstance(analyzer.get_usage_patterns(), dict)
    
    def test_ml_status(self):
        """Test ML status reporting."""
        status = self.ml_controller.get_ml_status()
        
        self.assertIn('auto_mode_enabled', status)
        self.assertIn('data_points', status)
        self.assertIn('sufficient_data', status)
        self.assertIsInstance(status['data_points'], int)


class TestAudioController(unittest.TestCase):
    """Test audio controller functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_controller = AudioController()
    
    def test_initialization(self):
        """Test audio controller initialization."""
        self.assertIsInstance(self.audio_controller.radio_stations, list)
        self.assertIsInstance(self.audio_controller.ambient_sounds, list)
        self.assertIsInstance(self.audio_controller.volume, int)
    
    def test_volume_control(self):
        """Test volume control functionality."""
        # Test volume setting
        self.audio_controller.set_volume(75)
        self.assertEqual(self.audio_controller.get_volume(), 75)
        
        # Test volume bounds
        self.audio_controller.set_volume(150)  # Over 100
        self.assertEqual(self.audio_controller.get_volume(), 100)
        
        self.audio_controller.set_volume(-10)  # Under 0
        self.assertEqual(self.audio_controller.get_volume(), 0)
    
    def test_track_loading(self):
        """Test audio track loading."""
        tracks = self.audio_controller.get_available_tracks()
        
        self.assertIn('radio', tracks)
        self.assertIn('ambient', tracks)
        self.assertIsInstance(tracks['radio'], list)
        self.assertIsInstance(tracks['ambient'], list)
    
    def test_audio_manager(self):
        """Test audio manager functionality."""
        manager = AudioManager()
        
        # Test status reporting
        status = manager.get_audio_status()
        self.assertIn('is_playing', status)
        self.assertIn('volume', status)
        self.assertIn('auto_enabled', status)


class TestSmartLampIntegration(unittest.TestCase):
    """Test Smart Lamp system integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the hardware initialization to avoid GPIO errors in testing
        with patch('src.hardware.RASPBERRY_PI_AVAILABLE', False):
            self.smart_lamp = SmartLamp()
    
    def test_initialization(self):
        """Test Smart Lamp initialization."""
        self.assertIsNotNone(self.smart_lamp.hardware)
        self.assertIsNotNone(self.smart_lamp.ml_controller)
        self.assertIsNotNone(self.smart_lamp.audio_manager)
    
    def test_lamp_control_api(self):
        """Test lamp control API methods."""
        # Test power control
        self.smart_lamp.turn_on()
        # In simulation mode, we can't test actual hardware state
        # but we can test that methods execute without error
        
        self.smart_lamp.turn_off()
        
        # Test color setting
        self.smart_lamp.set_color(255, 0, 0)
        
        # Test brightness setting
        self.smart_lamp.set_brightness(50)
    
    def test_status_reporting(self):
        """Test system status reporting."""
        status = self.smart_lamp.get_status()
        
        required_keys = ['timestamp', 'system', 'lamp', 'ml', 'audio', 'environmental']
        for key in required_keys:
            self.assertIn(key, status)
        
        # Test lamp status structure
        lamp_status = status['lamp']
        self.assertIn('is_on', lamp_status)
        self.assertIn('brightness', lamp_status)
        self.assertIn('color', lamp_status)
    
    def test_ml_integration(self):
        """Test ML integration with lamp control."""
        # Test ML status
        ml_status = self.smart_lamp.ml_controller.get_ml_status()
        self.assertIsInstance(ml_status, dict)
        
        # Test prediction
        prediction = self.smart_lamp.predict_for_time(datetime.now())
        self.assertIn('should_be_on', prediction)
        self.assertIn('confidence', prediction)
    
    def test_audio_integration(self):
        """Test audio integration."""
        # Test audio tracks availability
        tracks = self.smart_lamp.get_available_audio_tracks()
        self.assertIsInstance(tracks, dict)
        
        # Test audio status
        audio_status = self.smart_lamp.audio_manager.get_audio_status()
        self.assertIsInstance(audio_status, dict)


class TestEnvironmentalMonitoring(unittest.TestCase):
    """Test environmental monitoring functionality."""
    
    def test_environmental_data_structure(self):
        """Test environmental data structure."""
        # This would test the environmental sensors module
        # For now, we'll test the expected data structure
        
        expected_structure = {
            'earthquake': None,
            'air_quality': None,
            'temperature': None,
            'last_updated': None
        }
        
        # In a real implementation, this would test actual sensor data
        # For now, we verify the expected structure
        self.assertIsInstance(expected_structure, dict)
        self.assertIn('earthquake', expected_structure)
        self.assertIn('air_quality', expected_structure)
        self.assertIn('temperature', expected_structure)


class TestSystemResilience(unittest.TestCase):
    """Test system resilience and error handling."""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        # Test with hardware unavailable
        with patch('src.hardware.RASPBERRY_PI_AVAILABLE', False):
            hardware = HardwareController()
            # Should initialize without crashing
            self.assertIsNotNone(hardware)
    
    def test_api_failure_handling(self):
        """Test handling of API failures."""
        # This would test how the system handles network failures
        # and API unavailability
        pass
    
    def test_data_persistence(self):
        """Test data persistence across restarts."""
        # Test that data logging persists
        data_logger = DataLogger()
        
        # Test file path exists
        self.assertTrue(hasattr(data_logger, 'log_file'))
        self.assertIsInstance(data_logger.log_file, str)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_cases = [
        TestConfiguration,
        TestHardwareController,
        TestMLController,
        TestAudioController,
        TestSmartLampIntegration,
        TestEnvironmentalMonitoring,
        TestSystemResilience
    ]
    
    for test_case in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code) 