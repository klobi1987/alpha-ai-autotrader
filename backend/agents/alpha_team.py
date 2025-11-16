"""
Alpha AI Autotrader - Complete Alpha Crypto Team (7 remaining agents)
Compact implementation of all specialized agents
"""
from typing import Dict, Optional, List
from .base_agent import BaseAgent
import numpy as np


class RiskManagerAgent(BaseAgent):
    """Risk Management Specialist"""
    
    def __init__(self):
        super().__init__(
            name="risk-manager",
            role="Risk Management & Position Sizing"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Assess risk and determine position sizing"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        price = coin_data.get("price", 0)
        volatility = coin_data.get("volatility", 0)
        
        # Get portfolio context
        portfolio_value = context.get("portfolio_value", 10000) if context else 10000
        open_positions = context.get("open_positions", 0) if context else 0
        max_positions = context.get("max_positions", 3) if context else 3
        max_position_size = context.get("max_position_size_usd", 500) if context else 500
        
        warnings = []
        confidence = 7.0
        decision = "APPROVED"
        
        # Check portfolio capacity
        if open_positions >= max_positions:
            return {
                "decision": "REJECTED",
                "confidence": 0.0,
                "reasoning": f"Max positions reached ({open_positions}/{max_positions})",
                "warnings": ["Portfolio full"]
            }
        
        # Volatility risk assessment
        if volatility > 0.20:  # >20% volatility
            warnings.append(f"High volatility ({volatility:.1%})")
            confidence -= 1.5
            max_position_size *= 0.5  # Reduce position size
        
        # Calculate recommended position size
        risk_per_trade = portfolio_value * 0.02  # 2% risk per trade
        stop_loss_pct = 0.02  # 2% stop loss
        
        position_size_usd = min(
            risk_per_trade / stop_loss_pct,
            max_position_size
        )
        
        # Recommended leverage
        if volatility < 0.05:
            recommended_leverage = 5
        elif volatility < 0.10:
            recommended_leverage = 3
        else:
            recommended_leverage = 1
            warnings.append("High volatility - no leverage recommended")
        
        # Risk/reward calculation
        risk_reward_ratio = 2.5  # Target 2.5:1
        
        reasoning = f"Position size: ${position_size_usd:.2f} | Leverage: {recommended_leverage}x | R:R: {risk_reward_ratio}:1"
        if warnings:
            reasoning += " | ⚠️ " + ", ".join(warnings)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators": {
                "position_size_usd": position_size_usd,
                "recommended_leverage": recommended_leverage,
                "stop_loss_pct": stop_loss_pct,
                "risk_reward_ratio": risk_reward_ratio
            },
            "warnings": warnings
        }


class TradingStrategyAgent(BaseAgent):
    """Pattern Recognition & Strategy Specialist"""
    
    def __init__(self):
        super().__init__(
            name="trading-strategy-agent",
            role="Pattern Recognition & Entry/Exit Strategy"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Identify patterns and recommend strategy"""
        
        from ..core.patterns import PatternDetector
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        price = coin_data.get("price", 0)
        
        # Get OHLCV data if available
        ohlcv = market_data.get("ohlcv", []) if market_data else []
        
        # Detect patterns
        detector = PatternDetector()
        patterns = detector.detect_all_patterns(coin_data, ohlcv)
        
        if not patterns:
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": "No clear patterns detected",
                "indicators": {"patterns_found": 0}
            }
        
        # Calculate confluence
        confluence_score = detector.calculate_confluence_score(patterns)
        
        # Determine decision based on patterns
        long_patterns = [p for p in patterns if p.get("direction") == "LONG"]
        short_patterns = [p for p in patterns if p.get("direction") == "SHORT"]
        
        if len(long_patterns) > len(short_patterns):
            decision = "LONG"
            confidence = confluence_score
        elif len(short_patterns) > len(long_patterns):
            decision = "SHORT"
            confidence = confluence_score
        else:
            decision = "WAIT"
            confidence = 5.0
        
        # Best pattern
        best_pattern = max(patterns, key=lambda x: x.get("confidence", 0))
        
        reasoning = f"{len(patterns)} patterns detected | Best: {best_pattern['pattern_name']} ({best_pattern['confidence']:.1f}/10)"
        
        # Entry/exit levels (simplified)
        entry_price = price
        stop_loss = price * 0.98 if decision == "LONG" else price * 1.02
        take_profit = price * 1.05 if decision == "LONG" else price * 0.95
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators": {
                "patterns_found": len(patterns),
                "confluence_score": confluence_score,
                "best_pattern": best_pattern["pattern_name"],
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            },
            "patterns": patterns
        }


class TradeMonitorAgent(BaseAgent):
    """Live Position Monitoring Specialist"""
    
    def __init__(self):
        super().__init__(
            name="trade-monitor-agent",
            role="Live Position Management & Monitoring"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Monitor open position and recommend actions"""
        
        if not context or "position" not in context:
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": "No position to monitor"
            }
        
        position = context["position"]
        entry_price = position.get("entry_price", 0)
        current_price = coin_data.get("price", 0)
        stop_loss = position.get("stop_loss", 0)
        take_profit = position.get("take_profit", 0)
        side = position.get("side", "LONG")
        
        # Calculate P&L
        if side == "LONG":
            pnl_pct = (current_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - current_price) / entry_price * 100
        
        decision = "HOLD"
        confidence = 7.0
        reasoning_parts = []
        
        # Check stop loss
        if (side == "LONG" and current_price <= stop_loss) or \
           (side == "SHORT" and current_price >= stop_loss):
            decision = "CLOSE"
            confidence = 10.0
            reasoning_parts.append(f"Stop loss hit at ${current_price:.6f}")
        
        # Check take profit
        elif (side == "LONG" and current_price >= take_profit) or \
             (side == "SHORT" and current_price <= take_profit):
            decision = "CLOSE"
            confidence = 9.0
            reasoning_parts.append(f"Take profit hit at ${current_price:.6f}")
        
        # Move to break-even
        elif pnl_pct > 5.0 and stop_loss < entry_price:
            decision = "ADJUST_SL"
            confidence = 8.0
            reasoning_parts.append(f"Profit {pnl_pct:.1f}% - move SL to break-even")
        
        # Trailing stop
        elif pnl_pct > 10.0:
            decision = "ADJUST_SL"
            confidence = 8.0
            new_sl = current_price * 0.95 if side == "LONG" else current_price * 1.05
            reasoning_parts.append(f"Profit {pnl_pct:.1f}% - trailing stop to ${new_sl:.6f}")
        
        else:
            reasoning_parts.append(f"Position P&L: {pnl_pct:+.2f}%")
        
        reasoning = " | ".join(reasoning_parts)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators": {
                "pnl_pct": pnl_pct,
                "current_price": current_price,
                "entry_price": entry_price
            }
        }


class OnChainAnalyzerAgent(BaseAgent):
    """On-Chain Metrics Specialist (Future Feature)"""
    
    def __init__(self):
        super().__init__(
            name="onchain-analyzer",
            role="On-Chain Metrics & Whale Tracking"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze on-chain metrics (placeholder for future implementation)"""
        
        # Placeholder - future integration with Glassnode, Dune Analytics, etc.
        return {
            "decision": "WAIT",
            "confidence": 5.0,
            "reasoning": "On-chain analysis not yet implemented",
            "indicators": {}
        }


class PortfolioOptimizerAgent(BaseAgent):
    """Portfolio Balance & Optimization Specialist"""
    
    def __init__(self):
        super().__init__(
            name="portfolio-optimizer",
            role="Portfolio Balance & Diversification"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze portfolio balance and diversification"""
        
        if not context:
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": "No portfolio context provided"
            }
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        open_positions = context.get("open_positions_list", [])
        portfolio_value = context.get("portfolio_value", 10000)
        
        # Check if already have position in this coin
        existing_position = any(p.get("symbol") == symbol for p in open_positions)
        if existing_position:
            return {
                "decision": "REJECTED",
                "confidence": 0.0,
                "reasoning": f"Already have position in {symbol}",
                "warnings": ["Duplicate position"]
            }
        
        # Check portfolio concentration
        if len(open_positions) >= 3:
            return {
                "decision": "WAIT",
                "confidence": 6.0,
                "reasoning": "Portfolio at capacity - wait for position to close",
                "warnings": ["Max positions reached"]
            }
        
        # Check correlation (simplified - future: use actual correlation data)
        # For now, just check if we have too many similar coins
        categories = [p.get("category", "") for p in open_positions]
        coin_category = coin_data.get("categories", [""])[0] if coin_data.get("categories") else ""
        
        if coin_category and categories.count(coin_category) >= 2:
            return {
                "decision": "WAIT",
                "confidence": 6.0,
                "reasoning": f"Too many {coin_category} positions - diversify",
                "warnings": ["Correlation risk"]
            }
        
        return {
            "decision": "APPROVED",
            "confidence": 7.5,
            "reasoning": f"Portfolio balanced - OK to add {symbol}",
            "indicators": {
                "open_positions": len(open_positions),
                "portfolio_concentration": len(open_positions) / 3 * 100
            }
        }


class AlertManagerAgent(BaseAgent):
    """Alert & Notification Specialist"""
    
    def __init__(self):
        super().__init__(
            name="alert-manager",
            role="Alert & Notification Management"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Determine if alerts should be sent"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        alerts = []
        
        # High confidence signal
        confidence = context.get("consensus_confidence", 0) if context else 0
        if confidence >= 8.5:
            alerts.append(f"🚀 HIGH CONFIDENCE signal for {symbol} ({confidence:.1f}/10)")
        
        # Extreme sentiment
        sentiment = coin_data.get("sentiment", 50)
        if sentiment > 90:
            alerts.append(f"⚠️ {symbol} extreme greed (sentiment: {sentiment}/100)")
        elif sentiment < 20:
            alerts.append(f"💎 {symbol} extreme fear (sentiment: {sentiment}/100)")
        
        # Big AltRank jump
        alt_rank_change = coin_data.get("alt_rank_change", 0)
        if alt_rank_change > 500:
            alerts.append(f"📈 {symbol} AltRank surge +{alt_rank_change}")
        
        # Position P&L alerts
        if context and "position" in context:
            position = context["position"]
            pnl_pct = position.get("pnl_pct", 0)
            
            if pnl_pct > 10:
                alerts.append(f"💰 {symbol} profit +{pnl_pct:.1f}%")
            elif pnl_pct < -5:
                alerts.append(f"⚠️ {symbol} loss {pnl_pct:.1f}%")
        
        if alerts:
            return {
                "decision": "ALERT",
                "confidence": 8.0,
                "reasoning": " | ".join(alerts),
                "indicators": {"alert_count": len(alerts)},
                "alerts": alerts
            }
        
        return {
            "decision": "WAIT",
            "confidence": 5.0,
            "reasoning": "No alerts triggered"
        }


class CryptoResearchAgent(BaseAgent):
    """Deep Research & Web Surfing Specialist"""
    
    def __init__(self):
        super().__init__(
            name="crypto-research-agent",
            role="Deep Research & Fundamental Analysis"
        )
    
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Conduct deep research (web surfing when needed)"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        confidence = context.get("consensus_confidence", 0) if context else 0
        
        # Only surf web for high-confidence signals (>8.0)
        should_research = confidence > 8.0
        
        if not should_research:
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": "Confidence too low for deep research"
            }
        
        # Placeholder for web surfing implementation
        # Future: Integrate with BeautifulSoup, Selenium, or Playwright
        # to scrape CoinGecko, Twitter, Reddit, etc.
        
        research_findings = []
        
        # Check if coin is in top 100 (reliable)
        market_cap_rank = coin_data.get("market_cap_rank", 999)
        if market_cap_rank <= 100:
            research_findings.append(f"Top {market_cap_rank} by market cap (reliable)")
        
        # Check categories
        categories = coin_data.get("categories", [])
        if categories:
            research_findings.append(f"Categories: {', '.join(categories[:3])}")
        
        # Galaxy Score as proxy for fundamentals
        galaxy = coin_data.get("galaxy_score", 0)
        if galaxy > 70:
            research_findings.append(f"Strong fundamentals (Galaxy: {galaxy}/100)")
        elif galaxy < 40:
            research_findings.append(f"⚠️ Weak fundamentals (Galaxy: {galaxy}/100)")
        
        if research_findings:
            return {
                "decision": "APPROVED",
                "confidence": 7.0,
                "reasoning": " | ".join(research_findings),
                "indicators": {"research_items": len(research_findings)}
            }
        
        return {
            "decision": "WAIT",
            "confidence": 5.0,
            "reasoning": "Insufficient research data"
        }
