"""
Online Learning for Real-time Model Updates
Incremental learning from streaming data and trade outcomes
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Deque
from datetime import datetime, timedelta
from collections import deque
from sklearn.linear_model import SGDClassifier, PassiveAggressiveClassifier
from sklearn.preprocessing import StandardScaler
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class OnlineLearner:
    """
    Online Learning System for Real-time Updates

    Features:
    - Incremental model updates (SGD, Passive-Aggressive)
    - Streaming data processing
    - Concept drift detection
    - Model performance tracking
    - Adaptive learning rate
    - Sample buffer management
    - Forgetting mechanism for old data
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Online Learner"""
        self.config = config or {}

        # Model type
        self.model_type = self.config.get('model_type', 'sgd')  # sgd, passive_aggressive
        self.loss = self.config.get('loss', 'log_loss')  # log_loss, hinge, perceptron
        self.learning_rate = self.config.get('learning_rate', 'optimal')  # constant, optimal, invscaling, adaptive
        self.alpha = self.config.get('alpha', 0.0001)  # Regularization

        # Buffer settings
        self.buffer_size = self.config.get('buffer_size', 1000)
        self.batch_size = self.config.get('batch_size', 32)
        self.min_samples_before_update = self.config.get('min_samples_before_update', 10)

        # Drift detection
        self.drift_threshold = self.config.get('drift_threshold', 0.1)
        self.drift_window_size = self.config.get('drift_window_size', 100)

        # Model
        self.model = None
        self.scaler = StandardScaler()
        self.is_initialized = False

        # Buffers
        self.sample_buffer: Deque = deque(maxlen=self.buffer_size)
        self.performance_buffer: Deque = deque(maxlen=self.drift_window_size)

        # Statistics
        self.n_updates = 0
        self.n_samples_seen = 0
        self.current_accuracy = 0.0
        self.drift_detected = False

        # Model path
        self.model_path = self.config.get('model_path', 'models/online_model.pkl')

    def initialize_model(self, n_features: int) -> None:
        """
        Initialize online learning model

        Args:
            n_features: Number of input features
        """
        if self.model_type == 'sgd':
            self.model = SGDClassifier(
                loss=self.loss,
                learning_rate=self.learning_rate,
                alpha=self.alpha,
                max_iter=1,  # Online learning
                tol=None,
                warm_start=True,  # Keep previous fit
                random_state=42
            )
        elif self.model_type == 'passive_aggressive':
            self.model = PassiveAggressiveClassifier(
                C=1.0,
                max_iter=1,
                tol=None,
                warm_start=True,
                random_state=42
            )
        else:
            logger.warning(f"Unknown model type: {self.model_type}, using SGD")
            self.model = SGDClassifier(warm_start=True, random_state=42)

        # Initialize with dummy data
        X_dummy = np.zeros((1, n_features))
        y_dummy = np.array([0])
        self.scaler.fit(X_dummy)
        self.model.partial_fit(X_dummy, y_dummy, classes=[0, 1])

        self.is_initialized = True
        logger.info(f"Online learner initialized: {self.model_type}, {n_features} features")

    def add_sample(
        self,
        X: np.ndarray,
        y: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a new sample to buffer

        Args:
            X: Feature vector
            y: Target label (0 or 1)
            metadata: Optional metadata (timestamp, etc.)
        """
        sample = {
            'X': X,
            'y': y,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }

        self.sample_buffer.append(sample)
        self.n_samples_seen += 1

        logger.debug(f"Sample added to buffer. Buffer size: {len(self.sample_buffer)}")

    def should_update(self) -> bool:
        """Check if model should be updated"""
        return len(self.sample_buffer) >= self.min_samples_before_update

    def update_model(self, batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Update model with samples from buffer

        Args:
            batch_size: Number of samples to use for update (default: self.batch_size)

        Returns:
            Update results
        """
        if not self.is_initialized:
            logger.error("Model not initialized")
            return {}

        if len(self.sample_buffer) == 0:
            logger.warning("No samples in buffer")
            return {}

        batch_size = batch_size or self.batch_size
        batch_size = min(batch_size, len(self.sample_buffer))

        # Get batch from buffer
        batch = [self.sample_buffer.popleft() for _ in range(batch_size)]

        X_batch = np.array([sample['X'] for sample in batch])
        y_batch = np.array([sample['y'] for sample in batch])

        # Scale features
        X_batch_scaled = self.scaler.transform(X_batch)

        # Partial fit (incremental update)
        self.model.partial_fit(X_batch_scaled, y_batch)

        # Evaluate on batch
        y_pred = self.model.predict(X_batch_scaled)
        accuracy = np.mean(y_pred == y_batch)

        # Update statistics
        self.n_updates += 1
        self.current_accuracy = accuracy
        self.performance_buffer.append(accuracy)

        # Check for drift
        self.drift_detected = self._detect_drift()

        logger.info(f"Model updated: batch_size={batch_size}, accuracy={accuracy:.4f}, drift={self.drift_detected}")

        return {
            'batch_size': batch_size,
            'accuracy': float(accuracy),
            'n_updates': self.n_updates,
            'n_samples_seen': self.n_samples_seen,
            'buffer_size': len(self.sample_buffer),
            'drift_detected': self.drift_detected
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict with online model

        Args:
            X: Feature matrix

        Returns:
            Predictions
        """
        if not self.is_initialized or self.model is None:
            logger.error("Model not initialized")
            return np.array([])

        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities

        Args:
            X: Feature matrix

        Returns:
            Class probabilities
        """
        if not self.is_initialized or self.model is None:
            logger.error("Model not initialized")
            return np.array([])

        if not hasattr(self.model, 'predict_proba'):
            logger.error("Model does not support probability prediction")
            return np.array([])

        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)

        return probabilities

    def _detect_drift(self) -> bool:
        """
        Detect concept drift in model performance

        Returns:
            True if drift detected, False otherwise
        """
        if len(self.performance_buffer) < self.drift_window_size:
            return False

        # Compare recent performance to older performance
        recent_perf = list(self.performance_buffer)[-self.drift_window_size // 2:]
        older_perf = list(self.performance_buffer)[:self.drift_window_size // 2]

        recent_avg = np.mean(recent_perf)
        older_avg = np.mean(older_perf)

        # Drift if recent performance significantly worse
        performance_drop = older_avg - recent_avg

        if performance_drop > self.drift_threshold:
            logger.warning(f"Drift detected! Performance drop: {performance_drop:.4f}")
            return True

        return False

    def handle_drift(self) -> Dict[str, Any]:
        """
        Handle concept drift by resetting or adapting model

        Returns:
            Drift handling results
        """
        if not self.drift_detected:
            logger.info("No drift detected, no action needed")
            return {'action': 'none'}

        logger.warning("Handling concept drift...")

        # Option 1: Reset model (start fresh)
        # self.initialize_model(n_features)

        # Option 2: Increase learning rate (adapt faster)
        if hasattr(self.model, 'learning_rate') and self.model.learning_rate == 'constant':
            self.model.eta0 *= 1.5  # Increase learning rate by 50%
            logger.info(f"Increased learning rate to {self.model.eta0:.6f}")

        # Option 3: Clear old samples from buffer (forget old patterns)
        old_buffer_size = len(self.sample_buffer)
        keep_recent = old_buffer_size // 2
        self.sample_buffer = deque(
            list(self.sample_buffer)[-keep_recent:],
            maxlen=self.buffer_size
        )

        logger.info(f"Cleared old samples: {old_buffer_size} -> {len(self.sample_buffer)}")

        # Reset drift flag
        self.drift_detected = False

        return {
            'action': 'adapted',
            'old_buffer_size': old_buffer_size,
            'new_buffer_size': len(self.sample_buffer),
            'learning_rate_increased': True
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Performance stats
        """
        if len(self.performance_buffer) == 0:
            return {
                'current_accuracy': 0.0,
                'avg_accuracy': 0.0,
                'min_accuracy': 0.0,
                'max_accuracy': 0.0,
                'std_accuracy': 0.0
            }

        perf_array = np.array(list(self.performance_buffer))

        return {
            'current_accuracy': float(self.current_accuracy),
            'avg_accuracy': float(np.mean(perf_array)),
            'min_accuracy': float(np.min(perf_array)),
            'max_accuracy': float(np.max(perf_array)),
            'std_accuracy': float(np.std(perf_array)),
            'n_samples': len(self.performance_buffer)
        }

    def auto_update_loop(self) -> Dict[str, Any]:
        """
        Automatic update loop - update model if buffer has enough samples

        Returns:
            Update results
        """
        results = []

        while self.should_update():
            result = self.update_model()
            results.append(result)

            # Handle drift if detected
            if self.drift_detected:
                drift_result = self.handle_drift()
                result['drift_handling'] = drift_result

        return {
            'n_updates': len(results),
            'updates': results,
            'final_buffer_size': len(self.sample_buffer)
        }

    def save_model(self, path: Optional[str] = None) -> bool:
        """Save online model to file"""
        if self.model is None:
            logger.error("No model to save")
            return False

        path = path or self.model_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save model and metadata
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config,
                'is_initialized': self.is_initialized,
                'n_updates': self.n_updates,
                'n_samples_seen': self.n_samples_seen,
                'current_accuracy': self.current_accuracy,
                'performance_buffer': list(self.performance_buffer)
            }

            with open(path, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Online model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self, path: Optional[str] = None) -> bool:
        """Load online model from file"""
        path = path or self.model_path

        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.config = model_data.get('config', self.config)
            self.is_initialized = model_data.get('is_initialized', True)
            self.n_updates = model_data.get('n_updates', 0)
            self.n_samples_seen = model_data.get('n_samples_seen', 0)
            self.current_accuracy = model_data.get('current_accuracy', 0.0)

            perf_buffer = model_data.get('performance_buffer', [])
            self.performance_buffer = deque(perf_buffer, maxlen=self.drift_window_size)

            logger.info(f"Online model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_learner_info(self) -> Dict[str, Any]:
        """Get online learner information"""
        return {
            'is_initialized': self.is_initialized,
            'model_type': self.model_type,
            'loss': self.loss,
            'learning_rate': self.learning_rate,
            'alpha': self.alpha,
            'n_updates': self.n_updates,
            'n_samples_seen': self.n_samples_seen,
            'buffer_size': len(self.sample_buffer),
            'max_buffer_size': self.buffer_size,
            'batch_size': self.batch_size,
            'current_accuracy': self.current_accuracy,
            'drift_detected': self.drift_detected,
            'performance_stats': self.get_performance_stats()
        }
