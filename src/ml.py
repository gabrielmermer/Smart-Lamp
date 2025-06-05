"""
Smart Lamp Machine Learning Controller
Handles user pattern recognition and behavior prediction using SVM
"""

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

from src.config import settings
from src.database import db_manager
from src.utils import get_logger

logger = get_logger(__name__)


class MLController:
    """Machine Learning controller for user pattern recognition"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.last_training = None
        self.model_accuracy = 0.0
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(settings.settings.ML_MODEL_PATH), exist_ok=True)
        
        # Load existing model if available
        self._load_model()
        
        logger.info("ML Controller initialized")
    
    # =============================================================================
    # DATA COLLECTION
    # =============================================================================
    
    def log_user_interaction(self, action: str, value: Dict = None, timestamp: datetime = None):
        """Log user interaction for pattern learning"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Extract time features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            minute = timestamp.minute
            
            interaction_data = {
                "timestamp": timestamp.isoformat(),
                "action": action,
                "value": value or {},
                "hour": hour,
                "day_of_week": day_of_week,
                "minute": minute,
                "is_weekend": day_of_week >= 5
            }
            
            # Store in database
            db_manager.log_interaction(interaction_data)
            
            logger.info(f"Logged interaction: {action} at {timestamp}")
            
            # Check if we should retrain the model
            self._check_retrain_schedule()
            
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
    
    def log_lamp_state_change(self, is_on: bool, brightness: int = None, color: Dict = None):
        """Log lamp state changes"""
        action = "turn_on" if is_on else "turn_off"
        value = {
            "brightness": brightness,
            "color": color,
            "is_on": is_on
        }
        self.log_user_interaction(action, value)
    
    def log_color_change(self, color: Dict[str, int]):
        """Log color changes"""
        self.log_user_interaction("color_change", {"color": color})
    
    def log_brightness_change(self, brightness: int):
        """Log brightness changes"""
        self.log_user_interaction("brightness_change", {"brightness": brightness})
    
    # =============================================================================
    # FEATURE ENGINEERING
    # =============================================================================
    
    def _extract_features(self, interactions: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features from interaction data for ML training"""
        features = []
        labels = []
        
        for interaction in interactions:
            # Time-based features
            hour = interaction.get("hour", 0)
            day_of_week = interaction.get("day_of_week", 0)
            minute = interaction.get("minute", 0)
            is_weekend = interaction.get("is_weekend", False)
            
            # Create feature vector
            feature_vector = [
                hour,                    # Hour of day (0-23)
                day_of_week,            # Day of week (0-6)
                minute / 60.0,          # Minute as fraction of hour (0-1)
                1 if is_weekend else 0, # Weekend flag
                np.sin(2 * np.pi * hour / 24),     # Cyclical hour
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * day_of_week / 7), # Cyclical day
                np.cos(2 * np.pi * day_of_week / 7)
            ]
            
            features.append(feature_vector)
            
            # Create label based on action
            action = interaction.get("action", "")
            if action == "turn_on":
                labels.append(1)  # Turn on
            elif action == "turn_off":
                labels.append(0)  # Turn off
            else:
                continue  # Skip other actions for now
        
        return np.array(features), np.array(labels)
    
    def _extract_color_features(self, interactions: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features for color prediction"""
        features = []
        color_labels = []
        
        for interaction in interactions:
            if interaction.get("action") != "color_change":
                continue
            
            hour = interaction.get("hour", 0)
            day_of_week = interaction.get("day_of_week", 0)
            is_weekend = interaction.get("is_weekend", False)
            
            # Time-based features for color prediction
            feature_vector = [
                hour,
                day_of_week,
                1 if is_weekend else 0,
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24)
            ]
            
            # Extract color (convert RGB to HSV-like features)
            color = interaction.get("value", {}).get("color", {})
            if color:
                r, g, b = color.get("r", 0), color.get("g", 0), color.get("b", 0)
                
                # Simple color categorization
                color_category = self._categorize_color(r, g, b)
                
                features.append(feature_vector)
                color_labels.append(color_category)
        
        return np.array(features), np.array(color_labels)
    
    def _categorize_color(self, r: int, g: int, b: int) -> int:
        """Categorize RGB color into simple categories"""
        # Normalize RGB values
        total = r + g + b
        if total == 0:
            return 0  # Black/off
        
        r_norm, g_norm, b_norm = r/total, g/total, b/total
        
        # Simple color categorization
        if r_norm > 0.6:
            return 1  # Red-ish
        elif g_norm > 0.6:
            return 2  # Green-ish
        elif b_norm > 0.6:
            return 3  # Blue-ish
        elif r_norm > 0.4 and g_norm > 0.4:
            return 4  # Yellow-ish
        elif r_norm > 0.4 and b_norm > 0.4:
            return 5  # Purple-ish
        elif g_norm > 0.4 and b_norm > 0.4:
            return 6  # Cyan-ish
        else:
            return 7  # White-ish
    
    # =============================================================================
    # MODEL TRAINING
    # =============================================================================
    
    def train_model(self, force_retrain: bool = False) -> bool:
        """Train the SVM model with collected data"""
        try:
            # Get interaction data from database
            interactions = db_manager.get_interactions(
                days=settings.settings.PATTERN_ANALYSIS_DAYS
            )
            
            if len(interactions) < settings.settings.ML_MIN_DATA_POINTS:
                logger.warning(f"Not enough data for training: {len(interactions)} < {settings.settings.ML_MIN_DATA_POINTS}")
                return False
            
            # Skip training if recently trained and not forced
            if (not force_retrain and 
                self.last_training and 
                (datetime.now() - self.last_training).total_seconds() < settings.settings.ML_RETRAIN_INTERVAL_HOURS * 3600):
                logger.info("Model recently trained, skipping")
                return False
            
            logger.info(f"Training model with {len(interactions)} interactions")
            
            # Extract features for on/off prediction
            X, y = self._extract_features(interactions)
            
            if len(X) == 0 or len(set(y)) < 2:
                logger.warning("Insufficient data variety for training")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train SVM model
            self.model = SVC(
                kernel='rbf',
                probability=True,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            self.model_accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Model trained with accuracy: {self.model_accuracy:.3f}")
            logger.info(f"Classification report:\n{classification_report(y_test, y_pred)}")
            
            # Save model
            self._save_model()
            
            self.is_trained = True
            self.last_training = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            return False
    
    # =============================================================================
    # PREDICTION
    # =============================================================================
    
    def predict_lamp_state(self, timestamp: datetime = None) -> Dict:
        """Predict if lamp should be on/off at given time"""
        if not self.is_trained or not self.model or not self.scaler:
            return {"should_be_on": False, "confidence": 0.0, "reason": "Model not trained"}
        
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # Extract features for current time
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            minute = timestamp.minute
            is_weekend = day_of_week >= 5
            
            features = np.array([[
                hour,
                day_of_week,
                minute / 60.0,
                1 if is_weekend else 0,
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * day_of_week / 7),
                np.cos(2 * np.pi * day_of_week / 7)
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            result = {
                "should_be_on": bool(prediction),
                "confidence": confidence,
                "timestamp": timestamp.isoformat(),
                "probabilities": {
                    "off": probabilities[0],
                    "on": probabilities[1]
                }
            }
            
            # Only act if confidence is above threshold
            if confidence < settings.settings.ML_PREDICTION_CONFIDENCE_THRESHOLD:
                result["reason"] = f"Low confidence: {confidence:.3f} < {settings.settings.ML_PREDICTION_CONFIDENCE_THRESHOLD}"
                result["should_be_on"] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"should_be_on": False, "confidence": 0.0, "reason": f"Error: {e}"}
    
    def predict_preferred_color(self, timestamp: datetime = None) -> Dict:
        """Predict preferred color for given time"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Simple time-based color prediction (can be enhanced with ML later)
        hour = timestamp.hour
        
        if 6 <= hour < 9:      # Morning
            color = {"r": 255, "g": 230, "b": 180}  # Warm white
            mood = "energizing"
        elif 9 <= hour < 17:   # Day
            color = {"r": 255, "g": 255, "b": 255}  # Bright white
            mood = "productive"
        elif 17 <= hour < 20:  # Evening
            color = {"r": 255, "g": 200, "b": 150}  # Warm orange
            mood = "relaxing"
        elif 20 <= hour < 23:  # Night
            color = {"r": 255, "g": 150, "b": 100}  # Warm red
            mood = "cozy"
        else:                  # Late night
            color = {"r": 100, "g": 50, "b": 50}    # Dim red
            mood = "sleepy"
        
        return {
            "color": color,
            "mood": mood,
            "timestamp": timestamp.isoformat(),
            "confidence": 0.8  # Static confidence for rule-based approach
        }
    
    # =============================================================================
    # MODEL PERSISTENCE
    # =============================================================================
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "accuracy": self.model_accuracy,
                "training_time": datetime.now(),
                "settings.settings": {
                    "min_data_points": settings.settings.ML_MIN_DATA_POINTS,
                    "confidence_threshold": settings.settings.ML_PREDICTION_CONFIDENCE_THRESHOLD
                }
            }
            
            joblib.dump(model_data, settings.settings.ML_MODEL_PATH)
            logger.info(f"Model saved to {settings.settings.ML_MODEL_PATH}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            if not os.path.exists(settings.settings.ML_MODEL_PATH):
                logger.info("No existing model found")
                return
            
            model_data = joblib.load(settings.settings.ML_MODEL_PATH)
            
            self.model = model_data.get("model")
            self.scaler = model_data.get("scaler")
            self.model_accuracy = model_data.get("accuracy", 0.0)
            self.last_training = model_data.get("training_time")
            
            if self.model and self.scaler:
                self.is_trained = True
                logger.info(f"Model loaded with accuracy: {self.model_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_trained = False
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _check_retrain_schedule(self):
        """Check if model should be retrained"""
        if not self.last_training:
            return
        
        hours_since_training = (datetime.now() - self.last_training).total_seconds() / 3600
        
        if hours_since_training >= settings.settings.ML_RETRAIN_INTERVAL_HOURS:
            logger.info("Scheduled model retraining")
            self.train_model(force_retrain=True)
    
    def get_model_stats(self) -> Dict:
        """Get model statistics and information"""
        try:
            interaction_count = len(db_manager.get_interactions(days=30))
            recent_interactions = len(db_manager.get_interactions(days=1))
            
            return {
                "is_trained": self.is_trained,
                "model_accuracy": self.model_accuracy,
                "last_training": self.last_training.isoformat() if self.last_training else None,
                "total_interactions": interaction_count,
                "recent_interactions": recent_interactions,
                "model_path": settings.settings.ML_MODEL_PATH,
                "min_data_points": settings.settings.ML_MIN_DATA_POINTS,
                "confidence_threshold": settings.settings.ML_PREDICTION_CONFIDENCE_THRESHOLD,
                "retrain_interval_hours": settings.settings.ML_RETRAIN_INTERVAL_HOURS
            }
            
        except Exception as e:
            logger.error(f"Error getting model stats: {e}")
            return {"error": str(e)}
    
    def reset_model(self):
        """Reset and delete the trained model"""
        try:
            self.model = None
            self.scaler = None
            self.is_trained = False
            self.last_training = None
            self.model_accuracy = 0.0
            
            if os.path.exists(settings.settings.ML_MODEL_PATH):
                os.remove(settings.settings.ML_MODEL_PATH)
            
            logger.info("Model reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting model: {e}")
    
    def get_predictions_for_day(self, date: datetime = None) -> List[Dict]:
        """Get hourly predictions for a full day"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        predictions = []
        for hour in range(24):
            timestamp = date.replace(hour=hour)
            prediction = self.predict_lamp_state(timestamp)
            color_prediction = self.predict_preferred_color(timestamp)
            
            predictions.append({
                "hour": hour,
                "timestamp": timestamp.isoformat(),
                "lamp_state": prediction,
                "color": color_prediction
            })
        
        return predictions


# Create global ML controller instance
ml_controller = MLController()