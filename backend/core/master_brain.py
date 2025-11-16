"""
Alpha AI Autotrader - Master AI Brain
Orchestrates all 9 Alpha Agents and makes final decisions
"""
from typing import Dict, List, Optional
from loguru import logger
from collections import Counter

from ..agents import (
    MarketAnalyzerAgent,
    SentimentAnalyzerAgent,
    RiskManagerAgent,
    TradingStrategyAgent,
    TradeMonitorAgent,
    OnChainAnalyzerAgent,
    PortfolioOptimizerAgent,
    AlertManagerAgent,
    CryptoResearchAgent
)
from ..integrations.openrouter_client import OpenRouterClient


class MasterAIBrain:
    """
    Master AI Brain - Orchestrator of Alpha Crypto Team
    
    Workflow:
    1. Receive filtered candidates (5-10 coins)
    2. Each of 9 agents analyzes and votes
    3. Calculate agent consensus
    4. If high confidence (>7.5), ask Multi-AI for second opinion
    5. Make final decision based on all inputs
    6. Execute or reject trade
    
    Decision making:
    - Agent votes (weight: 60%)
    - Multi-AI consensus (weight: 40%)
    - Minimum confidence threshold: 7.5/10
    - Minimum agreement rate: 66% (2/3 agents agree)
    """
    
    def __init__(
        self,
        openrouter_api_key: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Args:
            openrouter_api_key: OpenRouter API key for multi-AI consensus
            config: Configuration dict
        """
        self.config = config or self._default_config()
        
        # Initialize all 9 Alpha Agents
        self.agents = {
            "market_analyzer": MarketAnalyzerAgent(),
            "sentiment_analyzer": SentimentAnalyzerAgent(),
            "risk_manager": RiskManagerAgent(),
            "strategy_agent": TradingStrategyAgent(),
            "trade_monitor": TradeMonitorAgent(),
            "onchain_analyzer": OnChainAnalyzerAgent(),
            "portfolio_optimizer": PortfolioOptimizerAgent(),
            "alert_manager": AlertManagerAgent(),
            "research_agent": CryptoResearchAgent()
        }
        
        # Initialize OpenRouter client (optional)
        self.openrouter = None
        if openrouter_api_key:
            self.openrouter = OpenRouterClient(openrouter_api_key)
        
        # Stats
        self.total_decisions = 0
        self.decisions_history = []
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "min_confidence": 7.5,
            "min_agreement_rate": 0.66,
            "enable_multi_ai": True,
            "multi_ai_threshold": 7.5,
            "agent_weight": 0.6,
            "multi_ai_weight": 0.4
        }
    
    def analyze_candidate(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a trading candidate through all agents
        
        Args:
            coin_data: LunarCrush coin data
            market_data: MEXC market data
            context: Additional context (portfolio, positions, etc.)
        
        Returns:
            {
                "symbol": "BTC",
                "decision": "LONG" | "SHORT" | "WAIT" | "REJECTED",
                "confidence": 8.5,
                "reasoning": "...",
                "agent_votes": [...],
                "multi_ai_consensus": {...},
                "final_recommendation": {...}
            }
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        logger.info(f"🧠 Master Brain analyzing {symbol}...")
        
        # Step 1: Collect votes from all agents
        agent_votes = self._collect_agent_votes(coin_data, market_data, context)
        
        # Step 2: Calculate agent consensus
        agent_consensus = self._calculate_agent_consensus(agent_votes)
        
        # Step 3: Check if Multi-AI consensus is needed
        multi_ai_consensus = None
        if (self.config["enable_multi_ai"] and 
            self.openrouter and 
            agent_consensus["confidence"] >= self.config["multi_ai_threshold"]):
            
            logger.info(f"🤖 High confidence ({agent_consensus['confidence']:.1f}) - requesting Multi-AI consensus...")
            
            try:
                # Get patterns from strategy agent
                strategy_vote = next(
                    (v for v in agent_votes if v["agent"] == "trading-strategy-agent"),
                    {}
                )
                patterns = strategy_vote.get("patterns", [])
                
                multi_ai_consensus = self.openrouter.get_consensus(
                    coin_data,
                    patterns,
                    market_context={"agent_consensus": agent_consensus}
                )
            except Exception as e:
                logger.error(f"Multi-AI consensus failed: {e}")
                multi_ai_consensus = None
        
        # Step 4: Make final decision
        final_decision = self._make_final_decision(
            agent_consensus,
            multi_ai_consensus
        )
        
        # Step 5: Build result
        result = {
            "symbol": symbol,
            "decision": final_decision["decision"],
            "confidence": final_decision["confidence"],
            "reasoning": final_decision["reasoning"],
            "agent_votes": agent_votes,
            "agent_consensus": agent_consensus,
            "multi_ai_consensus": multi_ai_consensus,
            "final_recommendation": final_decision.get("recommendation", {})
        }
        
        # Update stats
        self.total_decisions += 1
        self.decisions_history.append(result)
        
        logger.info(
            f"✅ Master Brain decision for {symbol}: "
            f"{final_decision['decision']} ({final_decision['confidence']:.1f}/10)"
        )
        
        return result
    
    def _collect_agent_votes(
        self,
        coin_data: Dict,
        market_data: Optional[Dict],
        context: Optional[Dict]
    ) -> List[Dict]:
        """Collect votes from all agents"""
        votes = []
        
        for agent_name, agent in self.agents.items():
            try:
                vote = agent.vote(coin_data, market_data, context)
                votes.append(vote)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                continue
        
        return votes
    
    def _calculate_agent_consensus(self, votes: List[Dict]) -> Dict:
        """
        Calculate consensus from agent votes
        
        Returns:
            {
                "decision": "LONG" | "SHORT" | "WAIT",
                "confidence": 8.2,
                "agreement_rate": 0.75,
                "votes_summary": {...}
            }
        """
        if not votes:
            return {
                "decision": "WAIT",
                "confidence": 0.0,
                "agreement_rate": 0.0,
                "votes_summary": {}
            }
        
        # Extract decisions and confidences
        decisions = [v.get("decision", "WAIT") for v in votes]
        confidences = [v.get("confidence", 5.0) for v in votes]
        
        # Most common decision
        decision_counts = Counter(decisions)
        consensus_decision = decision_counts.most_common(1)[0][0]
        
        # Agreement rate
        agreement_rate = decision_counts[consensus_decision] / len(votes)
        
        # Average confidence (only from agents that agree)
        agreeing_votes = [
            v for v in votes
            if v.get("decision") == consensus_decision
        ]
        avg_confidence = (
            sum(v.get("confidence", 5.0) for v in agreeing_votes) / len(agreeing_votes)
            if agreeing_votes else 5.0
        )
        
        # Votes summary
        votes_summary = {}
        for vote in votes:
            agent = vote.get("agent", "unknown")
            votes_summary[agent] = {
                "decision": vote.get("decision", "WAIT"),
                "confidence": vote.get("confidence", 5.0),
                "reasoning": vote.get("reasoning", "")
            }
        
        return {
            "decision": consensus_decision,
            "confidence": avg_confidence,
            "agreement_rate": agreement_rate,
            "votes_summary": votes_summary,
            "total_votes": len(votes)
        }
    
    def _make_final_decision(
        self,
        agent_consensus: Dict,
        multi_ai_consensus: Optional[Dict]
    ) -> Dict:
        """
        Make final decision combining agent and multi-AI consensus
        
        Decision logic:
        - If no multi-AI: Use agent consensus
        - If multi-AI available: Weighted average
        - Check minimum thresholds (confidence, agreement rate)
        """
        agent_decision = agent_consensus["decision"]
        agent_confidence = agent_consensus["confidence"]
        agreement_rate = agent_consensus["agreement_rate"]
        
        # If no multi-AI consensus, use agent consensus
        if not multi_ai_consensus:
            final_confidence = agent_confidence
            final_decision = agent_decision
            reasoning = f"Agent consensus: {agent_decision} ({agent_confidence:.1f}/10, {agreement_rate:.0%} agreement)"
        
        else:
            # Weighted average
            multi_ai_decision = multi_ai_consensus["consensus_decision"]
            multi_ai_confidence = multi_ai_consensus["consensus_confidence"]
            
            # Check if agents and AI agree
            if agent_decision == multi_ai_decision:
                # Agreement - boost confidence
                final_confidence = (
                    agent_confidence * self.config["agent_weight"] +
                    multi_ai_confidence * self.config["multi_ai_weight"]
                )
                final_decision = agent_decision
                reasoning = f"Strong consensus: Agents + AI agree on {final_decision} ({final_confidence:.1f}/10)"
            
            else:
                # Disagreement - reduce confidence
                final_confidence = min(agent_confidence, multi_ai_confidence) * 0.7
                final_decision = "WAIT"
                reasoning = f"Disagreement: Agents say {agent_decision}, AI says {multi_ai_decision} - WAIT"
        
        # Apply minimum thresholds
        if final_confidence < self.config["min_confidence"]:
            final_decision = "WAIT"
            reasoning += f" | Confidence too low ({final_confidence:.1f} < {self.config['min_confidence']})"
        
        if agreement_rate < self.config["min_agreement_rate"]:
            final_decision = "WAIT"
            reasoning += f" | Agreement too low ({agreement_rate:.0%} < {self.config['min_agreement_rate']:.0%})"
        
        # Check for REJECTED votes (from risk manager or portfolio optimizer)
        rejected_votes = [
            v for v in agent_consensus.get("votes_summary", {}).values()
            if v["decision"] == "REJECTED"
        ]
        
        if rejected_votes:
            final_decision = "REJECTED"
            reasoning = rejected_votes[0]["reasoning"]
        
        return {
            "decision": final_decision,
            "confidence": final_confidence,
            "reasoning": reasoning,
            "recommendation": {
                "agent_consensus": agent_consensus,
                "multi_ai_consensus": multi_ai_consensus
            }
        }
    
    def get_stats(self) -> Dict:
        """Get Master Brain statistics"""
        if not self.decisions_history:
            return {
                "total_decisions": 0,
                "decisions_breakdown": {},
                "avg_confidence": 0.0
            }
        
        decisions = [d["decision"] for d in self.decisions_history]
        confidences = [d["confidence"] for d in self.decisions_history]
        
        return {
            "total_decisions": self.total_decisions,
            "decisions_breakdown": dict(Counter(decisions)),
            "avg_confidence": sum(confidences) / len(confidences),
            "agent_stats": {
                name: agent.get_stats()
                for name, agent in self.agents.items()
            }
        }
