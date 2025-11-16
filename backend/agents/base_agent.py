"""
Alpha AI Autotrader - Base Agent Class
All Alpha Crypto Team agents inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from loguru import logger


class BaseAgent(ABC):
    """
    Base class for all Alpha Crypto Team agents
    
    Each agent has:
    - Specific role and expertise
    - Analysis method
    - Confidence scoring
    - Reasoning explanation
    """
    
    def __init__(self, name: str, role: str):
        """
        Args:
            name: Agent name (e.g., "crypto-market-analyzer")
            role: Agent role description
        """
        self.name = name
        self.role = role
        self.analysis_count = 0
        self.avg_confidence = 0.0
    
    @abstractmethod
    def analyze(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze data and provide recommendation
        
        Args:
            coin_data: LunarCrush coin data
            market_data: MEXC market data (price, volume, etc.)
            context: Additional context
        
        Returns:
            {
                "agent": "agent_name",
                "decision": "LONG" | "SHORT" | "WAIT",
                "confidence": 0-10,
                "reasoning": "explanation",
                "indicators": {...},
                "warnings": [...]
            }
        """
        pass
    
    def vote(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Cast a vote on a trading decision
        
        Wrapper around analyze() that adds metadata
        """
        try:
            analysis = self.analyze(coin_data, market_data, context)
            
            # Update stats
            self.analysis_count += 1
            confidence = analysis.get("confidence", 5.0)
            self.avg_confidence = (
                (self.avg_confidence * (self.analysis_count - 1) + confidence)
                / self.analysis_count
            )
            
            # Add metadata
            analysis["agent"] = self.name
            analysis["role"] = self.role
            
            logger.info(
                f"{self.name} vote: {analysis.get('decision', 'WAIT')} "
                f"({confidence:.1f}/10)"
            )
            
            return analysis
        
        except Exception as e:
            logger.error(f"{self.name} analysis failed: {e}")
            return {
                "agent": self.name,
                "decision": "WAIT",
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "error": True
            }
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            "name": self.name,
            "role": self.role,
            "analysis_count": self.analysis_count,
            "avg_confidence": self.avg_confidence
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
