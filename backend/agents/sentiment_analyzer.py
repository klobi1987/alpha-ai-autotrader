"""
Alpha AI Autotrader - Sentiment Analyzer Agent
Social sentiment and market psychology specialist
"""
from typing import Dict, Optional
from .base_agent import BaseAgent


class SentimentAnalyzerAgent(BaseAgent):
    """
    Social Sentiment & Market Psychology Specialist
    
    Analyzes:
    - LunarCrush metrics (AltRank, Galaxy Score, Sentiment)
    - Social volume and dominance
    - FUD/FOMO detection
    - Sentiment divergence
    """
    
    def __init__(self):
        super().__init__(
            name="crypto-sentiment-analyzer",
            role="Social Sentiment Specialist"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze social sentiment and psychology"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        # Social metrics
        alt_rank = coin_data.get("alt_rank", 0)
        alt_rank_prev = coin_data.get("alt_rank_previous", 0)
        galaxy_score = coin_data.get("galaxy_score", 0)
        galaxy_prev = coin_data.get("galaxy_score_previous", 0)
        sentiment = coin_data.get("sentiment", 50)
        social_vol = coin_data.get("social_volume_24h", 0)
        social_dom = coin_data.get("social_dominance", 0)
        
        indicators = {}
        warnings = []
        confidence = 5.0
        decision = "WAIT"
        reasoning_parts = []
        
        # AltRank analysis
        if alt_rank and alt_rank_prev:
            alt_rank_change = alt_rank_prev - alt_rank  # Positive = moved up
            
            if alt_rank_change > 500:
                confidence += 2.0
                decision = "LONG"
                reasoning_parts.append(f"🚀 AltRank surge +{alt_rank_change} positions")
                indicators["altrank_signal"] = "strong_surge"
            
            elif alt_rank_change > 200:
                confidence += 1.0
                decision = "LONG"
                reasoning_parts.append(f"AltRank improving +{alt_rank_change}")
                indicators["altrank_signal"] = "improving"
            
            elif alt_rank_change < -200:
                confidence += 0.5
                decision = "SHORT"
                reasoning_parts.append(f"AltRank declining {alt_rank_change}")
                indicators["altrank_signal"] = "declining"
            
            else:
                indicators["altrank_signal"] = "stable"
        
        # Galaxy Score analysis
        if galaxy_score and galaxy_prev:
            galaxy_change = galaxy_score - galaxy_prev
            
            if galaxy_score > 70 and galaxy_change > 10:
                confidence += 1.5
                decision = "LONG"
                reasoning_parts.append(f"✨ Galaxy Score high & improving ({galaxy_score:.1f}/100, +{galaxy_change:.1f})")
                indicators["quality"] = "excellent"
            
            elif galaxy_score > 60:
                reasoning_parts.append(f"Good quality (Galaxy: {galaxy_score:.1f}/100)")
                confidence += 0.5
                indicators["quality"] = "good"
            
            elif galaxy_score < 40:
                warnings.append(f"Low quality (Galaxy: {galaxy_score:.1f}/100)")
                confidence -= 1.0
                indicators["quality"] = "poor"
        
        # Sentiment analysis
        if sentiment > 85:
            # Extreme greed
            warnings.append(f"⚠️ Extreme greed (sentiment: {sentiment}/100) - potential top")
            confidence -= 0.5
            indicators["sentiment_level"] = "extreme_greed"
            
            # Contrarian: might be short opportunity
            if decision == "SHORT":
                confidence += 0.5
        
        elif sentiment > 70:
            # High optimism
            reasoning_parts.append(f"High optimism (sentiment: {sentiment}/100)")
            if decision == "LONG":
                confidence += 0.5
            indicators["sentiment_level"] = "bullish"
        
        elif sentiment < 30:
            # Extreme fear
            reasoning_parts.append(f"💎 Extreme fear (sentiment: {sentiment}/100) - contrarian buy")
            confidence += 1.0
            decision = "LONG"
            indicators["sentiment_level"] = "extreme_fear"
        
        elif sentiment < 50:
            # Bearish sentiment
            reasoning_parts.append(f"Bearish sentiment ({sentiment}/100)")
            indicators["sentiment_level"] = "bearish"
        
        else:
            indicators["sentiment_level"] = "neutral"
        
        # Social volume/dominance analysis
        if social_dom > 1.0:  # >1% of total social activity
            reasoning_parts.append(f"🔥 Viral (social dom: {social_dom:.2f}%)")
            confidence += 1.0
            indicators["social_status"] = "viral"
        
        elif social_dom > 0.5:
            reasoning_parts.append(f"High social activity (dom: {social_dom:.2f}%)")
            confidence += 0.5
            indicators["social_status"] = "trending"
        
        elif social_dom < 0.1:
            warnings.append(f"Low social activity (dom: {social_dom:.2f}%)")
            confidence -= 0.5
            indicators["social_status"] = "quiet"
        
        else:
            indicators["social_status"] = "normal"
        
        # Sentiment divergence check
        price_change_24h = coin_data.get("percent_change_24h", 0)
        
        if sentiment > 75 and price_change_24h < -5:
            # High sentiment but price down = accumulation?
            reasoning_parts.append("📊 Sentiment divergence: high sentiment but price down (accumulation?)")
            confidence += 1.0
            decision = "LONG"
            indicators["divergence"] = "bullish"
        
        elif sentiment < 40 and price_change_24h > 5:
            # Low sentiment but price up = distribution?
            warnings.append("Sentiment divergence: low sentiment but price up (distribution?)")
            confidence -= 0.5
            indicators["divergence"] = "bearish"
        
        # Cap confidence
        confidence = min(max(confidence, 0.0), 10.0)
        
        # Build reasoning
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Neutral sentiment"
        if warnings:
            reasoning += " | ⚠️ " + ", ".join(warnings)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators": indicators,
            "warnings": warnings
        }
