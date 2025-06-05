import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import threading
import logging

from .config import settings


class DatabaseManager:
    """Manages SQLite database operations for the Smart Lamp system."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or settings.system.database_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # User interactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        interaction_type TEXT NOT NULL,
                        brightness INTEGER,
                        color_temp INTEGER,
                        rgb_color TEXT,
                        duration INTEGER,
                        context TEXT,
                        environmental_data TEXT
                    )
                ''')
                
                # Environmental data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS environmental_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        temperature REAL,
                        humidity REAL,
                        air_quality INTEGER,
                        noise_level REAL,
                        light_level REAL,
                        weather_condition TEXT,
                        earthquake_detected INTEGER DEFAULT 0
                    )
                ''')
                
                # System events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        severity TEXT DEFAULT 'INFO',
                        message TEXT,
                        details TEXT
                    )
                ''')
                
                # ML predictions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ml_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        prediction_type TEXT NOT NULL,
                        input_features TEXT,
                        prediction_result TEXT,
                        confidence REAL,
                        actual_outcome TEXT
                    )
                ''')
                
                # Audio sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        session_type TEXT NOT NULL,
                        content_name TEXT,
                        duration INTEGER,
                        volume INTEGER,
                        user_rating INTEGER
                    )
                ''')
                
                # Configuration history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        config_key TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        changed_by TEXT DEFAULT 'system'
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON user_interactions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_environmental_timestamp ON environmental_data(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON ml_predictions(timestamp)')
                
                conn.commit()
                conn.close()
                
                self.logger.info("Database initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize database: {e}")
                raise
    
    def log_user_interaction(self, interaction_type: str, brightness: Optional[int] = None,
                           color_temp: Optional[int] = None, rgb_color: Optional[Tuple[int, int, int]] = None,
                           duration: Optional[int] = None, context: Optional[Dict] = None,
                           environmental_data: Optional[Dict] = None) -> int:
        """Log a user interaction."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_interactions 
                    (interaction_type, brightness, color_temp, rgb_color, duration, context, environmental_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction_type,
                    brightness,
                    color_temp,
                    json.dumps(rgb_color) if rgb_color else None,
                    duration,
                    json.dumps(context) if context else None,
                    json.dumps(environmental_data) if environmental_data else None
                ))
                
                interaction_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return interaction_id
                
            except Exception as e:
                self.logger.error(f"Failed to log user interaction: {e}")
                return -1
    
    def log_environmental_data(self, temperature: Optional[float] = None, humidity: Optional[float] = None,
                             air_quality: Optional[int] = None, noise_level: Optional[float] = None,
                             light_level: Optional[float] = None, weather_condition: Optional[str] = None,
                             earthquake_detected: bool = False) -> int:
        """Log environmental sensor data."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO environmental_data 
                    (temperature, humidity, air_quality, noise_level, light_level, weather_condition, earthquake_detected)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    temperature, humidity, air_quality, noise_level, 
                    light_level, weather_condition, 1 if earthquake_detected else 0
                ))
                
                record_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return record_id
                
            except Exception as e:
                self.logger.error(f"Failed to log environmental data: {e}")
                return -1
    
    def log_system_event(self, event_type: str, message: str, severity: str = 'INFO', details: Optional[Dict] = None) -> int:
        """Log a system event."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_events (event_type, severity, message, details)
                    VALUES (?, ?, ?, ?)
                ''', (
                    event_type,
                    severity,
                    message,
                    json.dumps(details) if details else None
                ))
                
                event_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return event_id
                
            except Exception as e:
                self.logger.error(f"Failed to log system event: {e}")
                return -1
    
    def log_ml_prediction(self, prediction_type: str, input_features: Dict, 
                         prediction_result: Any, confidence: float,
                         actual_outcome: Optional[Any] = None) -> int:
        """Log an ML prediction."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ml_predictions 
                    (prediction_type, input_features, prediction_result, confidence, actual_outcome)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    prediction_type,
                    json.dumps(input_features),
                    json.dumps(prediction_result),
                    confidence,
                    json.dumps(actual_outcome) if actual_outcome is not None else None
                ))
                
                prediction_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return prediction_id
                
            except Exception as e:
                self.logger.error(f"Failed to log ML prediction: {e}")
                return -1
    
    def log_audio_session(self, session_type: str, content_name: Optional[str] = None,
                         duration: Optional[int] = None, volume: Optional[int] = None,
                         user_rating: Optional[int] = None) -> int:
        """Log an audio session."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audio_sessions (session_type, content_name, duration, volume, user_rating)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_type, content_name, duration, volume, user_rating))
                
                session_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return session_id
                
            except Exception as e:
                self.logger.error(f"Failed to log audio session: {e}")
                return -1
    
    def get_user_interactions(self, hours_back: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent user interactions."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(hours=hours_back)
                
                cursor.execute('''
                    SELECT * FROM user_interactions 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (since_time, limit))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    # Parse JSON fields
                    if record['rgb_color']:
                        record['rgb_color'] = json.loads(record['rgb_color'])
                    if record['context']:
                        record['context'] = json.loads(record['context'])
                    if record['environmental_data']:
                        record['environmental_data'] = json.loads(record['environmental_data'])
                    results.append(record)
                
                conn.close()
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to get user interactions: {e}")
                return []
    
    def get_environmental_data(self, hours_back: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent environmental data."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(hours=hours_back)
                
                cursor.execute('''
                    SELECT * FROM environmental_data 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (since_time, limit))
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                conn.close()
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to get environmental data: {e}")
                return []
    
    def get_system_events(self, hours_back: int = 24, severity_filter: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent system events."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(hours=hours_back)
                
                if severity_filter:
                    cursor.execute('''
                        SELECT * FROM system_events 
                        WHERE timestamp >= ? AND severity = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (since_time, severity_filter, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM system_events 
                        WHERE timestamp >= ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (since_time, limit))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    if record['details']:
                        record['details'] = json.loads(record['details'])
                    results.append(record)
                
                conn.close()
                return results
                
            except Exception as e:
                self.logger.error(f"Failed to get system events: {e}")
                return []
    
    def get_usage_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze usage patterns from historical data."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(days=days_back)
                
                # Get interaction frequency by hour
                cursor.execute('''
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM user_interactions 
                    WHERE timestamp >= ?
                    GROUP BY hour
                    ORDER BY hour
                ''', (since_time,))
                
                hourly_usage = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Get most common interaction types
                cursor.execute('''
                    SELECT interaction_type, COUNT(*) as count
                    FROM user_interactions 
                    WHERE timestamp >= ?
                    GROUP BY interaction_type
                    ORDER BY count DESC
                ''', (since_time,))
                
                interaction_types = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Get average brightness and color temperature
                cursor.execute('''
                    SELECT AVG(brightness) as avg_brightness, AVG(color_temp) as avg_color_temp
                    FROM user_interactions 
                    WHERE timestamp >= ? AND brightness IS NOT NULL AND color_temp IS NOT NULL
                ''', (since_time,))
                
                avg_result = cursor.fetchone()
                averages = {
                    'brightness': avg_result[0] if avg_result[0] else 0,
                    'color_temp': avg_result[1] if avg_result[1] else 0
                }
                
                conn.close()
                
                return {
                    'hourly_usage': hourly_usage,
                    'interaction_types': interaction_types,
                    'averages': averages,
                    'analysis_period_days': days_back,
                    'total_interactions': sum(interaction_types.values())
                }
                
            except Exception as e:
                self.logger.error(f"Failed to analyze usage patterns: {e}")
                return {}
    
    def cleanup_old_data(self, keep_days: int = 30) -> int:
        """Clean up old data to prevent database from growing too large."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_time = datetime.now() - timedelta(days=keep_days)
                
                # Clean up old records from each table
                tables = ['user_interactions', 'environmental_data', 'system_events', 
                         'ml_predictions', 'audio_sessions']
                
                total_deleted = 0
                for table in tables:
                    cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_time,))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    self.logger.info(f"Deleted {deleted} old records from {table}")
                
                conn.commit()
                conn.close()
                
                return total_deleted
                
            except Exception as e:
                self.logger.error(f"Failed to cleanup old data: {e}")
                return 0
    
    def export_data(self, output_path: str, days_back: int = 30) -> bool:
        """Export data to JSON file."""
        try:
            since_time = datetime.now() - timedelta(days=days_back)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'days_back': days_back,
                'user_interactions': self.get_user_interactions(days_back * 24),
                'environmental_data': self.get_environmental_data(days_back * 24),
                'system_events': self.get_system_events(days_back * 24),
                'usage_patterns': self.get_usage_patterns(days_back)
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Data exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return False


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> DatabaseManager:
    """Get singleton database instance."""
    global _db_instance
    
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = DatabaseManager()
    
    return _db_instance
