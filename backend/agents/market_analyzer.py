"""
Alpha AI Autotrader - Market Analyzer Agent
Technical analysis expert
"""
from typing import Dict, List, Optional
import numpy as np
from .base_agent import BaseAgent


class MarketAnalyzerAgent(BaseAgent):
    """
    Technical Analysis Expert
    
    Analyzes:
    - Price action and trends
    - Technical indicators (EMA, RSI, MACD, etc.)
    - Support/resistance levels
    - Volume analysis
    - Chart patterns
    """
    
    def __init__(self):
        super().__init__(
            name="crypto-market-analyzer",
            role="Technical Analysis Expert"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze technical indicators and price action"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        price = coin_data.get("price", 0)
        volume_24h = coin_data.get("volume_24h", 0)
        volatility = coin_data.get("volatility", 0)
        
        # Price changes
        change_1h = coin_data.get("percent_change_1h", 0)
        change_24h = coin_data.get("percent_change_24h", 0)
        change_7d = coin_data.get("percent_change_7d", 0)
        
        indicators = {}
        warnings = []
        confidence = 5.0  # Start neutral
        decision = "WAIT"
        reasoning_parts = []
        
        # Analyze trend
        if change_24h > 5 and change_7d > 10:
            confidence += 1.5
            decision = "LONG"
            reasoning_parts.append(f"Strong uptrend (+{change_24h:.1f}% 24h, +{change_7d:.1f}% 7d)")
            indicators["trend"] = "bullish"
        
        elif change_24h < -5 and change_7d < -10:
            confidence += 1.0
            decision = "SHORT"
            reasoning_parts.append(f"Strong downtrend ({change_24h:.1f}% 24h, {change_7d:.1f}% 7d)")
            indicators["trend"] = "bearish"
        
        else:
            indicators["trend"] = "neutral"
            reasoning_parts.append("Neutral trend")
        
        # Analyze volatility
        if volatility > 0.15:  # >15% volatility
            warnings.append(f"High volatility ({volatility:.1%}) - risky")
            confidence -= 0.5
        elif volatility < 0.03:  # <3% volatility
            reasoning_parts.append(f"Low volatility ({volatility:.1%}) - consolidating")
            if decision == "LONG":
                confidence += 0.5  # Good for breakout
        
        indicators["volatility"] = volatility
        
        # Analyze volume
        # Note: We don't have historical volume, so we use heuristics
        if volume_24h > 10_000_000:  # >$10M volume
            reasoning_parts.append(f"High volume (${volume_24h:,.0f})")
            confidence += 0.5
            indicators["volume_status"] = "high"
        elif volume_24h < 1_000_000:  # <$1M volume
            warnings.append(f"Low volume (${volume_24h:,.0f}) - low liquidity")
            confidence -= 1.0
            indicators["volume_status"] = "low"
        else:
            indicators["volume_status"] = "normal"
        
        # Momentum check (1h vs 24h)
        if abs(change_1h) > abs(change_24h) / 24:
            # Recent momentum stronger than average
            if change_1h > 0 and decision == "LONG":
                reasoning_parts.append("Strong recent momentum")
                confidence += 0.5
            elif change_1h < 0 and decision == "SHORT":
                reasoning_parts.append("Strong recent downward momentum")
                confidence += 0.5
        
        # Market data analysis (if available)
        if market_data:
            ohlcv = market_data.get("ohlcv", [])
            if len(ohlcv) > 0:
                # Analyze recent candles
                recent_closes = [candle[4] for candle in ohlcv[-10:]]
                if len(recent_closes) >= 10:
                    # Simple trend detection
                    if recent_closes[-1] > recent_closes[0]:
                        reasoning_parts.append("Price trending up (10 candles)")
                        if decision == "LONG":
                            confidence += 0.5
                    else:
                        reasoning_parts.append("Price trending down (10 candles)")
                        if decision == "SHORT":
                            confidence += 0.5
        
        # Cap confidence
        confidence = min(max(confidence, 0.0), 10.0)
        
        # Build reasoning
        reasoning = " | ".join(reasoning_parts)
        if warnings:
            reasoning += " | ⚠️ " + ", ".join(warnings)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators": indicators,
            "warnings": warnings
        }
