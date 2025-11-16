"""
Alpha AI Autotrader - Adaptive Strategy Engine
Multi-strategy trading: Scalping, Day Trading, Swing Trading
Spot & Futures (Long & Short)
"""
from typing import Dict, List, Optional
from loguru import logger
from enum import Enum


class TradingStyle(Enum):
    """Trading style types"""
    SCALPING = "scalping"
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"


class MarketType(Enum):
    """Market types"""
    SPOT = "spot"
    FUTURES = "futures"


class AdaptiveStrategyEngine:
    """
    Adaptive Strategy Engine - Chooses best strategy for each opportunity
    
    Capabilities:
    - Detect best trading style (scalping/day/swing)
    - Choose spot vs futures
    - Decide long vs short
    - Adapt to market conditions
    - Maximize profit potential
    """
    
    def __init__(self):
        """Initialize adaptive strategy engine"""
        
        # Strategy configurations
        self.strategies = {
            TradingStyle.SCALPING: {
                "timeframe": "1m-15m",
                "hold_time_min": 5,  # minutes
                "hold_time_max": 60,
                "leverage_range": (5, 10),
                "target_profit": 0.01,  # 1-3%
                "stop_loss": 0.005,  # 0.5%
                "market_type": MarketType.FUTURES,
                "conditions": {
                    "min_volatility": 0.02,  # High volatility
                    "min_volume": 1e6,  # High volume
                    "min_liquidity": 0.8  # High liquidity
                }
            },
            TradingStyle.DAY_TRADING: {
                "timeframe": "15m-4h",
                "hold_time_min": 60,  # minutes
                "hold_time_max": 1440,  # 24 hours
                "leverage_range": (3, 5),
                "target_profit": 0.05,  # 5-10%
                "stop_loss": 0.02,  # 2%
                "market_type": MarketType.FUTURES,
                "conditions": {
                    "min_volatility": 0.01,
                    "min_volume": 5e5,
                    "min_liquidity": 0.6
                }
            },
            TradingStyle.SWING_TRADING: {
                "timeframe": "4h-1d",
                "hold_time_min": 1440,  # 24 hours
                "hold_time_max": 10080,  # 7 days
                "leverage_range": (1, 3),
                "target_profit": 0.20,  # 20-50%
                "stop_loss": 0.05,  # 5%
                "market_type": MarketType.SPOT,  # Prefer spot for swing
                "conditions": {
                    "min_volatility": 0.005,
                    "min_volume": 1e5,
                    "min_liquidity": 0.4
                }
            }
        }
        
        logger.info("✅ Adaptive Strategy Engine initialized")
    
    def analyze_opportunity(
        self,
        coin_data: Dict,
        market_data: Dict,
        patterns: List[str],
        agent_consensus: Dict
    ) -> Dict:
        """
        Analyze opportunity and recommend best strategy
        
        Args:
            coin_data: LunarCrush coin data
            market_data: MEXC market data
            patterns: Detected patterns
            agent_consensus: Agent voting results
        
        Returns:
            {
                "trading_style": "scalping" | "day_trading" | "swing_trading",
                "market_type": "spot" | "futures",
                "direction": "LONG" | "SHORT",
                "leverage": 3,
                "target_profit": 0.05,
                "stop_loss": 0.02,
                "hold_time_estimate": 240,  # minutes
                "confidence": 8.5,
                "reasoning": "..."
            }
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        logger.info(f"🎯 Analyzing strategy for {symbol}...")
        
        # Extract market characteristics
        volatility = self._calculate_volatility(coin_data, market_data)
        volume = market_data.get("volume_24h", 0)
        liquidity = self._calculate_liquidity(market_data)
        trend_strength = self._calculate_trend_strength(market_data)
        
        # Determine best trading style
        best_style = self._select_trading_style(
            volatility,
            volume,
            liquidity,
            trend_strength
        )
        
        # Determine direction (LONG or SHORT)
        direction = self._determine_direction(
            coin_data,
            market_data,
            patterns,
            agent_consensus
        )
        
        # Determine market type (SPOT or FUTURES)
        market_type = self._select_market_type(
            best_style,
            direction,
            volatility,
            agent_consensus.get("confidence", 7.0)
        )
        
        # Get strategy config
        strategy_config = self.strategies[best_style]
        
        # Calculate optimal leverage
        leverage = self._calculate_optimal_leverage(
            best_style,
            direction,
            volatility,
            agent_consensus.get("confidence", 7.0)
        )
        
        # Build recommendation
        recommendation = {
            "trading_style": best_style.value,
            "market_type": market_type.value,
            "direction": direction,
            "leverage": leverage,
            "target_profit": strategy_config["target_profit"],
            "stop_loss": strategy_config["stop_loss"],
            "hold_time_estimate": (
                strategy_config["hold_time_min"] + strategy_config["hold_time_max"]
            ) // 2,
            "confidence": agent_consensus.get("confidence", 7.0),
            "reasoning": self._build_reasoning(
                best_style,
                market_type,
                direction,
                volatility,
                trend_strength
            )
        }
        
        logger.info(
            f"✅ Strategy for {symbol}: "
            f"{best_style.value.upper()} {direction} on {market_type.value.upper()} "
            f"({leverage}x leverage)"
        )
        
        return recommendation
    
    def _calculate_volatility(self, coin_data: Dict, market_data: Dict) -> float:
        """Calculate volatility score (0-1)"""
        # Use LunarCrush volatility if available
        lc_volatility = coin_data.get("volatility", 0)
        
        # Use price change as proxy
        price_change_24h = abs(coin_data.get("percent_change_24h", 0)) / 100
        
        # Combine
        volatility = max(lc_volatility, price_change_24h)
        
        return min(1.0, volatility)
    
    def _calculate_liquidity(self, market_data: Dict) -> float:
        """Calculate liquidity score (0-1)"""
        # Based on volume and order book depth
        volume = market_data.get("volume_24h", 0)
        order_book_depth = market_data.get("order_book_depth", 0)
        
        # Normalize (simplified)
        volume_score = min(1.0, volume / 1e7)  # $10M = 1.0
        depth_score = min(1.0, order_book_depth / 1e6)  # $1M = 1.0
        
        return (volume_score + depth_score) / 2
    
    def _calculate_trend_strength(self, market_data: Dict) -> float:
        """Calculate trend strength (0-1)"""
        # Based on price action (simplified)
        # In real implementation, would use technical indicators (EMA, RSI, etc.)
        
        price_change_24h = market_data.get("percent_change_24h", 0) / 100
        
        # Strong trend if >5% move
        trend_strength = min(1.0, abs(price_change_24h) / 0.05)
        
        return trend_strength
    
    def _select_trading_style(
        self,
        volatility: float,
        volume: float,
        liquidity: float,
        trend_strength: float
    ) -> TradingStyle:
        """
        Select best trading style based on market characteristics
        
        Returns:
            Best trading style
        """
        scores = {}
        
        for style, config in self.strategies.items():
            conditions = config["conditions"]
            
            # Check if conditions are met
            score = 0
            
            if volatility >= conditions["min_volatility"]:
                score += 3
            
            if volume >= conditions["min_volume"]:
                score += 3
            
            if liquidity >= conditions["min_liquidity"]:
                score += 2
            
            # Bonus for matching characteristics
            if style == TradingStyle.SCALPING and volatility > 0.02:
                score += 2  # Scalping loves volatility
            
            if style == TradingStyle.SWING_TRADING and trend_strength > 0.5:
                score += 2  # Swing loves strong trends
            
            scores[style] = score
        
        # Select best
        best_style = max(scores, key=scores.get)
        
        return best_style
    
    def _determine_direction(
        self,
        coin_data: Dict,
        market_data: Dict,
        patterns: List[str],
        agent_consensus: Dict
    ) -> str:
        """
        Determine trade direction (LONG or SHORT)
        
        Returns:
            "LONG" or "SHORT"
        """
        # Start with agent consensus
        consensus_decision = agent_consensus.get("decision", "WAIT")
        
        if consensus_decision in ["LONG", "SHORT"]:
            return consensus_decision
        
        # Fallback: Analyze sentiment and price action
        sentiment = coin_data.get("sentiment", 50)
        price_change_24h = coin_data.get("percent_change_24h", 0)
        altrank = coin_data.get("alt_rank", 5000)
        
        # Bullish signals
        bullish_score = 0
        if sentiment > 60:
            bullish_score += 2
        if price_change_24h > 5:
            bullish_score += 2
        if altrank < 500:
            bullish_score += 1
        
        # Bearish signals
        bearish_score = 0
        if sentiment < 40:
            bearish_score += 2
        if price_change_24h < -5:
            bearish_score += 2
        if altrank > 5000:
            bearish_score += 1
        
        # Decide
        if bullish_score > bearish_score:
            return "LONG"
        elif bearish_score > bullish_score:
            return "SHORT"
        else:
            return "LONG"  # Default to LONG
    
    def _select_market_type(
        self,
        trading_style: TradingStyle,
        direction: str,
        volatility: float,
        confidence: float
    ) -> MarketType:
        """
        Select market type (SPOT or FUTURES)
        
        Returns:
            Market type
        """
        # SHORT requires futures
        if direction == "SHORT":
            return MarketType.FUTURES
        
        # High confidence + high volatility = futures
        if confidence > 8.0 and volatility > 0.02:
            return MarketType.FUTURES
        
        # Swing trading prefers spot (safer)
        if trading_style == TradingStyle.SWING_TRADING:
            return MarketType.SPOT
        
        # Scalping requires futures (leverage)
        if trading_style == TradingStyle.SCALPING:
            return MarketType.FUTURES
        
        # Default: futures for day trading
        return MarketType.FUTURES
    
    def _calculate_optimal_leverage(
        self,
        trading_style: TradingStyle,
        direction: str,
        volatility: float,
        confidence: float
    ) -> int:
        """
        Calculate optimal leverage
        
        Returns:
            Leverage (1-10x)
        """
        strategy_config = self.strategies[trading_style]
        min_lev, max_lev = strategy_config["leverage_range"]
        
        # Base leverage on confidence
        leverage = min_lev + (max_lev - min_lev) * (confidence / 10)
        
        # Reduce leverage for high volatility
        if volatility > 0.05:
            leverage *= 0.7
        
        # Reduce leverage for SHORT (riskier)
        if direction == "SHORT":
            leverage *= 0.8
        
        # Round and clamp
        leverage = int(round(leverage))
        leverage = max(1, min(10, leverage))
        
        return leverage
    
    def _build_reasoning(
        self,
        trading_style: TradingStyle,
        market_type: MarketType,
        direction: str,
        volatility: float,
        trend_strength: float
    ) -> str:
        """Build reasoning explanation"""
        
        reasons = []
        
        # Trading style reasoning
        if trading_style == TradingStyle.SCALPING:
            reasons.append(f"High volatility ({volatility:.1%}) suitable for scalping")
        elif trading_style == TradingStyle.SWING_TRADING:
            reasons.append(f"Strong trend ({trend_strength:.1%}) suitable for swing trading")
        else:
            reasons.append("Moderate conditions suitable for day trading")
        
        # Market type reasoning
        if market_type == MarketType.FUTURES:
            if direction == "SHORT":
                reasons.append("Futures required for SHORT position")
            else:
                reasons.append("Futures chosen for leverage opportunity")
        else:
            reasons.append("Spot chosen for safer, longer-term hold")
        
        # Direction reasoning
        if direction == "LONG":
            reasons.append("Bullish signals detected")
        else:
            reasons.append("Bearish signals detected")
        
        return ". ".join(reasons)
    
    def get_strategy_stats(self) -> Dict:
        """Get strategy statistics"""
        return {
            "available_strategies": [s.value for s in TradingStyle],
            "market_types": [m.value for m in MarketType],
            "supports_short": True,
            "supports_leverage": True,
            "max_leverage": 10
        }
