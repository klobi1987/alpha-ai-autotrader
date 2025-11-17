"""
Multi-timeframe Pattern Analysis
Discover and analyze patterns across multiple timeframes
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Timeframe(Enum):
    """Timeframe enumeration"""
    M1 = "1m"   # 1 minute
    M5 = "5m"   # 5 minutes
    M15 = "15m" # 15 minutes
    M30 = "30m" # 30 minutes
    H1 = "1h"   # 1 hour
    H4 = "4h"   # 4 hours
    D1 = "1d"   # 1 day
    W1 = "1w"   # 1 week


class MultiTimeframeAnalyzer:
    """
    Multi-timeframe Pattern Analysis

    Features:
    - Pattern discovery across multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
    - Timeframe alignment and correlation
    - Trend consistency detection
    - Multi-timeframe confluence
    - Pattern strength aggregation
    - Timeframe-specific feature extraction
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Multi-timeframe Analyzer"""
        self.config = config or {}

        # Timeframes to analyze
        self.timeframes = self.config.get('timeframes', [
            Timeframe.M1, Timeframe.M5, Timeframe.M15,
            Timeframe.H1, Timeframe.H4, Timeframe.D1
        ])

        # Confluence settings
        self.min_confluence = self.config.get('min_confluence', 0.6)  # 60% timeframes agree
        self.confluence_weights = self.config.get('confluence_weights', {
            Timeframe.M1: 0.1,
            Timeframe.M5: 0.15,
            Timeframe.M15: 0.2,
            Timeframe.H1: 0.25,
            Timeframe.H4: 0.2,
            Timeframe.D1: 0.1
        })

        # Pattern storage
        self.timeframe_patterns = {tf: [] for tf in self.timeframes}
        self.confluence_patterns = []

    def add_timeframe_data(
        self,
        timeframe: Timeframe,
        data: pd.DataFrame
    ) -> None:
        """
        Add OHLCV data for a specific timeframe

        Args:
            timeframe: Timeframe enum
            data: OHLCV DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if timeframe not in self.timeframes:
            logger.warning(f"Timeframe {timeframe} not in configured timeframes")
            return

        # Store data
        if not hasattr(self, 'timeframe_data'):
            self.timeframe_data = {}

        self.timeframe_data[timeframe] = data

        logger.debug(f"Data added for {timeframe.value}: {len(data)} candles")

    def extract_timeframe_features(
        self,
        timeframe: Timeframe,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """
        Extract features for a specific timeframe

        Args:
            timeframe: Timeframe enum
            lookback: Number of candles to look back

        Returns:
            Feature dictionary
        """
        if not hasattr(self, 'timeframe_data') or timeframe not in self.timeframe_data:
            logger.error(f"No data for timeframe {timeframe.value}")
            return {}

        data = self.timeframe_data[timeframe].tail(lookback)

        if len(data) < lookback:
            logger.warning(f"Insufficient data for {timeframe.value}: {len(data)}/{lookback}")
            return {}

        # Calculate features
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        volume = data['volume'].values if 'volume' in data.columns else None

        # Price features
        price_change = (close[-1] - close[0]) / close[0] * 100
        avg_price = np.mean(close)
        volatility = np.std(close) / avg_price * 100

        # Trend features
        sma_short = np.mean(close[-5:])
        sma_long = np.mean(close)
        trend = 'bullish' if sma_short > sma_long else 'bearish'
        trend_strength = abs(sma_short - sma_long) / sma_long * 100

        # Momentum
        momentum = (close[-1] - close[-5]) / close[-5] * 100 if len(close) >= 5 else 0

        # High/Low range
        current_range = (high[-1] - low[-1]) / close[-1] * 100
        avg_range = np.mean((high - low) / close) * 100

        # Volume (if available)
        volume_features = {}
        if volume is not None:
            volume_features = {
                'avg_volume': float(np.mean(volume)),
                'volume_change': float((volume[-1] - np.mean(volume[:-1])) / np.mean(volume[:-1]) * 100),
                'volume_trend': 'increasing' if volume[-1] > np.mean(volume[:-1]) else 'decreasing'
            }

        features = {
            'timeframe': timeframe.value,
            'price': float(close[-1]),
            'price_change_pct': float(price_change),
            'volatility_pct': float(volatility),
            'trend': trend,
            'trend_strength_pct': float(trend_strength),
            'momentum_pct': float(momentum),
            'current_range_pct': float(current_range),
            'avg_range_pct': float(avg_range),
            'sma_short': float(sma_short),
            'sma_long': float(sma_long),
            **volume_features
        }

        return features

    def analyze_all_timeframes(
        self,
        lookback: int = 20
    ) -> Dict[Timeframe, Dict[str, Any]]:
        """
        Extract features for all timeframes

        Args:
            lookback: Number of candles to look back

        Returns:
            Dictionary mapping timeframes to features
        """
        all_features = {}

        for timeframe in self.timeframes:
            features = self.extract_timeframe_features(timeframe, lookback)
            if features:
                all_features[timeframe] = features

        logger.info(f"Analyzed {len(all_features)} timeframes")

        return all_features

    def detect_trend_confluence(
        self,
        timeframe_features: Dict[Timeframe, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect trend confluence across timeframes

        Args:
            timeframe_features: Features for each timeframe

        Returns:
            Confluence analysis
        """
        if not timeframe_features:
            return {}

        # Count trends
        bullish_count = sum(1 for features in timeframe_features.values() if features.get('trend') == 'bullish')
        bearish_count = sum(1 for features in timeframe_features.values() if features.get('trend') == 'bearish')
        total_count = len(timeframe_features)

        # Overall trend
        if bullish_count > bearish_count:
            overall_trend = 'bullish'
            confluence_ratio = bullish_count / total_count
        else:
            overall_trend = 'bearish'
            confluence_ratio = bearish_count / total_count

        # Weighted confluence (consider timeframe importance)
        weighted_score = 0.0
        total_weight = 0.0

        for timeframe, features in timeframe_features.items():
            weight = self.confluence_weights.get(timeframe, 0.1)
            trend_value = 1.0 if features.get('trend') == overall_trend else -1.0
            weighted_score += trend_value * weight
            total_weight += weight

        weighted_confluence = (weighted_score / total_weight + 1) / 2  # Normalize to 0-1

        # Confluence strength
        if confluence_ratio >= 0.8:
            strength = 'strong'
        elif confluence_ratio >= 0.6:
            strength = 'moderate'
        else:
            strength = 'weak'

        return {
            'overall_trend': overall_trend,
            'confluence_ratio': float(confluence_ratio),
            'weighted_confluence': float(weighted_confluence),
            'strength': strength,
            'bullish_timeframes': bullish_count,
            'bearish_timeframes': bearish_count,
            'total_timeframes': total_count,
            'aligned': confluence_ratio >= self.min_confluence
        }

    def detect_momentum_alignment(
        self,
        timeframe_features: Dict[Timeframe, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect momentum alignment across timeframes

        Args:
            timeframe_features: Features for each timeframe

        Returns:
            Momentum alignment analysis
        """
        if not timeframe_features:
            return {}

        momentums = [features.get('momentum_pct', 0) for features in timeframe_features.values()]

        # Count positive/negative momentum
        positive_count = sum(1 for m in momentums if m > 0)
        negative_count = sum(1 for m in momentums if m < 0)
        total_count = len(momentums)

        # Overall momentum
        avg_momentum = np.mean(momentums)
        momentum_direction = 'positive' if avg_momentum > 0 else 'negative'

        # Alignment ratio
        if avg_momentum > 0:
            alignment_ratio = positive_count / total_count
        else:
            alignment_ratio = negative_count / total_count

        return {
            'avg_momentum_pct': float(avg_momentum),
            'momentum_direction': momentum_direction,
            'alignment_ratio': float(alignment_ratio),
            'positive_timeframes': positive_count,
            'negative_timeframes': negative_count,
            'total_timeframes': total_count,
            'aligned': alignment_ratio >= self.min_confluence
        }

    def detect_volatility_pattern(
        self,
        timeframe_features: Dict[Timeframe, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect volatility patterns across timeframes

        Args:
            timeframe_features: Features for each timeframe

        Returns:
            Volatility pattern analysis
        """
        if not timeframe_features:
            return {}

        volatilities = [features.get('volatility_pct', 0) for features in timeframe_features.values()]

        avg_volatility = np.mean(volatilities)
        max_volatility = np.max(volatilities)
        min_volatility = np.min(volatilities)

        # Volatility level
        if avg_volatility > 5:
            level = 'high'
        elif avg_volatility > 2:
            level = 'medium'
        else:
            level = 'low'

        return {
            'avg_volatility_pct': float(avg_volatility),
            'max_volatility_pct': float(max_volatility),
            'min_volatility_pct': float(min_volatility),
            'volatility_level': level,
            'volatility_range_pct': float(max_volatility - min_volatility)
        }

    def generate_multi_timeframe_signal(
        self,
        timeframe_features: Dict[Timeframe, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate trading signal based on multi-timeframe analysis

        Args:
            timeframe_features: Features for each timeframe

        Returns:
            Multi-timeframe trading signal
        """
        # Analyze confluences
        trend_confluence = self.detect_trend_confluence(timeframe_features)
        momentum_alignment = self.detect_momentum_alignment(timeframe_features)
        volatility_pattern = self.detect_volatility_pattern(timeframe_features)

        # Signal strength (0-1)
        signal_strength = (
            0.5 * trend_confluence.get('weighted_confluence', 0) +
            0.3 * momentum_alignment.get('alignment_ratio', 0) +
            0.2 * (1.0 if volatility_pattern.get('volatility_level') != 'high' else 0.5)
        )

        # Signal direction
        if trend_confluence.get('overall_trend') == 'bullish' and momentum_alignment.get('momentum_direction') == 'positive':
            signal = 'BUY'
        elif trend_confluence.get('overall_trend') == 'bearish' and momentum_alignment.get('momentum_direction') == 'negative':
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'

        # Confidence
        confidence = signal_strength if signal != 'NEUTRAL' else 0.5

        return {
            'signal': signal,
            'confidence': float(confidence),
            'signal_strength': float(signal_strength),
            'trend_confluence': trend_confluence,
            'momentum_alignment': momentum_alignment,
            'volatility_pattern': volatility_pattern,
            'timeframe_features': {tf.value: features for tf, features in timeframe_features.items()}
        }

    def find_best_entry_timeframe(
        self,
        timeframe_features: Dict[Timeframe, Dict[str, Any]],
        signal: str
    ) -> Optional[Timeframe]:
        """
        Find best timeframe for entry based on signal

        Args:
            timeframe_features: Features for each timeframe
            signal: Trading signal (BUY/SELL)

        Returns:
            Best timeframe for entry or None
        """
        if signal not in ['BUY', 'SELL']:
            return None

        # Score each timeframe
        scores = {}

        for timeframe, features in timeframe_features.items():
            score = 0.0

            # Trend alignment
            if signal == 'BUY' and features.get('trend') == 'bullish':
                score += 0.4
            elif signal == 'SELL' and features.get('trend') == 'bearish':
                score += 0.4

            # Momentum alignment
            if signal == 'BUY' and features.get('momentum_pct', 0) > 0:
                score += 0.3
            elif signal == 'SELL' and features.get('momentum_pct', 0) < 0:
                score += 0.3

            # Prefer lower timeframes for entry (better precision)
            if timeframe in [Timeframe.M1, Timeframe.M5]:
                score += 0.2
            elif timeframe in [Timeframe.M15, Timeframe.H1]:
                score += 0.1

            # Lower volatility is better for entry
            volatility = features.get('volatility_pct', 5)
            if volatility < 2:
                score += 0.1

            scores[timeframe] = score

        # Find best
        if scores:
            best_timeframe = max(scores, key=scores.get)
            return best_timeframe

        return None

    def get_timeframe_hierarchy(self) -> List[Timeframe]:
        """Get timeframes sorted by hierarchy (lowest to highest)"""
        timeframe_order = [
            Timeframe.M1, Timeframe.M5, Timeframe.M15,
            Timeframe.M30, Timeframe.H1, Timeframe.H4,
            Timeframe.D1, Timeframe.W1
        ]

        return [tf for tf in timeframe_order if tf in self.timeframes]

    def get_analyzer_info(self) -> Dict[str, Any]:
        """Get multi-timeframe analyzer information"""
        return {
            'timeframes': [tf.value for tf in self.timeframes],
            'min_confluence': self.min_confluence,
            'confluence_weights': {tf.value: weight for tf, weight in self.confluence_weights.items()},
            'n_timeframe_data': len(self.timeframe_data) if hasattr(self, 'timeframe_data') else 0,
            'supported_timeframes': [tf.value for tf in Timeframe]
        }
