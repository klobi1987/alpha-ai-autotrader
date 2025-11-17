"""
Alpha AI Autotrader - Master AI Brain V2
Claude as the primary decision maker with 9 agents as data collectors
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime

from ..integrations.claude_agent_client import ClaudeAgentClient
from ..integrations.lunarcrush import LunarCrushClient
from ..integrations.mexc_client import MEXCClient
from ..agents.alpha_team import (
    MarketAnalyzer,
    SentimentAnalyzer,
    RiskManager,
    TradingStrategyAgent,
    TradeMonitorAgent,
    OnChainAnalyzer,
    PortfolioOptimizer,
    AlertManager,
    CryptoResearchAgent
)
from ..core.memory_system import MemorySystem
from ..core.ml_engine import MLEngine
from ..core.web_research import WebResearcher


class MasterAIBrain:
    """
    Master AI Brain - Claude-Powered Decision System
    
    Architecture:
    - Claude AI = Master decision maker
    - 9 Alpha Agents = Data collectors (Swiss watch precision)
    - ML Engine = Pattern discovery & predictions
    - Memory System = Historical context & learning
    - Web Researcher = Additional intelligence
    
    Flow:
    1. Scan market (every 5 min)
    2. Filter candidates (1000 → 5-10)
    3. Agents collect data (synchronized)
    4. Claude analyzes & decides
    5. Execute trades
    6. Monitor & adjust
    7. Learn from results
    """
    
    def __init__(
        self,
        claude_client: ClaudeAgentClient,
        lunarcrush_client: LunarCrushClient,
        mexc_client: MEXCClient,
        memory_system: MemorySystem,
        ml_engine: MLEngine,
        web_researcher: WebResearcher
    ):
        """
        Args:
            claude_client: Claude Agent SDK client
            lunarcrush_client: LunarCrush API client
            mexc_client: MEXC trading client
            memory_system: Memory & learning system
            ml_engine: Machine learning engine
            web_researcher: Web research capabilities
        """
        self.claude = claude_client
        self.lunarcrush = lunarcrush_client
        self.mexc = mexc_client
        self.memory = memory_system
        self.ml = ml_engine
        self.web_researcher = web_researcher
        
        # Initialize 9 Alpha Agents
        self.agents = {
            "market_analyzer": MarketAnalyzer(mexc_client),
            "sentiment_analyzer": SentimentAnalyzer(lunarcrush_client),
            "risk_manager": RiskManager(mexc_client),
            "strategy_agent": TradingStrategyAgent(),
            "trade_monitor": TradeMonitorAgent(mexc_client),
            "onchain_analyzer": OnChainAnalyzer(),
            "portfolio_optimizer": PortfolioOptimizer(mexc_client),
            "alert_manager": AlertManager(),
            "research_agent": CryptoResearchAgent(web_researcher)
        }
        
        # State
        self.is_running = False
        self.scan_task = None
        self.scan_interval = 300  # 5 minutes
        
        # Stats
        self.total_scans = 0
        self.total_trades = 0
        self.total_decisions = 0
        
        logger.info("✅ Master AI Brain initialized (Claude-powered)")
    
    async def start(self):
        """Start the autonomous trading system"""
        if self.is_running:
            logger.warning("Master Brain already running")
            return
        
        self.is_running = True
        self.scan_task = asyncio.create_task(self._scan_loop())
        
        logger.info("🚀 Master AI Brain started - Autonomous trading active")
    
    async def stop(self):
        """Stop the system"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scan_task:
            self.scan_task.cancel()
        
        logger.info("🛑 Master AI Brain stopped")
    
    async def _scan_loop(self):
        """Main scanning loop"""
        while self.is_running:
            try:
                await self._execute_scan_cycle()
                self.total_scans += 1
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Scan cycle error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    async def _execute_scan_cycle(self):
        """
        Execute one complete scan cycle
        
        Steps:
        1. Fetch top coins from LunarCrush
        2. Filter candidates
        3. Collect data from all agents (synchronized)
        4. Claude analyzes and decides
        5. Execute trades if needed
        """
        logger.info(f"🔍 Scan cycle #{self.total_scans + 1} started")
        
        # Step 1: Fetch top coins
        coins = await self._fetch_top_coins()
        
        if not coins:
            logger.warning("No coins fetched, skipping cycle")
            return
        
        logger.info(f"📊 Fetched {len(coins)} coins from LunarCrush")
        
        # Step 2: Filter candidates
        candidates = await self._filter_candidates(coins)
        
        if not candidates:
            logger.info("No candidates passed filters")
            return
        
        logger.info(f"🎯 {len(candidates)} candidates selected for analysis")
        
        # Step 3: Analyze each candidate
        for candidate in candidates:
            try:
                await self._analyze_and_decide(candidate)
            except Exception as e:
                logger.error(f"Failed to analyze {candidate.get('symbol', 'UNKNOWN')}: {e}")
        
        logger.info(f"✅ Scan cycle #{self.total_scans + 1} completed")
    
    async def _fetch_top_coins(self) -> List[Dict]:
        """Fetch top coins from LunarCrush"""
        try:
            # Fetch top 100 by social volume
            coins = self.lunarcrush.get_coins_list(
                limit=100,
                sort="social_volume_24h"
            )
            
            return coins
        
        except Exception as e:
            logger.error(f"Failed to fetch coins: {e}")
            return []
    
    async def _filter_candidates(self, coins: List[Dict]) -> List[Dict]:
        """
        Filter coins to top candidates
        
        Filters:
        - Market cap > $10M
        - Volume 24h > $1M
        - Social volume > 1000
        - Galaxy score > 50
        
        Returns:
            Top 5-10 candidates
        """
        candidates = []
        
        for coin in coins:
            # Extract metrics
            market_cap = coin.get("market_cap", 0)
            volume_24h = coin.get("volume_24h", 0)
            social_volume = coin.get("social_volume_24h", 0)
            galaxy_score = coin.get("galaxy_score", 0)
            
            # Apply filters
            if market_cap < 10_000_000:
                continue
            
            if volume_24h < 1_000_000:
                continue
            
            if social_volume < 1000:
                continue
            
            if galaxy_score < 50:
                continue
            
            candidates.append(coin)
        
        # Sort by social volume and take top 10
        candidates.sort(key=lambda x: x.get("social_volume_24h", 0), reverse=True)
        
        return candidates[:10]
    
    async def _analyze_and_decide(self, coin_data: Dict):
        """
        Analyze a candidate and let Claude decide
        
        Args:
            coin_data: LunarCrush coin data
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        logger.info(f"🤖 Analyzing {symbol}...")
        
        # Step 1: Collect data from all agents (synchronized)
        agent_reports = await self._collect_agent_reports(coin_data)
        
        # Step 2: Get additional context
        context = await self._get_decision_context(coin_data)
        
        # Step 3: Let Claude decide
        decision = await self._claude_decision(
            coin_data,
            agent_reports,
            context
        )
        
        self.total_decisions += 1
        
        # Step 4: Execute if Claude says so
        if decision.get("action") in ["LONG", "SHORT"]:
            await self._execute_trade(decision)
        else:
            logger.info(f"Claude decision for {symbol}: {decision.get('action')} - {decision.get('reasoning', '')[:100]}")
    
    async def _collect_agent_reports(self, coin_data: Dict) -> Dict:
        """
        Collect reports from all 9 agents (synchronized)
        
        Args:
            coin_data: Coin data
        
        Returns:
            Dict with all agent reports
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        logger.debug(f"📋 Collecting agent reports for {symbol}...")
        
        # Run all agents in parallel (Swiss watch precision)
        tasks = {
            "market": self.agents["market_analyzer"].analyze(coin_data),
            "sentiment": self.agents["sentiment_analyzer"].analyze(coin_data),
            "risk": self.agents["risk_manager"].analyze(coin_data),
            "strategy": self.agents["strategy_agent"].analyze(coin_data),
            "onchain": self.agents["onchain_analyzer"].analyze(coin_data),
            "portfolio": self.agents["portfolio_optimizer"].analyze(coin_data),
            "research": self.agents["research_agent"].analyze(coin_data)
        }
        
        # Wait for all agents (with timeout)
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Build reports dict
        reports = {}
        for (name, task), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                logger.error(f"Agent {name} failed: {result}")
                reports[name] = {"status": "error", "error": str(result)}
            else:
                reports[name] = result
        
        logger.debug(f"✅ Collected {len(reports)} agent reports for {symbol}")
        
        return reports
    
    async def _get_decision_context(self, coin_data: Dict) -> Dict:
        """
        Get additional context for decision
        
        Args:
            coin_data: Coin data
        
        Returns:
            Context dict
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        # Get memory context
        memory_context = await self.memory.get_context_for_decision(coin_data)
        
        # Get ML prediction
        ml_prediction = self.ml.predict_outcome(coin_data)
        
        return {
            "memory": memory_context,
            "ml_prediction": ml_prediction,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _claude_decision(
        self,
        coin_data: Dict,
        agent_reports: Dict,
        context: Dict
    ) -> Dict:
        """
        Let Claude analyze everything and make the decision
        
        Args:
            coin_data: Coin data
            agent_reports: Reports from all agents
            context: Additional context
        
        Returns:
            Claude's decision
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        logger.info(f"🧠 Claude analyzing {symbol}...")
        
        # Build comprehensive prompt for Claude
        prompt = self._build_claude_prompt(coin_data, agent_reports, context)
        
        # Get Claude's analysis
        try:
            response = await self.claude.chat(prompt, context=context)
            
            # Parse Claude's response
            decision = self._parse_claude_response(response, coin_data)
            
            logger.info(
                f"✅ Claude decision for {symbol}: "
                f"{decision.get('action')} "
                f"(confidence: {decision.get('confidence', 0):.1f}/10)"
            )
            
            return decision
        
        except Exception as e:
            logger.error(f"Claude decision failed: {e}")
            return {
                "action": "WAIT",
                "reasoning": f"Claude error: {str(e)}",
                "confidence": 0
            }
    
    def _build_claude_prompt(
        self,
        coin_data: Dict,
        agent_reports: Dict,
        context: Dict
    ) -> str:
        """Build comprehensive prompt for Claude"""
        
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        prompt = f"""You are the Master AI Brain of an autonomous cryptocurrency trading system.

Your task: Analyze {symbol} and decide whether to trade.

**COIN DATA (LunarCrush)**:
- Symbol: {symbol}
- Price: ${coin_data.get('price', 0):.4f}
- Market Cap: ${coin_data.get('market_cap', 0):,.0f}
- Volume 24h: ${coin_data.get('volume_24h', 0):,.0f}
- AltRank: {coin_data.get('alt_rank', 0)} (1-10000, lower is better)
- Galaxy Score: {coin_data.get('galaxy_score', 0)}/100
- Sentiment: {coin_data.get('sentiment', 0)}/100
- Social Volume 24h: {coin_data.get('social_volume_24h', 0):,} posts
- Social Dominance: {coin_data.get('social_dominance', 0):.2%}
- Price Change 24h: {coin_data.get('percent_change_24h', 0):.1f}%

**AGENT REPORTS**:

1. Market Analyzer:
{self._format_agent_report(agent_reports.get('market', {}))}

2. Sentiment Analyzer:
{self._format_agent_report(agent_reports.get('sentiment', {}))}

3. Risk Manager:
{self._format_agent_report(agent_reports.get('risk', {}))}

4. Strategy Agent:
{self._format_agent_report(agent_reports.get('strategy', {}))}

5. OnChain Analyzer:
{self._format_agent_report(agent_reports.get('onchain', {}))}

6. Portfolio Optimizer:
{self._format_agent_report(agent_reports.get('portfolio', {}))}

7. Research Agent:
{self._format_agent_report(agent_reports.get('research', {}))}

**ML PREDICTION**:
{self._format_ml_prediction(context.get('ml_prediction', {}))}

**HISTORICAL CONTEXT**:
{self._format_memory_context(context.get('memory', {}))}

**YOUR DECISION**:

Analyze all the data above and decide:

1. **ACTION**: LONG | SHORT | WAIT
2. **MARKET**: SPOT | FUTURES (or SPOT if futures not available for micro tokens)
3. **LEVERAGE**: 1-10x (if futures)
4. **CONFIDENCE**: 0-10 (only trade if >7.5)
5. **POSITION_SIZE**: USD amount to risk
6. **ENTRY_PRICE**: Recommended entry
7. **STOP_LOSS**: Stop-loss price
8. **TAKE_PROFIT**: Target price
9. **HOLD_TIME**: Estimated hold time (scalping/day/swing)
10. **REASONING**: Your detailed analysis (2-3 sentences)

**IMPORTANT**:
- Be conservative - only trade high confidence signals (>7.5/10)
- Consider risk/reward ratio
- Use historical context to avoid past mistakes
- Adapt to market conditions (volatility, trend, sentiment)
- You can SHORT on futures if bearish
- You can transfer between spot/futures if needed
- Micro tokens may only have spot (no futures)

Provide your decision in this format:

ACTION: [LONG/SHORT/WAIT]
MARKET: [SPOT/FUTURES]
LEVERAGE: [1-10]
CONFIDENCE: [0-10]
POSITION_SIZE: [USD]
ENTRY_PRICE: [price]
STOP_LOSS: [price]
TAKE_PROFIT: [price]
HOLD_TIME: [scalping/day/swing]
REASONING: [your analysis]
"""
        
        return prompt
    
    def _format_agent_report(self, report: Dict) -> str:
        """Format agent report for prompt"""
        if not report or report.get("status") == "error":
            return "  [Agent failed or no data]"
        
        lines = []
        for key, value in report.items():
            if key not in ["status", "timestamp"]:
                lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines) if lines else "  [No significant data]"
    
    def _format_ml_prediction(self, prediction: Dict) -> str:
        """Format ML prediction for prompt"""
        if not prediction:
            return "  [ML model not trained yet]"
        
        return f"""  - Predicted Action: {prediction.get('predicted_decision', 'UNKNOWN')}
  - ML Confidence: {prediction.get('confidence', 0):.1%}
  - Expected P&L: ${prediction.get('expected_pnl', 0):.2f}
  - ML Score: {prediction.get('ml_score', 0):.1f}/10"""
    
    def _format_memory_context(self, memory: Dict) -> str:
        """Format memory context for prompt"""
        if not memory:
            return "  [No historical data]"
        
        similar_trades = memory.get("similar_trades", [])
        lessons = memory.get("lessons_learned", [])
        performance = memory.get("recent_performance", {})
        
        lines = []
        
        if similar_trades:
            lines.append(f"  - Similar trades: {len(similar_trades)} past trades")
            avg_pnl = sum(t.get("pnl", 0) for t in similar_trades) / len(similar_trades)
            lines.append(f"  - Average P&L: ${avg_pnl:.2f}")
        
        if performance:
            win_rate = performance.get("win_rate", 0)
            lines.append(f"  - Recent win rate: {win_rate:.1%}")
        
        if lessons:
            lines.append(f"  - Lessons learned: {len(lessons)} insights")
            for lesson in lessons[:2]:
                lines.append(f"    • {lesson.get('lesson', '')}")
        
        return "\n".join(lines) if lines else "  [No historical context]"
    
    def _parse_claude_response(self, response: str, coin_data: Dict) -> Dict:
        """Parse Claude's response into structured decision"""
        
        decision = {
            "action": "WAIT",
            "market": "SPOT",
            "leverage": 1,
            "confidence": 5.0,
            "position_size": 100,
            "entry_price": coin_data.get("price", 0),
            "stop_loss": None,
            "take_profit": None,
            "hold_time": "day",
            "reasoning": "",
            "symbol": coin_data.get("symbol", "UNKNOWN"),
            "raw_response": response
        }
        
        # Parse response line by line
        lines = response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("ACTION:"):
                action = line.split(":", 1)[1].strip().upper()
                if action in ["LONG", "SHORT", "WAIT"]:
                    decision["action"] = action
            
            elif line.startswith("MARKET:"):
                market = line.split(":", 1)[1].strip().upper()
                if market in ["SPOT", "FUTURES"]:
                    decision["market"] = market
            
            elif line.startswith("LEVERAGE:"):
                try:
                    leverage = int(line.split(":", 1)[1].strip())
                    decision["leverage"] = max(1, min(10, leverage))
                except:
                    pass
            
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                    decision["confidence"] = max(0, min(10, confidence))
                except:
                    pass
            
            elif line.startswith("POSITION_SIZE:"):
                try:
                    size = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                    decision["position_size"] = size
                except:
                    pass
            
            elif line.startswith("ENTRY_PRICE:"):
                try:
                    price = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                    decision["entry_price"] = price
                except:
                    pass
            
            elif line.startswith("STOP_LOSS:"):
                try:
                    price = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                    decision["stop_loss"] = price
                except:
                    pass
            
            elif line.startswith("TAKE_PROFIT:"):
                try:
                    price = float(line.split(":", 1)[1].strip().replace("$", "").replace(",", ""))
                    decision["take_profit"] = price
                except:
                    pass
            
            elif line.startswith("HOLD_TIME:"):
                hold_time = line.split(":", 1)[1].strip().lower()
                if hold_time in ["scalping", "day", "swing"]:
                    decision["hold_time"] = hold_time
            
            elif line.startswith("REASONING:"):
                decision["reasoning"] = line.split(":", 1)[1].strip()
        
        return decision
    
    async def _execute_trade(self, decision: Dict):
        """
        Execute trade based on Claude's decision
        
        Args:
            decision: Claude's trading decision
        """
        symbol = decision.get("symbol", "UNKNOWN")
        action = decision.get("action")
        market = decision.get("market")
        
        logger.info(
            f"🚀 Executing trade: {symbol} {action} on {market} "
            f"(confidence: {decision.get('confidence', 0):.1f}/10)"
        )
        
        try:
            # Execute on MEXC
            if market == "SPOT":
                result = await self.mexc.execute_spot_trade(
                    symbol=symbol,
                    side=action,
                    quantity=decision.get("position_size", 100) / decision.get("entry_price", 1)
                )
            else:  # FUTURES
                result = await self.mexc.execute_futures_trade(
                    symbol=symbol,
                    side=action,
                    quantity=decision.get("position_size", 100) / decision.get("entry_price", 1),
                    leverage=decision.get("leverage", 1),
                    stop_loss=decision.get("stop_loss"),
                    take_profit=decision.get("take_profit")
                )
            
            # Remember trade
            await self.memory.remember_trade(
                trade_data={
                    "symbol": symbol,
                    "side": action,
                    "entry_price": decision.get("entry_price"),
                    "quantity": result.get("quantity", 0),
                    "leverage": decision.get("leverage", 1),
                    "stop_loss": decision.get("stop_loss"),
                    "take_profit": decision.get("take_profit")
                },
                market_conditions={},
                decision_context=decision
            )
            
            self.total_trades += 1
            
            logger.info(f"✅ Trade executed: {symbol} {action}")
        
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
    
    def get_stats(self) -> Dict:
        """Get Master Brain statistics"""
        return {
            "is_running": self.is_running,
            "total_scans": self.total_scans,
            "total_decisions": self.total_decisions,
            "total_trades": self.total_trades,
            "agents_count": len(self.agents),
            "scan_interval": self.scan_interval
        }

    
    def get_agents_status(self) -> List[Dict]:
        """Get status of all 9 agents"""
        agents_status = []
        
        for agent in self.agents:
            status = {
                "name": agent.name,
                "role": agent.role,
                "status": "active" if self.is_running else "idle",
                "total_analyses": getattr(agent, 'total_analyses', 0),
                "avg_confidence": getattr(agent, 'avg_confidence', 0),
                "last_analysis": getattr(agent, 'last_analysis_time', None)
            }
            agents_status.append(status)
        
        return agents_status
