"""
Alpha AI Autotrader - Pattern Detection System
10 high-probability trading patterns
"""
from typing import Dict, List, Optional, Tuple
from loguru import logger
import numpy as np


class PatternDetector:
    """
    Detects trading patterns from LunarCrush + MEXC data
    
    Patterns:
    1. Social Surge + Consolidation (User's discovery)
    2. AltRank Momentum Breakout
    3. Galaxy Score Improvement
    4. Sentiment Divergence
    5. Volume Profile POC Bounce
    6. Funding Rate Reversal
    7. Whale Accumulation Signal
    8. Fear & Greed Extremes
    9. Correlation Breakdown
    10. Multi-Timeframe Confluence
    """
    
    def __init__(self):
        self.patterns_detected = []
    
    def detect_all_patterns(
        self,
        coin_data: Dict,
        price_data: List[List],  # OHLCV
        orderbook: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Run all pattern detectors
        
        Args:
            coin_data: LunarCrush coin data
            price_data: MEXC OHLCV data [[timestamp, o, h, l, c, v], ...]
            orderbook: MEXC orderbook (optional)
        
        Returns:
            List of detected patterns with confidence scores
        """
        patterns = []
        
        # Pattern 1: Social Surge + Consolidation
        p1 = self.detect_social_surge_consolidation(coin_data, price_data)
        if p1:
            patterns.append(p1)
        
        # Pattern 2: AltRank Momentum
        p2 = self.detect_altrank_momentum(coin_data)
        if p2:
            patterns.append(p2)
        
        # Pattern 3: Galaxy Score Improvement
        p3 = self.detect_galaxy_improvement(coin_data)
        if p3:
            patterns.append(p3)
        
        # Pattern 4: Sentiment Divergence
        p4 = self.detect_sentiment_divergence(coin_data, price_data)
        if p4:
            patterns.append(p4)
        
        # Pattern 5: Volume Profile POC Bounce
        p5 = self.detect_poc_bounce(price_data)
        if p5:
            patterns.append(p5)
        
        # Pattern 6: Funding Rate Reversal (futures only)
        # Requires funding rate data - implement when available
        
        # Pattern 7: Whale Accumulation
        p7 = self.detect_whale_accumulation(coin_data, price_data)
        if p7:
            patterns.append(p7)
        
        # Pattern 8: Fear & Greed Extremes
        p8 = self.detect_sentiment_extremes(coin_data)
        if p8:
            patterns.append(p8)
        
        # Pattern 9: Multi-Timeframe Confluence
        p9 = self.detect_mtf_confluence(price_data)
        if p9:
            patterns.append(p9)
        
        return patterns
    
    # ==================== PATTERN 1: Social Surge + Consolidation ====================
    
    def detect_social_surge_consolidation(
        self,
        coin_data: Dict,
        price_data: List[List]
    ) -> Optional[Dict]:
        """
        User's discovered pattern:
        - Social volume surge (2x+ average)
        - Price consolidating (low volatility)
        - AltRank improving
        
        Signal: Breakout imminent
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        
        # Social surge check
        social_vol = coin_data.get('social_volume_24h', 0)
        social_dom = coin_data.get('social_dominance', 0)
        
        # Heuristic: social_dominance > 0.5% = surge
        social_surge = social_dom > 0.5
        
        # Price consolidation check (low volatility)
        if len(price_data) < 20:
            return None
        
        recent_closes = [candle[4] for candle in price_data[-20:]]
        volatility = np.std(recent_closes) / np.mean(recent_closes)
        
        consolidating = volatility < 0.03  # <3% volatility
        
        # AltRank improving
        alt_rank = coin_data.get('alt_rank', 0)
        alt_rank_prev = coin_data.get('alt_rank_previous', 0)
        alt_rank_improving = alt_rank < alt_rank_prev  # Lower rank = better
        
        if social_surge and consolidating and alt_rank_improving:
            confidence = 8.5
            
            return {
                'pattern_name': 'Social Surge + Consolidation',
                'pattern_type': 'breakout',
                'symbol': symbol,
                'confidence': confidence,
                'direction': 'LONG',
                'reason': f'Social surge (dom: {social_dom:.2f}%), price consolidating (vol: {volatility:.2%}), AltRank improving',
                'indicators': {
                    'social_dominance': social_dom,
                    'volatility': volatility,
                    'alt_rank_change': alt_rank_prev - alt_rank
                }
            }
        
        return None
    
    # ==================== PATTERN 2: AltRank Momentum ====================
    
    def detect_altrank_momentum(self, coin_data: Dict) -> Optional[Dict]:
        """
        Big AltRank jump (500+ positions)
        Indicates massive social attention spike
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        alt_rank = coin_data.get('alt_rank', 0)
        alt_rank_prev = coin_data.get('alt_rank_previous', 0)
        
        if not alt_rank or not alt_rank_prev:
            return None
        
        jump = alt_rank_prev - alt_rank
        
        if jump > 500:
            confidence = min(8.0 + (jump / 1000), 9.5)  # Max 9.5
            
            return {
                'pattern_name': 'AltRank Momentum Breakout',
                'pattern_type': 'momentum',
                'symbol': symbol,
                'confidence': confidence,
                'direction': 'LONG',
                'reason': f'AltRank jumped {jump} positions (massive attention)',
                'indicators': {
                    'alt_rank_jump': jump,
                    'current_rank': alt_rank
                }
            }
        
        return None
    
    # ==================== PATTERN 3: Galaxy Score Improvement ====================
    
    def detect_galaxy_improvement(self, coin_data: Dict) -> Optional[Dict]:
        """
        Galaxy Score improving + already high quality
        Indicates project fundamentals strengthening
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        galaxy = coin_data.get('galaxy_score', 0)
        galaxy_prev = coin_data.get('galaxy_score_previous', 0)
        
        if not galaxy or not galaxy_prev:
            return None
        
        improvement = galaxy - galaxy_prev
        
        if galaxy > 70 and improvement > 10:
            confidence = 7.5 + (improvement / 10)
            
            return {
                'pattern_name': 'Galaxy Score Improvement',
                'pattern_type': 'quality',
                'symbol': symbol,
                'confidence': min(confidence, 9.0),
                'direction': 'LONG',
                'reason': f'Galaxy Score improved +{improvement:.1f} (now {galaxy:.1f}/100)',
                'indicators': {
                    'galaxy_score': galaxy,
                    'improvement': improvement
                }
            }
        
        return None
    
    # ==================== PATTERN 4: Sentiment Divergence ====================
    
    def detect_sentiment_divergence(
        self,
        coin_data: Dict,
        price_data: List[List]
    ) -> Optional[Dict]:
        """
        High sentiment but price declining = accumulation opportunity
        (Contrarian signal)
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        sentiment = coin_data.get('sentiment', 0)
        
        if len(price_data) < 2:
            return None
        
        # Price change last 24h
        price_change_24h = coin_data.get('percent_change_24h', 0)
        
        # High sentiment (>80) but price down
        if sentiment > 80 and price_change_24h < -2:
            confidence = 7.8
            
            return {
                'pattern_name': 'Bullish Sentiment Divergence',
                'pattern_type': 'contrarian',
                'symbol': symbol,
                'confidence': confidence,
                'direction': 'LONG',
                'reason': f'High sentiment ({sentiment}/100) but price down {price_change_24h:.1f}% (accumulation?)',
                'indicators': {
                    'sentiment': sentiment,
                    'price_change_24h': price_change_24h
                }
            }
        
        return None
    
    # ==================== PATTERN 5: Volume Profile POC Bounce ====================
    
    def detect_poc_bounce(self, price_data: List[List]) -> Optional[Dict]:
        """
        Price bouncing off Point of Control (high volume area)
        S-Tier pattern (Patrick Neil)
        """
        if len(price_data) < 50:
            return None
        
        # Calculate volume profile (simplified)
        volumes = [candle[5] for candle in price_data[-50:]]
        closes = [candle[4] for candle in price_data[-50:]]
        
        # Find POC (price level with highest volume)
        # Simplified: use price with max volume
        max_vol_idx = volumes.index(max(volumes))
        poc_price = closes[max_vol_idx]
        
        # Current price
        current_price = closes[-1]
        
        # Check if bouncing off POC (within 2%)
        distance_to_poc = abs(current_price - poc_price) / poc_price
        
        if distance_to_poc < 0.02:  # Within 2%
            # Check if bouncing up
            recent_prices = closes[-5:]
            bouncing_up = recent_prices[-1] > recent_prices[0]
            
            if bouncing_up:
                confidence = 8.2
                
                return {
                    'pattern_name': 'Volume Profile POC Bounce',
                    'pattern_type': 'support',
                    'symbol': 'UNKNOWN',  # Set by caller
                    'confidence': confidence,
                    'direction': 'LONG',
                    'reason': f'Price bouncing off POC at {poc_price:.2f} (high volume support)',
                    'indicators': {
                        'poc_price': poc_price,
                        'current_price': current_price,
                        'distance_pct': distance_to_poc * 100
                    }
                }
        
        return None
    
    # ==================== PATTERN 7: Whale Accumulation ====================
    
    def detect_whale_accumulation(
        self,
        coin_data: Dict,
        price_data: List[List]
    ) -> Optional[Dict]:
        """
        High volume + price stable/up = whales accumulating
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        volume_24h = coin_data.get('volume_24h', 0)
        
        if len(price_data) < 10:
            return None
        
        # Average volume last 10 candles
        recent_volumes = [candle[5] for candle in price_data[-10:]]
        avg_volume = np.mean(recent_volumes)
        
        # Current volume vs average
        current_volume = recent_volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Price change
        price_change = (price_data[-1][4] - price_data[-10][4]) / price_data[-10][4] * 100
        
        # High volume (2x+) + price stable or up
        if volume_ratio > 2.0 and price_change >= -1:
            confidence = 7.5 + min(volume_ratio / 2, 1.5)
            
            return {
                'pattern_name': 'Whale Accumulation Signal',
                'pattern_type': 'accumulation',
                'symbol': symbol,
                'confidence': min(confidence, 9.0),
                'direction': 'LONG',
                'reason': f'Volume {volume_ratio:.1f}x average, price stable (whales buying)',
                'indicators': {
                    'volume_ratio': volume_ratio,
                    'price_change': price_change
                }
            }
        
        return None
    
    # ==================== PATTERN 8: Sentiment Extremes ====================
    
    def detect_sentiment_extremes(self, coin_data: Dict) -> Optional[Dict]:
        """
        Extreme fear or greed = reversal opportunity
        """
        symbol = coin_data.get('symbol', 'UNKNOWN')
        sentiment = coin_data.get('sentiment', 50)
        
        # Extreme fear (<20) = buy opportunity
        if sentiment < 20:
            confidence = 7.0
            
            return {
                'pattern_name': 'Extreme Fear (Contrarian Buy)',
                'pattern_type': 'contrarian',
                'symbol': symbol,
                'confidence': confidence,
                'direction': 'LONG',
                'reason': f'Extreme fear (sentiment: {sentiment}/100) - potential bottom',
                'indicators': {
                    'sentiment': sentiment
                }
            }
        
        # Extreme greed (>90) = potential top (short or avoid)
        elif sentiment > 90:
            confidence = 6.5
            
            return {
                'pattern_name': 'Extreme Greed (Potential Top)',
                'pattern_type': 'contrarian',
                'symbol': symbol,
                'confidence': confidence,
                'direction': 'SHORT',
                'reason': f'Extreme greed (sentiment: {sentiment}/100) - potential reversal',
                'indicators': {
                    'sentiment': sentiment
                }
            }
        
        return None
    
    # ==================== PATTERN 9: Multi-Timeframe Confluence ====================
    
    def detect_mtf_confluence(self, price_data: List[List]) -> Optional[Dict]:
        """
        Multiple timeframes aligned (simplified version)
        Checks if trend is consistent across different periods
        """
        if len(price_data) < 50:
            return None
        
        closes = [candle[4] for candle in price_data]
        
        # Short-term trend (last 5 candles)
        st_trend = closes[-1] > closes[-5]
        
        # Medium-term trend (last 20 candles)
        mt_trend = closes[-1] > closes[-20]
        
        # Long-term trend (last 50 candles)
        lt_trend = closes[-1] > closes[-50]
        
        # All aligned bullish
        if st_trend and mt_trend and lt_trend:
            confidence = 8.0
            
            return {
                'pattern_name': 'Multi-Timeframe Bullish Confluence',
                'pattern_type': 'trend',
                'symbol': 'UNKNOWN',
                'confidence': confidence,
                'direction': 'LONG',
                'reason': 'All timeframes aligned bullish (strong trend)',
                'indicators': {
                    'short_term': 'bullish',
                    'medium_term': 'bullish',
                    'long_term': 'bullish'
                }
            }
        
        # All aligned bearish
        elif not st_trend and not mt_trend and not lt_trend:
            confidence = 7.5
            
            return {
                'pattern_name': 'Multi-Timeframe Bearish Confluence',
                'pattern_type': 'trend',
                'symbol': 'UNKNOWN',
                'confidence': confidence,
                'direction': 'SHORT',
                'reason': 'All timeframes aligned bearish (strong downtrend)',
                'indicators': {
                    'short_term': 'bearish',
                    'medium_term': 'bearish',
                    'long_term': 'bearish'
                }
            }
        
        return None
    
    # ==================== UTILITY ====================
    
    def calculate_confluence_score(self, patterns: List[Dict]) -> float:
        """
        Calculate overall confluence score from multiple patterns
        
        Args:
            patterns: List of detected patterns
        
        Returns:
            Confluence score (0-10)
        """
        if not patterns:
            return 0.0
        
        # Average confidence weighted by pattern count
        total_confidence = sum(p['confidence'] for p in patterns)
        avg_confidence = total_confidence / len(patterns)
        
        # Bonus for multiple patterns
        pattern_bonus = min(len(patterns) * 0.5, 2.0)
        
        confluence = min(avg_confidence + pattern_bonus, 10.0)
        
        return confluence
