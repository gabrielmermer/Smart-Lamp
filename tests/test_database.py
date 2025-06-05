import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta

from src.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database manager
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Check if database file exists
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables are created
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'user_interactions',
            'environmental_data',
            'system_events',
            'ml_predictions',
            'audio_sessions',
            'config_history'
        ]
        
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_log_user_interaction(self):
        """Test logging user interactions."""
        # Log a user interaction
        interaction_id = self.db.log_user_interaction(
            interaction_type="brightness_change",
            brightness=75,
            color_temp=4000,
            rgb_color=(255, 255, 255),
            context={"source": "button"},
            environmental_data={"temperature": 22.5}
        )
        
        self.assertGreater(interaction_id, 0)
        
        # Retrieve and verify
        interactions = self.db.get_user_interactions(hours_back=1, limit=10)
        self.assertEqual(len(interactions), 1)
        
        interaction = interactions[0]
        self.assertEqual(interaction['interaction_type'], "brightness_change")
        self.assertEqual(interaction['brightness'], 75)
        self.assertEqual(interaction['color_temp'], 4000)
        self.assertEqual(interaction['rgb_color'], [255, 255, 255])
        self.assertEqual(interaction['context']['source'], "button")
    
    def test_log_environmental_data(self):
        """Test logging environmental data."""
        # Log environmental data
        record_id = self.db.log_environmental_data(
            temperature=23.5,
            humidity=45.2,
            air_quality=85,
            noise_level=35.0,
            light_level=450.0,
            weather_condition="sunny",
            earthquake_detected=False
        )
        
        self.assertGreater(record_id, 0)
        
        # Retrieve and verify
        env_data = self.db.get_environmental_data(hours_back=1, limit=10)
        self.assertEqual(len(env_data), 1)
        
        data = env_data[0]
        self.assertEqual(data['temperature'], 23.5)
        self.assertEqual(data['humidity'], 45.2)
        self.assertEqual(data['air_quality'], 85)
        self.assertEqual(data['earthquake_detected'], 0)  # SQLite stores as int
    
    def test_log_system_event(self):
        """Test logging system events."""
        # Log system event
        event_id = self.db.log_system_event(
            event_type="startup",
            message="System started successfully",
            severity="INFO",
            details={"version": "1.0.0"}
        )
        
        self.assertGreater(event_id, 0)
        
        # Retrieve and verify
        events = self.db.get_system_events(hours_back=1, limit=10)
        self.assertEqual(len(events), 1)
        
        event = events[0]
        self.assertEqual(event['event_type'], "startup")
        self.assertEqual(event['severity'], "INFO")
        self.assertEqual(event['details']['version'], "1.0.0")
    
    def test_log_ml_prediction(self):
        """Test logging ML predictions."""
        # Log ML prediction
        prediction_id = self.db.log_ml_prediction(
            prediction_type="brightness_prediction",
            input_features={"hour": 14, "temperature": 22.5},
            prediction_result={"brightness": 80},
            confidence=0.85
        )
        
        self.assertGreater(prediction_id, 0)
    
    def test_log_audio_session(self):
        """Test logging audio sessions."""
        # Log audio session
        session_id = self.db.log_audio_session(
            session_type="ambient_sound",
            content_name="ocean_waves",
            duration=300,
            volume=70,
            user_rating=4
        )
        
        self.assertGreater(session_id, 0)
    
    def test_get_usage_patterns(self):
        """Test usage pattern analysis."""
        # Log some sample interactions
        for i in range(5):
            self.db.log_user_interaction(
                interaction_type="brightness_change",
                brightness=50 + i * 10,
                color_temp=4000
            )
        
        # Get usage patterns
        patterns = self.db.get_usage_patterns(days_back=1)
        
        self.assertIn('hourly_usage', patterns)
        self.assertIn('interaction_types', patterns)
        self.assertIn('averages', patterns)
        self.assertEqual(patterns['total_interactions'], 5)
    
    def test_cleanup_old_data(self):
        """Test old data cleanup."""
        # Log some data
        self.db.log_user_interaction("test", brightness=50)
        
        # Check that data exists
        interactions = self.db.get_user_interactions(hours_back=24, limit=10)
        self.assertEqual(len(interactions), 1)
        
        # Cleanup with 0 days (should remove all data)
        deleted = self.db.cleanup_old_data(keep_days=0)
        self.assertGreater(deleted, 0)
        
        # Check that data is gone
        interactions = self.db.get_user_interactions(hours_back=24, limit=10)
        self.assertEqual(len(interactions), 0)
    
    def test_export_data(self):
        """Test data export functionality."""
        # Log some sample data
        self.db.log_user_interaction("test", brightness=50)
        self.db.log_environmental_data(temperature=22.5, humidity=45.0)
        self.db.log_system_event("test", "Test event")
        
        # Export data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            export_path = f.name
        
        try:
            success = self.db.export_data(export_path, days_back=1)
            self.assertTrue(success)
            
            # Verify export file
            self.assertTrue(os.path.exists(export_path))
            
            with open(export_path, 'r') as f:
                export_data = json.load(f)
            
            self.assertIn('export_timestamp', export_data)
            self.assertIn('user_interactions', export_data)
            self.assertIn('environmental_data', export_data)
            self.assertIn('system_events', export_data)
            
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


if __name__ == '__main__':
    unittest.main()
