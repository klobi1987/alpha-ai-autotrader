"""
Alpha AI Autotrader - Claude Agent SDK Client
Replaces OpenRouter with Claude Agent SDK (uses Claude Max subscription)
"""
import os
from typing import Dict, List, Optional
from loguru import logger

try:
    from claude_agent_sdk import ClaudeAgent
    CLAUDE_AGENT_AVAILABLE = True
except ImportError:
    CLAUDE_AGENT_AVAILABLE = False
    logger.warning("Claude Agent SDK not installed. Install with: pip install claude-agent-sdk")


class ClaudeAgentClient:
    """
    Claude Agent SDK Client
    
    Uses Claude Max subscription via ANTHROPIC_API_KEY
    Provides AI-powered analysis for trading decisions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        """
        if not CLAUDE_AGENT_AVAILABLE:
            raise ImportError(
                "Claude Agent SDK not installed. "
                "Install with: pip install claude-agent-sdk"
            )
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env or pass as argument"
            )
        
        # Initialize Claude Agent
        self.agent = ClaudeAgent(
            api_key=self.api_key,
            model="claude-4.5-sonnet-20250514",  # Latest model
            max_tokens=4096,
            temperature=0.7
        )
        
        logger.info("✅ Claude Agent SDK client initialized")
    
    async def analyze_trading_opportunity(
        self,
        coin_data: Dict,
        patterns: List[str],
        agent_votes: Dict,
        market_context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze trading opportunity using Claude Agent SDK
        
        Args:
            coin_data: LunarCrush coin data
            patterns: Detected patterns
            agent_votes: Votes from 9 Alpha Agents
            market_context: Additional market context
        
        Returns:
            {
                "decision": "LONG" | "SHORT" | "WAIT",
                "confidence": 8.5,
                "reasoning": "...",
                "entry_price": 60000,
                "stop_loss": 59200,
                "take_profit": 62500,
                "leverage": 3,
                "position_size": 500
            }
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        logger.info(f"🤖 Claude analyzing {symbol}...")
        
        # Build comprehensive prompt
        prompt = self._build_analysis_prompt(
            coin_data,
            patterns,
            agent_votes,
            market_context
        )
        
        try:
            # Query Claude Agent
            response = await self.agent.query(prompt)
            
            # Parse response
            analysis = self._parse_response(response)
            
            logger.info(
                f"✅ Claude analysis for {symbol}: "
                f"{analysis['decision']} ({analysis['confidence']:.1f}/10)"
            )
            
            return analysis
        
        except Exception as e:
            logger.error(f"Claude Agent analysis failed: {e}")
            
            # Fallback to agent consensus
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": f"Claude analysis failed: {str(e)}",
                "error": str(e)
            }
    
    def _build_analysis_prompt(
        self,
        coin_data: Dict,
        patterns: List[str],
        agent_votes: Dict,
        market_context: Optional[Dict]
    ) -> str:
        """Build comprehensive analysis prompt for Claude"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        # Extract key metrics
        altrank = coin_data.get("alt_rank", 0)
        galaxy_score = coin_data.get("galaxy_score", 0)
        sentiment = coin_data.get("sentiment", 0)
        social_volume = coin_data.get("social_volume_24h", 0)
        price = coin_data.get("price", 0)
        volume_24h = coin_data.get("volume_24h", 0)
        market_cap = coin_data.get("market_cap", 0)
        
        # Agent consensus
        agent_consensus = market_context.get("agent_consensus", {}) if market_context else {}
        consensus_decision = agent_consensus.get("decision", "UNKNOWN")
        consensus_confidence = agent_consensus.get("confidence", 0)
        agreement_rate = agent_consensus.get("agreement_rate", 0)
        
        prompt = f"""You are an expert cryptocurrency trader analyzing a trading opportunity.

**Coin**: {symbol}

**LunarCrush Social Metrics**:
- AltRank: {altrank} (1-10000, lower is better)
- Galaxy Score: {galaxy_score}/100 (overall quality)
- Sentiment: {sentiment}/100 (bullish/bearish)
- Social Volume 24h: {social_volume:,} posts
- Price: ${price:,.2f}
- Volume 24h: ${volume_24h:,.0f}
- Market Cap: ${market_cap:,.0f}

**Detected Patterns**:
{self._format_patterns(patterns)}

**Alpha Agents Consensus**:
- Decision: {consensus_decision}
- Confidence: {consensus_confidence:.1f}/10
- Agreement Rate: {agreement_rate:.0%}

**Individual Agent Votes**:
{self._format_agent_votes(agent_votes)}

**Your Task**:
Analyze this trading opportunity and provide your expert opinion.

Consider:
1. Social metrics (AltRank, Galaxy Score, sentiment)
2. Detected patterns (strength, reliability)
3. Agent consensus (do you agree?)
4. Risk/reward ratio
5. Current market conditions

Provide your analysis in this format:

DECISION: [LONG/SHORT/WAIT]
CONFIDENCE: [0-10]
REASONING: [Your detailed reasoning]
ENTRY_PRICE: [Recommended entry price]
STOP_LOSS: [Stop-loss price]
TAKE_PROFIT: [Take-profit target]
LEVERAGE: [1-5x recommended leverage]
POSITION_SIZE: [Recommended position size in USD]

Be specific, analytical, and conservative. Only recommend LONG/SHORT if confidence >7.5/10.
"""
        
        return prompt
    
    def _format_patterns(self, patterns: List[str]) -> str:
        """Format patterns for prompt"""
        if not patterns:
            return "- No patterns detected"
        
        return "\n".join(f"- {pattern}" for pattern in patterns)
    
    def _format_agent_votes(self, agent_votes: Dict) -> str:
        """Format agent votes for prompt"""
        if not agent_votes:
            return "- No agent votes available"
        
        lines = []
        for agent_name, vote in agent_votes.items():
            decision = vote.get("decision", "UNKNOWN")
            confidence = vote.get("confidence", 0)
            reasoning = vote.get("reasoning", "")[:100]  # Truncate
            
            lines.append(
                f"- {agent_name}: {decision} ({confidence:.1f}/10) - {reasoning}"
            )
        
        return "\n".join(lines)
    
    def _parse_response(self, response: str) -> Dict:
        """Parse Claude's response into structured format"""
        
        # Default values
        result = {
            "decision": "WAIT",
            "confidence": 5.0,
            "reasoning": "",
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "leverage": 1,
            "position_size": 100
        }
        
        # Parse response line by line
        lines = response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip().upper()
                if decision in ["LONG", "SHORT", "WAIT"]:
                    result["decision"] = decision
            
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                    result["confidence"] = max(0, min(10, confidence))
                except:
                    pass
            
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
            
            elif line.startswith("ENTRY_PRICE:"):
                try:
                    result["entry_price"] = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                except:
                    pass
            
            elif line.startswith("STOP_LOSS:"):
                try:
                    result["stop_loss"] = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                except:
                    pass
            
            elif line.startswith("TAKE_PROFIT:"):
                try:
                    result["take_profit"] = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                except:
                    pass
            
            elif line.startswith("LEVERAGE:"):
                try:
                    leverage = line.split(":", 1)[1].strip().replace("x", "")
                    result["leverage"] = int(float(leverage))
                except:
                    pass
            
            elif line.startswith("POSITION_SIZE:"):
                try:
                    result["position_size"] = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                except:
                    pass
        
        return result
    
    async def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Chat with Claude Agent
        
        Args:
            message: User message
            context: Optional context (portfolio, positions, etc.)
        
        Returns:
            Claude's response
        """
        try:
            # Build prompt with context
            if context:
                prompt = f"""Context:
{self._format_context(context)}

User: {message}
"""
            else:
                prompt = message
            
            # Query Claude
            response = await self.agent.query(prompt)
            
            return response
        
        except Exception as e:
            logger.error(f"Claude chat failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _format_context(self, context: Dict) -> str:
        """Format context for chat"""
        lines = []
        
        if "portfolio" in context:
            lines.append(f"Portfolio Value: ${context['portfolio'].get('total_value', 0):,.2f}")
        
        if "open_positions" in context:
            positions = context["open_positions"]
            lines.append(f"Open Positions: {len(positions)}")
            
            for pos in positions:
                symbol = pos.get("symbol", "UNKNOWN")
                pnl = pos.get("pnl", 0)
                lines.append(f"  - {symbol}: ${pnl:,.2f} P&L")
        
        if "recent_trades" in context:
            trades = context["recent_trades"]
            lines.append(f"Recent Trades: {len(trades)}")
        
        return "\n".join(lines)
