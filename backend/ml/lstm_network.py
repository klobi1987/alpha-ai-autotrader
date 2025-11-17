"""
LSTM Neural Network for Pattern Sequence Prediction
Deep learning for time series forecasting and trend detection
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import pickle
import os

logger = logging.getLogger(__name__)

# Try to import TensorFlow/Keras (optional dependency)
try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    KERAS_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow/Keras not available. LSTM features will be limited.")
    KERAS_AVAILABLE = False


class LSTMNetwork:
    """
    LSTM Neural Network for Time Series Prediction

    Features:
    - Multi-layer LSTM architecture
    - Sequence-to-sequence prediction
    - Multi-step ahead forecasting
    - Trend detection (continuation/reversal)
    - Monte Carlo confidence estimation
    - Model save/load functionality
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LSTM Network"""
        self.config = config or {}

        # Architecture parameters
        self.sequence_length = self.config.get('sequence_length', 20)
        self.n_features = self.config.get('n_features', 10)
        self.lstm_units = self.config.get('lstm_units', [128, 64, 32])
        self.dropout_rate = self.config.get('dropout_rate', 0.2)
        self.learning_rate = self.config.get('learning_rate', 0.001)

        # Training parameters
        self.batch_size = self.config.get('batch_size', 32)
        self.epochs = self.config.get('epochs', 50)
        self.validation_split = self.config.get('validation_split', 0.2)

        # Prediction parameters
        self.forecast_steps = self.config.get('forecast_steps', 10)
        self.mc_iterations = self.config.get('mc_iterations', 100)

        # Model
        self.model = None
        self.is_trained = False
        self.training_history = None

        # Model path
        self.model_path = self.config.get('model_path', 'models/lstm_model.h5')

    def build_model(self) -> None:
        """Build LSTM model architecture"""
        if not KERAS_AVAILABLE:
            logger.error("Keras not available. Cannot build LSTM model.")
            return

        model = Sequential()

        # First LSTM layer
        model.add(LSTM(
            self.lstm_units[0],
            return_sequences=True,
            input_shape=(self.sequence_length, self.n_features)
        ))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout_rate))

        # Second LSTM layer
        if len(self.lstm_units) > 1:
            model.add(LSTM(
                self.lstm_units[1],
                return_sequences=True if len(self.lstm_units) > 2 else False
            ))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))

        # Third LSTM layer (optional)
        if len(self.lstm_units) > 2:
            model.add(LSTM(self.lstm_units[2], return_sequences=False))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))

        # Dense layers
        model.add(Dense(32, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(16, activation='relu'))

        # Output layer (predicting next values)
        model.add(Dense(self.n_features))

        # Compile model
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
        )

        self.model = model
        logger.info(f"LSTM model built: {len(self.lstm_units)} layers, {sum(self.lstm_units)} total units")

    def prepare_sequences(
        self,
        data: np.ndarray,
        target: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Prepare sequences for LSTM training/prediction

        Args:
            data: Input features (n_samples, n_features)
            target: Target values (optional, for training)

        Returns:
            X: Sequences (n_sequences, sequence_length, n_features)
            y: Targets (n_sequences, n_features) if target provided
        """
        X = []
        y = [] if target is not None else None

        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            if target is not None:
                y.append(target[i + self.sequence_length])

        X = np.array(X)
        y = np.array(y) if y else None

        return X, y

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Train LSTM model

        Args:
            X_train: Training sequences (n_sequences, sequence_length, n_features)
            y_train: Training targets (n_sequences, n_features)
            X_val: Validation sequences (optional)
            y_val: Validation targets (optional)

        Returns:
            Training history
        """
        if not KERAS_AVAILABLE:
            logger.error("Keras not available. Cannot train LSTM model.")
            return {}

        if self.model is None:
            self.build_model()

        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]

        # Train model
        validation_data = (X_val, y_val) if X_val is not None else None

        history = self.model.fit(
            X_train,
            y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_data=validation_data,
            validation_split=self.validation_split if validation_data is None else 0.0,
            callbacks=callbacks,
            verbose=1
        )

        self.is_trained = True
        self.training_history = history.history

        logger.info(f"LSTM training complete. Final loss: {history.history['loss'][-1]:.6f}")

        return self.training_history

    def predict(
        self,
        X: np.ndarray,
        return_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Predict next values

        Args:
            X: Input sequences (n_sequences, sequence_length, n_features)
            return_confidence: Whether to compute confidence intervals

        Returns:
            predictions: Predicted values
            confidence: Confidence intervals (if return_confidence=True)
        """
        if not KERAS_AVAILABLE or self.model is None:
            logger.error("Model not available for prediction")
            return {}

        # Base prediction
        predictions = self.model.predict(X, verbose=0)

        result = {
            'predictions': predictions,
            'mean': np.mean(predictions, axis=0),
            'std': np.std(predictions, axis=0)
        }

        # Monte Carlo confidence estimation
        if return_confidence and self.mc_iterations > 0:
            mc_predictions = []

            for _ in range(self.mc_iterations):
                mc_pred = self.model.predict(X, verbose=0)
                mc_predictions.append(mc_pred)

            mc_predictions = np.array(mc_predictions)

            result['confidence_lower'] = np.percentile(mc_predictions, 5, axis=0)
            result['confidence_upper'] = np.percentile(mc_predictions, 95, axis=0)
            result['confidence_interval'] = result['confidence_upper'] - result['confidence_lower']

        return result

    def forecast_multi_step(
        self,
        initial_sequence: np.ndarray,
        n_steps: Optional[int] = None
    ) -> np.ndarray:
        """
        Multi-step ahead forecasting

        Args:
            initial_sequence: Initial sequence (sequence_length, n_features)
            n_steps: Number of steps to forecast (default: self.forecast_steps)

        Returns:
            forecasts: Forecasted values (n_steps, n_features)
        """
        if not KERAS_AVAILABLE or self.model is None:
            logger.error("Model not available for forecasting")
            return np.array([])

        n_steps = n_steps or self.forecast_steps
        forecasts = []
        current_sequence = initial_sequence.copy()

        for _ in range(n_steps):
            # Predict next step
            X = current_sequence.reshape(1, self.sequence_length, self.n_features)
            next_pred = self.model.predict(X, verbose=0)[0]

            forecasts.append(next_pred)

            # Update sequence (rolling window)
            current_sequence = np.vstack([current_sequence[1:], next_pred])

        return np.array(forecasts)

    def detect_trend(
        self,
        sequence: np.ndarray,
        price_index: int = 0
    ) -> Dict[str, Any]:
        """
        Detect trend (continuation/reversal) from sequence

        Args:
            sequence: Input sequence (sequence_length, n_features)
            price_index: Index of price feature in sequence

        Returns:
            trend_info: Trend detection results
        """
        if not KERAS_AVAILABLE or self.model is None:
            logger.error("Model not available for trend detection")
            return {}

        # Forecast next steps
        forecasts = self.forecast_multi_step(sequence, n_steps=5)

        # Extract price forecasts
        price_forecasts = forecasts[:, price_index]
        current_price = sequence[-1, price_index]

        # Detect trend
        price_changes = np.diff(price_forecasts)
        avg_change = np.mean(price_changes)
        std_change = np.std(price_changes)

        # Current trend (from historical data)
        historical_prices = sequence[:, price_index]
        historical_trend = np.mean(np.diff(historical_prices[-5:]))

        # Trend prediction
        if avg_change > 0.001:
            predicted_trend = 'bullish'
        elif avg_change < -0.001:
            predicted_trend = 'bearish'
        else:
            predicted_trend = 'neutral'

        # Reversal detection
        is_reversal = (historical_trend > 0 and avg_change < 0) or \
                      (historical_trend < 0 and avg_change > 0)

        return {
            'current_price': float(current_price),
            'forecasted_prices': price_forecasts.tolist(),
            'avg_change': float(avg_change),
            'std_change': float(std_change),
            'predicted_trend': predicted_trend,
            'historical_trend': 'bullish' if historical_trend > 0 else 'bearish',
            'is_reversal': bool(is_reversal),
            'confidence': float(1.0 - min(std_change / abs(avg_change) if avg_change != 0 else 1.0, 1.0))
        }

    def save_model(self, path: Optional[str] = None) -> bool:
        """Save model to file"""
        if not KERAS_AVAILABLE or self.model is None:
            logger.error("No model to save")
            return False

        path = path or self.model_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save Keras model
            self.model.save(path)

            # Save config and metadata
            metadata_path = path.replace('.h5', '_metadata.pkl')
            metadata = {
                'config': self.config,
                'is_trained': self.is_trained,
                'training_history': self.training_history
            }
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)

            logger.info(f"Model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self, path: Optional[str] = None) -> bool:
        """Load model from file"""
        if not KERAS_AVAILABLE:
            logger.error("Keras not available. Cannot load model.")
            return False

        path = path or self.model_path

        try:
            # Load Keras model
            self.model = load_model(path)

            # Load metadata
            metadata_path = path.replace('.h5', '_metadata.pkl')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                    self.config = metadata.get('config', self.config)
                    self.is_trained = metadata.get('is_trained', True)
                    self.training_history = metadata.get('training_history')

            logger.info(f"Model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if not KERAS_AVAILABLE or self.model is None:
            return {
                'available': False,
                'error': 'Keras not available or model not built'
            }

        return {
            'available': True,
            'is_trained': self.is_trained,
            'architecture': {
                'sequence_length': self.sequence_length,
                'n_features': self.n_features,
                'lstm_units': self.lstm_units,
                'dropout_rate': self.dropout_rate,
                'total_params': self.model.count_params() if self.model else 0
            },
            'training': {
                'batch_size': self.batch_size,
                'epochs': self.epochs,
                'learning_rate': self.learning_rate,
                'final_loss': self.training_history['loss'][-1] if self.training_history else None,
                'final_val_loss': self.training_history.get('val_loss', [None])[-1] if self.training_history else None
            },
            'prediction': {
                'forecast_steps': self.forecast_steps,
                'mc_iterations': self.mc_iterations
            }
        }
