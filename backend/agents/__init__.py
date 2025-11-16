"""
Alpha AI Autotrader - Agents Module
All 9 Alpha Crypto Team agents
"""
from .base_agent import BaseAgent
from .market_analyzer import MarketAnalyzerAgent
from .sentiment_analyzer import SentimentAnalyzerAgent
from .alpha_team import (
    RiskManagerAgent,
    TradingStrategyAgent,
    TradeMonitorAgent,
    OnChainAnalyzerAgent,
    PortfolioOptimizerAgent,
    AlertManagerAgent,
    CryptoResearchAgent
)

__all__ = [
    "BaseAgent",
    "MarketAnalyzerAgent",
    "SentimentAnalyzerAgent",
    "RiskManagerAgent",
    "TradingStrategyAgent",
    "TradeMonitorAgent",
    "OnChainAnalyzerAgent",
    "PortfolioOptimizerAgent",
    "AlertManagerAgent",
    "CryptoResearchAgent"
]
