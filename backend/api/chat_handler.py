"""
Alpha AI Autotrader - Chat Handler
Real-time communication with Claude AI Brain
"""
from typing import Dict, List, Optional
from loguru import logger
import asyncio
from datetime import datetime

from backend.integrations.claude_agent_client import ClaudeAgentClient
from backend.core.master_brain_v2 import MasterAIBrain


class ChatHandler:
    """
    Chat Handler - Real-time communication with Claude
    
    Features:
    - User can ask Claude anything
    - Claude explains decisions
    - Claude gives trading advice
    - Claude learns from user feedback
    - Streaming responses (real-time typing)
    """
    
    def __init__(
        self,
        claude_client: ClaudeAgentClient,
        master_brain: MasterAIBrain
    ):
        """
        Args:
            claude_client: Claude Agent SDK client
            master_brain: Master AI Brain instance
        """
        self.claude = claude_client
        self.brain = master_brain
        self.conversation_history: List[Dict] = []
        
        logger.info("✅ Chat Handler initialized")
    
    async def handle_user_message(
        self,
        message: str,
        user_id: str = "default"
    ) -> Dict:
        """
        Handle user message and get Claude's response
        
        Args:
            message: User's message
            user_id: User identifier
        
        Returns:
            {
                "response": str,
                "timestamp": str,
                "context": dict (optional)
            }
        """
        logger.info(f"💬 User message: {message}")
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build context for Claude
        context = await self._build_context()
        
        # Create prompt for Claude
        prompt = self._create_prompt(message, context)
        
        # Get Claude's response
        try:
            response = await self.claude.chat(
                messages=self.conversation_history[-10:],  # Last 10 messages
                system_prompt=self._get_system_prompt(),
                max_tokens=1000
            )
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"🤖 Claude response: {response[:100]}...")
            
            return {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "context": context
            }
        
        except Exception as e:
            logger.error(f"Failed to get Claude response: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
    
    async def stream_response(
        self,
        message: str,
        user_id: str = "default"
    ):
        """
        Stream Claude's response in real-time (typing effect)
        
        Yields:
            str: Chunks of response text
        """
        logger.info(f"💬 Streaming response for: {message}")
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build context
        context = await self._build_context()
        
        # Stream from Claude
        try:
            full_response = ""
            
            async for chunk in self.claude.stream_chat(
                messages=self.conversation_history[-10:],
                system_prompt=self._get_system_prompt()
            ):
                full_response += chunk
                yield chunk
            
            # Add complete response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n\n[Error: {str(e)}]"
    
    async def _build_context(self) -> Dict:
        """
        Build current context for Claude
        
        Returns:
            {
                "portfolio": {...},
                "open_positions": [...],
                "recent_signals": [...],
                "agent_status": {...},
                "market_overview": {...}
            }
        """
        context = {}
        
        try:
            # Portfolio info
            context["portfolio"] = {
                "total_value": 10000,  # TODO: Get from DB
                "available_balance": 5000,
                "exposure_pct": 50
            }
            
            # Open positions
            context["open_positions"] = []  # TODO: Get from DB
            
            # Recent signals
            context["recent_signals"] = []  # TODO: Get from DB
            
            # Agent status
            context["agent_status"] = {
                "total_agents": 9,
                "active_agents": 9,
                "last_scan": datetime.now().isoformat()
            }
            
            # Market overview
            context["market_overview"] = {
                "trending_coins": [],  # TODO: Get from LunarCrush
                "market_sentiment": "neutral"
            }
        
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
        
        return context
    
    def _create_prompt(self, message: str, context: Dict) -> str:
        """Create prompt for Claude with context"""
        
        prompt = f"""
User Question: {message}

Current Context:
- Portfolio Value: ${context.get('portfolio', {}).get('total_value', 0):,}
- Open Positions: {len(context.get('open_positions', []))}
- Exposure: {context.get('portfolio', {}).get('exposure_pct', 0)}%
- Active Agents: {context.get('agent_status', {}).get('active_agents', 0)}/9

Please provide a helpful, detailed response.
"""
        
        return prompt.strip()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Claude"""
        
        return """
You are Claude, the AI Brain of the Alpha AI Autotrader system.

Your role:
- Autonomous crypto trader (you make ALL trading decisions)
- Advisor to the user (explain decisions, give insights)
- Teacher (help user understand crypto trading)
- Learner (adapt based on user feedback)

Your personality:
- Professional but friendly
- Confident but humble
- Transparent (always explain your reasoning)
- Honest about risks and uncertainties

Your capabilities:
- Analyze 1000+ coins from LunarCrush
- Execute trades on MEXC (spot + futures)
- Manage 9 specialized AI agents
- Learn from results (ML + memory)
- Research the web when needed

Current mode: AUTONOMOUS
- You trade automatically based on your analysis
- User can ask questions, give suggestions, or override decisions
- You explain every decision you make

When responding:
- Be concise but informative
- Use emojis sparingly (only when appropriate)
- Provide actionable insights
- Admit when you don't know something
- Ask for clarification if needed

Remember: You're not just a chatbot - you're an autonomous trader with real money at stake.
Be responsible, transparent, and always prioritize risk management.
"""
    
    def get_conversation_history(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-limit:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("🗑️ Conversation history cleared")
    
    async def explain_decision(
        self,
        decision: Dict
    ) -> str:
        """
        Ask Claude to explain a trading decision
        
        Args:
            decision: Trading decision dict
        
        Returns:
            Explanation string
        """
        prompt = f"""
Please explain this trading decision in detail:

Symbol: {decision.get('symbol')}
Decision: {decision.get('action')} ({decision.get('market')})
Confidence: {decision.get('confidence')}/10
Entry: ${decision.get('entry_price')}
Stop-Loss: ${decision.get('stop_loss')}
Take-Profit: ${decision.get('take_profit')}
Leverage: {decision.get('leverage')}x

Why did you make this decision?
What signals did you see?
What are the risks?
What's your expected outcome?
"""
        
        try:
            response = await self.claude.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self._get_system_prompt(),
                max_tokens=500
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to explain decision: {e}")
            return f"Error explaining decision: {str(e)}"
    
    async def get_trading_advice(
        self,
        symbol: str,
        user_question: Optional[str] = None
    ) -> str:
        """
        Get Claude's trading advice for a specific coin
        
        Args:
            symbol: Coin symbol (e.g., "BTC")
            user_question: Optional specific question
        
        Returns:
            Trading advice
        """
        prompt = f"""
The user is asking about {symbol}.

{f"Specific question: {user_question}" if user_question else ""}

Please provide:
1. Current analysis of {symbol}
2. Trading recommendation (LONG/SHORT/WAIT)
3. Reasoning
4. Risk assessment
5. Entry/SL/TP suggestions (if applicable)

Be honest if you don't have enough data to make a recommendation.
"""
        
        try:
            response = await self.claude.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self._get_system_prompt(),
                max_tokens=800
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to get trading advice: {e}")
            return f"Error getting advice: {str(e)}"
