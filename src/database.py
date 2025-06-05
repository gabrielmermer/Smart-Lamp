"""
Smart Lamp Database Controller
Handles SQLite database operations for user interactions, sensor data, and system events
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """SQLite database manager for Smart Lamp"""
    
    def __init__(self):
        self.db_path = settings.settings.DATABASE_PATH
        self._ensure_database_directory()
        self._initialize_database()
        logger.info(f"Database initialized: {self.db_path}")
    
    def _ensure_database_directory(self):
        """Create database directory if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # User interactions table for ML training
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        action TEXT NOT NULL,
                        value TEXT,
                        hour INTEGER,
                        day_of_week INTEGER,
                        minute INTEGER,
                        is_weekend INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Environmental data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS environmental_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        value REAL,
                        metadata TEXT,
                        location TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        description TEXT,
                        severity TEXT DEFAULT 'info',
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Lamp state history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lamp_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        is_on INTEGER NOT NULL,
                        brightness INTEGER,
                        color_r INTEGER,
                        color_g INTEGER,
                        color_b INTEGER,
                        mode TEXT,
                        trigger_type TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON user_interactions(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_action ON user_interactions(action)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_env_data_type ON environmental_data(data_type, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lamp_states_timestamp ON lamp_states(timestamp)")
                
                conn.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    # =============================================================================
    # USER INTERACTIONS (for ML training)
    # =============================================================================
    
    def log_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Log user interaction for ML training"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_interactions 
                    (timestamp, action, value, hour, day_of_week, minute, is_weekend)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    interaction_data["timestamp"],
                    interaction_data["action"],
                    json.dumps(interaction_data.get("value", {})),
                    interaction_data["hour"],
                    interaction_data["day_of_week"],
                    interaction_data["minute"],
                    1 if interaction_data["is_weekend"] else 0
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            return False
    
    def get_interactions(self, days: int = 30, action_type: str = None) -> List[Dict]:
        """Get user interactions for ML training"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate date threshold
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                if action_type:
                    cursor.execute("""
                        SELECT * FROM user_interactions 
                        WHERE timestamp > ? AND action = ?
                        ORDER BY timestamp DESC
                    """, (cutoff_date, action_type))
                else:
                    cursor.execute("""
                        SELECT * FROM user_interactions 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                    """, (cutoff_date,))
                
                rows = cursor.fetchall()
                
                interactions = []
                for row in rows:
                    interaction = {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "action": row["action"],
                        "value": json.loads(row["value"]) if row["value"] else {},
                        "hour": row["hour"],
                        "day_of_week": row["day_of_week"],
                        "minute": row["minute"],
                        "is_weekend": bool(row["is_weekend"])
                    }
                    interactions.append(interaction)
                
                return interactions
                
        except Exception as e:
            logger.error(f"Error getting interactions: {e}")
            return []
    
    def get_interaction_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get interaction statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total interactions
                cursor.execute("""
                    SELECT COUNT(*) as total FROM user_interactions 
                    WHERE timestamp > ?
                """, (cutoff_date,))
                total = cursor.fetchone()["total"]
                
                # Actions breakdown
                cursor.execute("""
                    SELECT action, COUNT(*) as count FROM user_interactions 
                    WHERE timestamp > ?
                    GROUP BY action
                    ORDER BY count DESC
                """, (cutoff_date,))
                actions = {row["action"]: row["count"] for row in cursor.fetchall()}
                
                # Hourly distribution
                cursor.execute("""
                    SELECT hour, COUNT(*) as count FROM user_interactions 
                    WHERE timestamp > ?
                    GROUP BY hour
                    ORDER BY hour
                """, (cutoff_date,))
                hourly = {row["hour"]: row["count"] for row in cursor.fetchall()}
                
                return {
                    "total_interactions": total,
                    "actions_breakdown": actions,
                    "hourly_distribution": hourly,
                    "days_analyzed": days
                }
                
        except Exception as e:
            logger.error(f"Error getting interaction stats: {e}")
            return {}
    
    def cleanup_old_interactions(self, keep_days: int = None) -> int:
        """Clean up old interaction data"""
        if keep_days is None:
            keep_days = settings.settings.PATTERN_ANALYSIS_DAYS * 2  # Keep double the analysis period
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=keep_days)).isoformat()
                
                cursor.execute("""
                    DELETE FROM user_interactions 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old interactions")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up interactions: {e}")
            return 0
    
    # =============================================================================
    # ENVIRONMENTAL DATA
    # =============================================================================
    
    def log_environmental_data(self, data_type: str, value: float, metadata: Dict = None, location: str = None) -> bool:
        """Log environmental sensor data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO environmental_data 
                    (timestamp, data_type, value, metadata, location)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    data_type,
                    value,
                    json.dumps(metadata) if metadata else None,
                    location or settings.settings.LOCATION_NAME
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging environmental data: {e}")
            return False
    
    def get_environmental_data(self, data_type: str = None, hours: int = 24) -> List[Dict]:
        """Get environmental data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                if data_type:
                    cursor.execute("""
                        SELECT * FROM environmental_data 
                        WHERE data_type = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                    """, (data_type, cutoff_time))
                else:
                    cursor.execute("""
                        SELECT * FROM environmental_data 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                    """, (cutoff_time,))
                
                rows = cursor.fetchall()
                
                data = []
                for row in rows:
                    entry = {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "data_type": row["data_type"],
                        "value": row["value"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "location": row["location"]
                    }
                    data.append(entry)
                
                return data
                
        except Exception as e:
            logger.error(f"Error getting environmental data: {e}")
            return []
    
    # =============================================================================
    # SYSTEM EVENTS
    # =============================================================================
    
    def log_system_event(self, event_type: str, description: str, severity: str = "info", metadata: Dict = None) -> bool:
        """Log system event"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_events 
                    (timestamp, event_type, description, severity, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    event_type,
                    description,
                    severity,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    def get_system_events(self, event_type: str = None, hours: int = 24, severity: str = None) -> List[Dict]:
        """Get system events"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                # Build query based on filters
                query = "SELECT * FROM system_events WHERE timestamp > ?"
                params = [cutoff_time]
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                if severity:
                    query += " AND severity = ?"
                    params.append(severity)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "event_type": row["event_type"],
                        "description": row["description"],
                        "severity": row["severity"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                    }
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Error getting system events: {e}")
            return []
    
    # =============================================================================
    # LAMP STATE HISTORY
    # =============================================================================
    
    def log_lamp_state(self, is_on: bool, brightness: int = None, color: Dict = None, 
                      mode: str = None, trigger_type: str = "manual") -> bool:
        """Log lamp state change"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO lamp_states 
                    (timestamp, is_on, brightness, color_r, color_g, color_b, mode, trigger_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    1 if is_on else 0,
                    brightness,
                    color.get("r") if color else None,
                    color.get("g") if color else None,
                    color.get("b") if color else None,
                    mode,
                    trigger_type
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging lamp state: {e}")
            return False
    
    def get_lamp_history(self, hours: int = 24) -> List[Dict]:
        """Get lamp state history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                cursor.execute("""
                    SELECT * FROM lamp_states 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    state = {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "is_on": bool(row["is_on"]),
                        "brightness": row["brightness"],
                        "color": {
                            "r": row["color_r"],
                            "g": row["color_g"],
                            "b": row["color_b"]
                        } if row["color_r"] is not None else None,
                        "mode": row["mode"],
                        "trigger_type": row["trigger_type"]
                    }
                    history.append(state)
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting lamp history: {e}")
            return []
    
    def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get lamp usage statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total on time calculation (approximate)
                cursor.execute("""
                    SELECT COUNT(*) as on_count FROM lamp_states 
                    WHERE is_on = 1 AND timestamp > ?
                """, (cutoff_time,))
                on_count = cursor.fetchone()["on_count"]
                
                # Mode distribution
                cursor.execute("""
                    SELECT mode, COUNT(*) as count FROM lamp_states 
                    WHERE timestamp > ? AND mode IS NOT NULL
                    GROUP BY mode
                """, (cutoff_time,))
                modes = {row["mode"]: row["count"] for row in cursor.fetchall()}
                
                # Trigger type distribution
                cursor.execute("""
                    SELECT trigger_type, COUNT(*) as count FROM lamp_states 
                    WHERE timestamp > ?
                    GROUP BY trigger_type
                """, (cutoff_time,))
                triggers = {row["trigger_type"]: row["count"] for row in cursor.fetchall()}
                
                return {
                    "on_state_count": on_count,
                    "mode_distribution": modes,
                    "trigger_distribution": triggers,
                    "days_analyzed": days
                }
                
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}
    
    # =============================================================================
    # DATABASE MAINTENANCE
    # =============================================================================
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                tables = ["user_interactions", "environmental_data", "system_events", "lamp_states"]
                table_info = {}
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()["count"]
                    table_info[table] = count
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    "database_path": self.db_path,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "table_counts": table_info,
                    "total_records": sum(table_info.values())
                }
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
    def vacuum_database(self) -> bool:
        """Optimize database by running VACUUM"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                conn.commit()
                
            logger.info("Database vacuumed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error vacuuming database: {e}")
            return False
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create database backup"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.db_path}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False


# Create global database manager instance
db_manager = DatabaseManager()