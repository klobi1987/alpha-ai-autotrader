"""
Advanced ML Pattern Discovery Engine
Automatically discovers and learns trading patterns from historical data
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import logging

logger = logging.getLogger(__name__)


class PatternDiscoveryEngine:
    """
    Advanced ML Pattern Discovery Engine
    
    Features:
    - K-Means clustering for pattern grouping
    - Random Forest for pattern success prediction
    - Isolation Forest for anomaly detection
    - PCA for dimensionality reduction
    - Real-time pattern matching
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Pattern Discovery Engine"""
        self.config = config or {}
        
        # ML Models
        self.kmeans_model = None
        self.rf_model = None
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=10)
        
        # Pattern Storage
        self.discovered_patterns = []
        self.pattern_performance = {}
        
        # Configuration
        self.n_clusters = self.config.get('n_clusters', 20)
        self.min_pattern_occurrences = self.config.get('min_pattern_occurrences', 5)
        self.min_success_rate = self.config.get('min_success_rate', 0.6)
        self.lookback_period = self.config.get('lookback_period', 100)
        
        logger.info("🧠 ML Pattern Discovery Engine initialized")
    
    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features from price data
        
        Features:
        - Price momentum (multiple timeframes)
        - Volume patterns
        - Volatility metrics
        - RSI, MACD, Bollinger Bands
        - Social sentiment (if available)
        """
        features = []
        
        # Price momentum features
        for period in [5, 10, 20, 50]:
            df[f'return_{period}'] = df['close'].pct_change(period)
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
        
        # Volume features
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        df['volume_momentum'] = df['volume'].pct_change(10)
        
        # Volatility features
        df['volatility_10'] = df['close'].pct_change().rolling(10).std()
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        df['atr'] = self._calculate_atr(df, period=14)
        
        # Technical indicators
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
        df['bb_upper'], df['bb_lower'], df['bb_middle'] = self._calculate_bollinger_bands(df['close'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Price position features
        df['price_vs_ma20'] = df['close'] / df['close'].rolling(20).mean() - 1
        df['price_vs_ma50'] = df['close'] / df['close'].rolling(50).mean() - 1
        
        # High/Low features
        df['high_low_ratio'] = df['high'] / df['low'] - 1
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # Select feature columns
        feature_cols = [
            'return_5', 'return_10', 'return_20', 'return_50',
            'momentum_5', 'momentum_10', 'momentum_20', 'momentum_50',
            'volume_ratio', 'volume_momentum',
            'volatility_10', 'volatility_20', 'atr',
            'rsi', 'macd', 'macd_signal',
            'bb_position', 'price_vs_ma20', 'price_vs_ma50',
            'high_low_ratio', 'close_position'
        ]
        
        # Drop NaN and return features
        df_clean = df[feature_cols].dropna()
        
        return df_clean.values
    
    def discover_patterns(self, historical_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Discover patterns from historical data using K-Means clustering
        
        Args:
            historical_data: DataFrame with OHLCV data
            
        Returns:
            List of discovered patterns with metadata
        """
        logger.info(f"🔍 Discovering patterns from {len(historical_data)} data points...")
        
        # Extract features
        features = self.extract_features(historical_data)
        
        if len(features) < self.min_pattern_occurrences:
            logger.warning("Not enough data for pattern discovery")
            return []
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Apply PCA for dimensionality reduction
        features_pca = self.pca.fit_transform(features_scaled)
        
        # K-Means clustering
        self.kmeans_model = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=10
        )
        cluster_labels = self.kmeans_model.fit_predict(features_pca)
        
        # Analyze each cluster
        patterns = []
        for cluster_id in range(self.n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_size = np.sum(cluster_mask)
            
            if cluster_size < self.min_pattern_occurrences:
                continue
            
            # Get cluster center in original feature space
            cluster_center_pca = self.kmeans_model.cluster_centers_[cluster_id]
            cluster_center = self.pca.inverse_transform(cluster_center_pca.reshape(1, -1))
            cluster_center = self.scaler.inverse_transform(cluster_center)[0]
            
            # Calculate pattern characteristics
            pattern = {
                'pattern_id': f'ML_PATTERN_{cluster_id}',
                'cluster_id': cluster_id,
                'occurrences': int(cluster_size),
                'center': cluster_center.tolist(),
                'discovered_at': datetime.now().isoformat(),
                'type': 'ml_discovered',
                'confidence': self._calculate_pattern_confidence(cluster_size, len(features))
            }
            
            patterns.append(pattern)
        
        self.discovered_patterns = patterns
        logger.info(f"✅ Discovered {len(patterns)} patterns")
        
        return patterns
    
    def train_pattern_predictor(
        self,
        historical_data: pd.DataFrame,
        labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Train Random Forest to predict pattern success
        
        Args:
            historical_data: DataFrame with OHLCV data
            labels: Binary labels (1 = successful trade, 0 = unsuccessful)
            
        Returns:
            Training metrics
        """
        logger.info("🎓 Training pattern success predictor...")
        
        # Extract features
        features = self.extract_features(historical_data)
        
        # Ensure labels match features length
        if len(labels) != len(features):
            logger.warning(f"Label length mismatch: {len(labels)} vs {len(features)}")
            min_len = min(len(labels), len(features))
            labels = labels[:min_len]
            features = features[:min_len]
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train Random Forest
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(features_scaled, labels)
        
        # Calculate metrics
        train_score = self.rf_model.score(features_scaled, labels)
        feature_importance = self.rf_model.feature_importances_
        
        metrics = {
            'train_accuracy': float(train_score),
            'n_samples': len(features),
            'n_features': features.shape[1],
            'feature_importance': feature_importance.tolist(),
            'trained_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Pattern predictor trained (accuracy: {train_score:.2%})")
        
        return metrics
    
    def detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalous patterns using Isolation Forest
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of detected anomalies
        """
        logger.info("🔍 Detecting anomalous patterns...")
        
        # Extract features
        features = self.extract_features(data)
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        anomaly_labels = self.isolation_forest.fit_predict(features_scaled)
        
        # Get anomaly scores
        anomaly_scores = self.isolation_forest.score_samples(features_scaled)
        
        # Extract anomalies
        anomalies = []
        for idx, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:  # Anomaly
                anomalies.append({
                    'index': int(idx),
                    'anomaly_score': float(score),
                    'timestamp': data.index[idx].isoformat() if hasattr(data.index[idx], 'isoformat') else str(data.index[idx]),
                    'type': 'anomaly'
                })
        
        logger.info(f"✅ Detected {len(anomalies)} anomalous patterns")
        
        return anomalies
    
    def match_pattern(self, current_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Match current market data against discovered patterns
        
        Args:
            current_data: Recent OHLCV data
            
        Returns:
            Best matching pattern or None
        """
        if not self.discovered_patterns or self.kmeans_model is None:
            return None
        
        # Extract features from current data
        features = self.extract_features(current_data)
        
        if len(features) == 0:
            return None
        
        # Use last data point
        current_features = features[-1].reshape(1, -1)
        
        # Normalize
        current_features_scaled = self.scaler.transform(current_features)
        
        # Apply PCA
        current_features_pca = self.pca.transform(current_features_scaled)
        
        # Find closest cluster
        cluster_id = self.kmeans_model.predict(current_features_pca)[0]
        
        # Get distance to cluster center
        distance = np.linalg.norm(
            current_features_pca - self.kmeans_model.cluster_centers_[cluster_id]
        )
        
        # Find matching pattern
        matching_pattern = None
        for pattern in self.discovered_patterns:
            if pattern['cluster_id'] == cluster_id:
                matching_pattern = pattern.copy()
                matching_pattern['match_distance'] = float(distance)
                matching_pattern['match_confidence'] = float(1 / (1 + distance))
                break
        
        return matching_pattern
    
    def predict_pattern_success(self, data: pd.DataFrame) -> float:
        """
        Predict success probability of current pattern
        
        Args:
            data: Recent OHLCV data
            
        Returns:
            Success probability (0-1)
        """
        if self.rf_model is None:
            return 0.5  # Neutral if no model trained
        
        # Extract features
        features = self.extract_features(data)
        
        if len(features) == 0:
            return 0.5
        
        # Use last data point
        current_features = features[-1].reshape(1, -1)
        
        # Normalize
        current_features_scaled = self.scaler.transform(current_features)
        
        # Predict probability
        success_prob = self.rf_model.predict_proba(current_features_scaled)[0][1]
        
        return float(success_prob)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about discovered patterns"""
        if not self.discovered_patterns:
            return {
                'total_patterns': 0,
                'avg_occurrences': 0,
                'avg_confidence': 0
            }
        
        total_occurrences = sum(p['occurrences'] for p in self.discovered_patterns)
        avg_occurrences = total_occurrences / len(self.discovered_patterns)
        avg_confidence = sum(p['confidence'] for p in self.discovered_patterns) / len(self.discovered_patterns)
        
        return {
            'total_patterns': len(self.discovered_patterns),
            'total_occurrences': total_occurrences,
            'avg_occurrences': avg_occurrences,
            'avg_confidence': avg_confidence,
            'patterns': self.discovered_patterns
        }
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: int = 2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, lower, middle
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    def _calculate_pattern_confidence(self, cluster_size: int, total_size: int) -> float:
        """Calculate pattern confidence based on occurrence frequency"""
        frequency = cluster_size / total_size
        # Normalize to 0-1 range with sigmoid-like function
        confidence = 1 / (1 + np.exp(-10 * (frequency - 0.05)))
        return float(confidence)
