"""
Database Manager for Smart Lamp

Simple SQLite database for storing:
- User interactions (ON/OFF, color changes)
- Environmental data (weather, air quality, earthquakes)
- System logs

Independent module - lightweight and easy to use.
"""

import sqlite3
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from config import settings

class DatabaseManager:
    """Simple database manager for Smart Lamp"""
    
    def __init__(self, db_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or settings.DATABASE_PATH
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._create_tables()
        self.logger.info(f"Database initialized: {self.db_path}")
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _create_tables(self):
        """Create database tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # User interactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        action TEXT NOT NULL,
                        color_r INTEGER,
                        color_g INTEGER,
                        color_b INTEGER,
                        brightness INTEGER,
                        hour INTEGER,
                        day_of_week INTEGER
                    )
                ''')
                
                # Environmental data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS environmental_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        data_type TEXT NOT NULL,
                        value REAL,
                        details TEXT
                    )
                ''')
                
                # System logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        level TEXT,
                        message TEXT
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
    
    def log_user_action(self, action: str, color: Tuple[int, int, int] = None, brightness: int = None):
        """Log user interaction"""
        try:
            now = datetime.now()
            r, g, b = color if color else (None, None, None)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions 
                    (action, color_r, color_g, color_b, brightness, hour, day_of_week)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (action, r, g, b, brightness, now.hour, now.weekday()))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log user action: {e}")
    
    def log_environmental_data(self, data_type: str, value: float, details: Dict = None):
        """Log environmental sensor data"""
        try:
            details_json = json.dumps(details) if details else None
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO environmental_data (data_type, value, details)
                    VALUES (?, ?, ?)
                ''', (data_type, value, details_json))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log environmental data: {e}")
    
    def get_user_patterns(self, days: int = 7) -> List[Dict]:
        """Get user interaction patterns for ML training"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT action, color_r, color_g, color_b, brightness, hour, day_of_week, timestamp
                    FROM user_interactions
                    WHERE timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp
                '''.format(days))
                
                rows = cursor.fetchall()
                
                patterns = []
                for row in rows:
                    patterns.append({
                        'action': row[0],
                        'color': (row[1], row[2], row[3]) if row[1] is not None else None,
                        'brightness': row[4],
                        'hour': row[5],
                        'day_of_week': row[6],
                        'timestamp': row[7]
                    })
                
                return patterns
                
        except Exception as e:
            self.logger.error(f"Failed to get user patterns: {e}")
            return []
    
    def get_environmental_data(self, data_type: str = None, hours: int = 24) -> List[Dict]:
        """Get recent environmental data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if data_type:
                    cursor.execute('''
                        SELECT data_type, value, details, timestamp
                        FROM environmental_data
                        WHERE data_type = ? AND timestamp >= datetime('now', '-{} hours')
                        ORDER BY timestamp DESC
                    '''.format(hours), (data_type,))
                else:
                    cursor.execute('''
                        SELECT data_type, value, details, timestamp
                        FROM environmental_data
                        WHERE timestamp >= datetime('now', '-{} hours')
                        ORDER BY timestamp DESC
                    '''.format(hours))
                
                rows = cursor.fetchall()
                
                data = []
                for row in rows:
                    details = json.loads(row[2]) if row[2] else {}
                    data.append({
                        'type': row[0],
                        'value': row[1],
                        'details': details,
                        'timestamp': row[3]
                    })
                
                return data
                
        except Exception as e:
            self.logger.error(f"Failed to get environmental data: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                cursor.execute('SELECT COUNT(*) FROM user_interactions')
                user_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM environmental_data')
                env_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM system_logs')
                log_count = cursor.fetchone()[0]
                
                return {
                    'user_interactions': user_count,
                    'environmental_data': env_count,
                    'system_logs': log_count,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Remove old data to keep database size manageable"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Keep only recent data
                cursor.execute('''
                    DELETE FROM user_interactions 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                cursor.execute('''
                    DELETE FROM environmental_data 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                cursor.execute('''
                    DELETE FROM system_logs 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                # Vacuum to reclaim space
                cursor.execute('VACUUM')
                conn.commit()
                
                self.logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test database
    db = DatabaseManager("test_lamp.db")
    
    print("Testing database...")
    
    # Test logging user actions
    db.log_user_action("TURN_ON", (255, 0, 0), 80)
    db.log_user_action("COLOR_CHANGE", (0, 255, 0), 75)
    db.log_user_action("TURN_OFF")
    
    # Test logging environmental data
    db.log_environmental_data("temperature", 22.5, {"location": "room"})
    db.log_environmental_data("air_quality", 85, {"aqi_level": 2})
    
    # Get patterns
    patterns = db.get_user_patterns(1)
    print(f"User patterns: {len(patterns)} records")
    
    # Get environmental data
    env_data = db.get_environmental_data()
    print(f"Environmental data: {len(env_data)} records")
    
    # Get stats
    stats = db.get_stats()
    print(f"Database stats: {stats}")
    
    print("Database test completed!")