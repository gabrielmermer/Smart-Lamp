"""
Machine Learning module for Smart Lamp.
Handles usage pattern recognition and automated behavior prediction.
Team member: Shohruh (Usage pattern recognition)
"""

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import threading
import time

from .config import settings


@dataclass
class UserAction:
    """Represents a user action with the lamp."""
    timestamp: datetime
    action_type: str  # 'on', 'off', 'color_change', 'brightness_change'
    brightness: int
    color_r: int
    color_g: int
    color_b: int
    hour: int
    day_of_week: int  # 0=Monday, 6=Sunday
    is_weekend: bool
    previous_state: bool  # Was lamp on before this action


@dataclass
class PredictionResult:
    """Result of a prediction."""
    should_be_on: bool
    predicted_brightness: int
    predicted_color: Tuple[int, int, int]
    confidence: float
    reasoning: str


class DataLogger:
    """Logs user interactions for machine learning."""
    
    def __init__(self):
        self.log_file = settings.system.data_log_path
        self.actions: List[UserAction] = []
        self._ensure_log_directory()
        self.load_existing_data()
    
    def _ensure_log_directory(self):
        """Ensure the data log directory exists."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log_action(self, action_type: str, brightness: int, color_r: int, color_g: int, color_b: int, previous_state: bool):
        """Log a user action."""
        now = datetime.now()
        action = UserAction(
            timestamp=now,
            action_type=action_type,
            brightness=brightness,
            color_r=color_r,
            color_g=color_g,
            color_b=color_b,
            hour=now.hour,
            day_of_week=now.weekday(),
            is_weekend=now.weekday() >= 5,
            previous_state=previous_state
        )
        
        self.actions.append(action)
        self.save_to_file()
        print(f"Logged action: {action_type} at {now.strftime('%H:%M')}")
    
    def save_to_file(self):
        """Save actions to JSON file."""
        try:
            # Convert actions to dictionaries for JSON serialization
            actions_data = []
            for action in self.actions:
                action_dict = asdict(action)
                action_dict['timestamp'] = action.timestamp.isoformat()
                actions_data.append(action_dict)
            
            with open(self.log_file, 'w') as f:
                json.dump(actions_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving log data: {e}")
    
    def load_existing_data(self):
        """Load existing actions from file."""
        if not os.path.exists(self.log_file):
            return
        
        try:
            with open(self.log_file, 'r') as f:
                actions_data = json.load(f)
            
            self.actions = []
            for action_dict in actions_data:
                action_dict['timestamp'] = datetime.fromisoformat(action_dict['timestamp'])
                self.actions.append(UserAction(**action_dict))
            
            print(f"Loaded {len(self.actions)} existing actions")
            
        except Exception as e:
            print(f"Error loading existing data: {e}")
            self.actions = []
    
    def get_recent_actions(self, hours: int = 24) -> List[UserAction]:
        """Get actions from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [action for action in self.actions if action.timestamp >= cutoff]
    
    def get_actions_by_time_period(self, start_hour: int, end_hour: int) -> List[UserAction]:
        """Get actions within a specific time period."""
        return [action for action in self.actions if start_hour <= action.hour <= end_hour]
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of logged data."""
        if not self.actions:
            return {'total_actions': 0}
        
        df = self.to_dataframe()
        return {
            'total_actions': len(self.actions),
            'date_range': {
                'start': min(action.timestamp for action in self.actions).strftime('%Y-%m-%d'),
                'end': max(action.timestamp for action in self.actions).strftime('%Y-%m-%d')
            },
            'action_types': df['action_type'].value_counts().to_dict(),
            'most_active_hours': df['hour'].value_counts().head(3).to_dict(),
            'weekend_vs_weekday': df['is_weekend'].value_counts().to_dict()
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert actions to pandas DataFrame."""
        if not self.actions:
            return pd.DataFrame()
        
        data = []
        for action in self.actions:
            data.append(asdict(action))
        
        return pd.DataFrame(data)


class PatternAnalyzer:
    """Analyzes user behavior patterns."""
    
    def __init__(self, data_logger: DataLogger):
        self.data_logger = data_logger
        self.model_path = settings.system.model_save_path
        self.models = {}
        self.scalers = {}
        self._ensure_model_directory()
    
    def _ensure_model_directory(self):
        """Ensure the model directory exists."""
        os.makedirs(self.model_path, exist_ok=True)
    
    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for training."""
        return len(self.data_logger.actions) >= settings.system.ml_min_data_points
    
    def prepare_features(self, actions: List[UserAction]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare features for machine learning."""
        if not actions:
            return np.array([]), np.array([]), np.array([])
        
        features = []
        on_off_labels = []
        color_labels = []
        
        for action in actions:
            # Feature vector: [hour, day_of_week, is_weekend, previous_state]
            feature_vector = [
                action.hour,
                action.day_of_week,
                int(action.is_weekend),
                int(action.previous_state),
                action.brightness
            ]
            features.append(feature_vector)
            
            # Labels
            on_off_labels.append(1 if action.action_type in ['on', 'color_change', 'brightness_change'] else 0)
            color_labels.append([action.color_r, action.color_g, action.color_b])
        
        return np.array(features), np.array(on_off_labels), np.array(color_labels)
    
    def train_on_off_model(self) -> bool:
        """Train model to predict when lamp should be on/off."""
        if not self.has_sufficient_data():
            print("Insufficient data for training ON/OFF model")
            return False
        
        try:
            features, labels, _ = self.prepare_features(self.data_logger.actions)
            
            if len(np.unique(labels)) < 2:
                print("Need both ON and OFF examples for training")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"ON/OFF Model trained with accuracy: {accuracy:.2f}")
            
            # Save model and scaler
            self.models['on_off'] = model
            self.scalers['on_off'] = scaler
            self._save_model('on_off', model, scaler)
            
            return True
            
        except Exception as e:
            print(f"Error training ON/OFF model: {e}")
            return False
    
    def train_color_model(self) -> bool:
        """Train model to predict preferred colors."""
        if not self.has_sufficient_data():
            print("Insufficient data for training color model")
            return False
        
        try:
            # Get only actions that involve color changes
            color_actions = [a for a in self.data_logger.actions if a.action_type in ['on', 'color_change']]
            
            if len(color_actions) < 10:
                print("Insufficient color data for training")
                return False
            
            features, _, color_labels = self.prepare_features(color_actions)
            
            # Use clustering to find color preferences
            kmeans = KMeans(n_clusters=min(5, len(color_actions) // 3), random_state=42)
            color_clusters = kmeans.fit_predict(color_labels)
            
            # Create features with time context for color prediction
            time_features = []
            cluster_labels = []
            
            for i, action in enumerate(color_actions):
                time_feature = [action.hour, int(action.is_weekend)]
                time_features.append(time_feature)
                cluster_labels.append(color_clusters[i])
            
            # Train classifier to predict color cluster based on time
            time_features = np.array(time_features)
            scaler = StandardScaler()
            time_features_scaled = scaler.fit_transform(time_features)
            
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(time_features_scaled, cluster_labels)
            
            print("Color preference model trained")
            
            # Save models
            self.models['color'] = model
            self.models['color_clusters'] = kmeans
            self.scalers['color'] = scaler
            self._save_model('color', model, scaler, kmeans)
            
            return True
            
        except Exception as e:
            print(f"Error training color model: {e}")
            return False
    
    def _save_model(self, model_name: str, model, scaler, clustering_model=None):
        """Save trained model and scaler."""
        try:
            model_file = os.path.join(self.model_path, f'{model_name}_model.joblib')
            scaler_file = os.path.join(self.model_path, f'{model_name}_scaler.joblib')
            
            joblib.dump(model, model_file)
            joblib.dump(scaler, scaler_file)
            
            if clustering_model:
                cluster_file = os.path.join(self.model_path, f'{model_name}_clusters.joblib')
                joblib.dump(clustering_model, cluster_file)
            
            print(f"Saved {model_name} model")
            
        except Exception as e:
            print(f"Error saving {model_name} model: {e}")
    
    def load_models(self):
        """Load saved models."""
        try:
            # Load ON/OFF model
            on_off_model_file = os.path.join(self.model_path, 'on_off_model.joblib')
            on_off_scaler_file = os.path.join(self.model_path, 'on_off_scaler.joblib')
            
            if os.path.exists(on_off_model_file) and os.path.exists(on_off_scaler_file):
                self.models['on_off'] = joblib.load(on_off_model_file)
                self.scalers['on_off'] = joblib.load(on_off_scaler_file)
                print("Loaded ON/OFF model")
            
            # Load color model
            color_model_file = os.path.join(self.model_path, 'color_model.joblib')
            color_scaler_file = os.path.join(self.model_path, 'color_scaler.joblib')
            color_cluster_file = os.path.join(self.model_path, 'color_clusters.joblib')
            
            if all(os.path.exists(f) for f in [color_model_file, color_scaler_file, color_cluster_file]):
                self.models['color'] = joblib.load(color_model_file)
                self.scalers['color'] = joblib.load(color_scaler_file)
                self.models['color_clusters'] = joblib.load(color_cluster_file)
                print("Loaded color model")
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def predict_lamp_state(self, current_time: Optional[datetime] = None) -> PredictionResult:
        """Predict what the lamp state should be."""
        if current_time is None:
            current_time = datetime.now()
        
        # Default prediction
        default_result = PredictionResult(
            should_be_on=False,
            predicted_brightness=settings.system.default_brightness,
            predicted_color=(
                settings.system.default_color_r,
                settings.system.default_color_g,
                settings.system.default_color_b
            ),
            confidence=0.0,
            reasoning="No trained model available"
        )
        
        try:
            # Predict ON/OFF state
            should_be_on = False
            on_off_confidence = 0.0
            
            if 'on_off' in self.models:
                feature_vector = np.array([[
                    current_time.hour,
                    current_time.weekday(),
                    int(current_time.weekday() >= 5),  # is_weekend
                    0,  # previous_state (we'll update this)
                    settings.system.default_brightness
                ]])
                
                feature_vector_scaled = self.scalers['on_off'].transform(feature_vector)
                prediction = self.models['on_off'].predict(feature_vector_scaled)[0]
                prediction_proba = self.models['on_off'].predict_proba(feature_vector_scaled)[0]
                
                should_be_on = bool(prediction)
                on_off_confidence = max(prediction_proba)
            
            # Predict color
            predicted_color = (
                settings.system.default_color_r,
                settings.system.default_color_g,
                settings.system.default_color_b
            )
            color_confidence = 0.0
            
            if 'color' in self.models and 'color_clusters' in self.models:
                time_feature = np.array([[
                    current_time.hour,
                    int(current_time.weekday() >= 5)
                ]])
                
                time_feature_scaled = self.scalers['color'].transform(time_feature)
                cluster_pred = self.models['color'].predict(time_feature_scaled)[0]
                
                # Get the cluster center (representative color)
                cluster_center = self.models['color_clusters'].cluster_centers_[cluster_pred]
                predicted_color = tuple(int(c) for c in cluster_center)
                color_confidence = 0.7  # Simplified confidence
            
            # Overall confidence
            overall_confidence = (on_off_confidence + color_confidence) / 2
            
            # Generate reasoning
            reasoning_parts = []
            if on_off_confidence > settings.system.ml_prediction_confidence_threshold:
                reasoning_parts.append(f"Historical usage at {current_time.hour:02d}:00")
            if color_confidence > 0.5:
                reasoning_parts.append("Color preference pattern")
            
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Default behavior"
            
            return PredictionResult(
                should_be_on=should_be_on,
                predicted_brightness=settings.system.default_brightness,
                predicted_color=predicted_color,
                confidence=overall_confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return default_result
    
    def get_usage_patterns(self) -> Dict:
        """Get analysis of usage patterns."""
        if not self.data_logger.actions:
            return {}
        
        df = self.data_logger.to_dataframe()
        
        patterns = {
            'most_active_hours': df['hour'].value_counts().head(5).to_dict(),
            'weekend_behavior': df.groupby('is_weekend')['action_type'].value_counts().to_dict(),
            'color_preferences': {},
            'average_brightness': df['brightness'].mean(),
            'total_interactions': len(df)
        }
        
        # Analyze color preferences
        color_actions = df[df['action_type'].isin(['on', 'color_change'])]
        if not color_actions.empty:
            patterns['color_preferences'] = {
                'most_used_red': color_actions['color_r'].mode().iloc[0] if not color_actions['color_r'].mode().empty else 255,
                'most_used_green': color_actions['color_g'].mode().iloc[0] if not color_actions['color_g'].mode().empty else 255,
                'most_used_blue': color_actions['color_b'].mode().iloc[0] if not color_actions['color_b'].mode().empty else 255,
                'color_variety': len(color_actions[['color_r', 'color_g', 'color_b']].drop_duplicates())
            }
        
        return patterns


class MLController:
    """Main controller for machine learning functionality."""
    
    def __init__(self, lamp_controller=None):
        self.lamp_controller = lamp_controller
        self.data_logger = DataLogger()
        self.pattern_analyzer = PatternAnalyzer(self.data_logger)
        self.auto_mode_enabled = False
        self.last_prediction_time = None
        self.prediction_thread = None
        self.running = False
        
        # Load existing models
        self.pattern_analyzer.load_models()
    
    def log_user_action(self, action_type: str):
        """Log a user action with current lamp state."""
        if self.lamp_controller:
            state = self.lamp_controller.state
            self.data_logger.log_action(
                action_type=action_type,
                brightness=state.brightness,
                color_r=state.color_r,
                color_g=state.color_g,
                color_b=state.color_b,
                previous_state=state.is_on
            )
    
    def enable_auto_mode(self, enable: bool = True):
        """Enable or disable automatic prediction mode."""
        self.auto_mode_enabled = enable
        
        if enable and not self.running:
            self.start_prediction_loop()
        elif not enable and self.running:
            self.stop_prediction_loop()
        
        print(f"ML auto mode {'enabled' if enable else 'disabled'}")
    
    def start_prediction_loop(self):
        """Start the prediction loop thread."""
        self.running = True
        self.prediction_thread = threading.Thread(target=self._prediction_worker, daemon=True)
        self.prediction_thread.start()
        print("ML prediction loop started")
    
    def stop_prediction_loop(self):
        """Stop the prediction loop thread."""
        self.running = False
        if self.prediction_thread:
            self.prediction_thread.join(timeout=5)
        print("ML prediction loop stopped")
    
    def _prediction_worker(self):
        """Worker thread for making predictions."""
        while self.running and self.auto_mode_enabled:
            try:
                current_time = datetime.now()
                
                # Make prediction every minute
                if (self.last_prediction_time is None or 
                    (current_time - self.last_prediction_time).total_seconds() >= 60):
                    
                    prediction = self.pattern_analyzer.predict_lamp_state(current_time)
                    
                    if (prediction.confidence >= settings.system.ml_prediction_confidence_threshold and
                        self.lamp_controller):
                        
                        self._apply_prediction(prediction)
                    
                    self.last_prediction_time = current_time
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in prediction worker: {e}")
                time.sleep(10)
    
    def _apply_prediction(self, prediction: PredictionResult):
        """Apply prediction to the lamp."""
        if not self.lamp_controller:
            return
        
        current_state = self.lamp_controller.state
        
        # Apply ON/OFF prediction
        if prediction.should_be_on != current_state.is_on:
            if prediction.should_be_on:
                self.lamp_controller.turn_on()
                print(f"ML: Turned lamp ON ({prediction.reasoning})")
            else:
                self.lamp_controller.turn_off()
                print(f"ML: Turned lamp OFF ({prediction.reasoning})")
        
        # Apply color prediction if lamp is on
        if prediction.should_be_on and current_state.is_on:
            current_color = (current_state.color_r, current_state.color_g, current_state.color_b)
            if prediction.predicted_color != current_color:
                self.lamp_controller.set_led_color(*prediction.predicted_color)
                print(f"ML: Changed color to {prediction.predicted_color} ({prediction.reasoning})")
    
    def retrain_models(self) -> bool:
        """Retrain all models with current data."""
        if not self.pattern_analyzer.has_sufficient_data():
            print("Insufficient data for retraining")
            return False
        
        print("Retraining ML models...")
        
        on_off_success = self.pattern_analyzer.train_on_off_model()
        color_success = self.pattern_analyzer.train_color_model()
        
        success = on_off_success or color_success
        if success:
            print("Model retraining completed")
        else:
            print("Model retraining failed")
        
        return success
    
    def get_prediction_for_time(self, target_time: datetime) -> PredictionResult:
        """Get prediction for a specific time."""
        return self.pattern_analyzer.predict_lamp_state(target_time)
    
    def get_ml_status(self) -> Dict:
        """Get current ML system status."""
        return {
            'auto_mode_enabled': self.auto_mode_enabled,
            'data_points': len(self.data_logger.actions),
            'sufficient_data': self.pattern_analyzer.has_sufficient_data(),
            'models_loaded': len(self.pattern_analyzer.models),
            'last_prediction': self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            'data_summary': self.data_logger.get_data_summary(),
            'usage_patterns': self.pattern_analyzer.get_usage_patterns()
        }
    
    def cleanup(self):
        """Clean up ML controller."""
        self.stop_prediction_loop()
        self.data_logger.save_to_file()
        print("ML controller cleaned up")
