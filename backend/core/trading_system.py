"""
Alpha AI Autotrader - Trading System
Main orchestrator that ties everything together
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime

from ..integrations.lunarcrush import LunarCrushClient
from ..integrations.mexc_client import MEXCClient
from ..integrations.openrouter_client import OpenRouterClient
from .candidate_filter import CandidateFilter
from .master_brain_v2 import MasterAIBrain
from .config import Settings


class TradingSystem:
    """
    Main Trading System Orchestrator
    
    Workflow:
    1. Fetch data from LunarCrush (every 5 min)
    2. Filter candidates (1000+ → 5-10)
    3. Fetch MEXC market data for candidates
    4. Master Brain analyzes each candidate
    5. Execute trades if confidence >threshold
    6. Monitor open positions
    7. Broadcast updates via WebSocket
    """
    
    def __init__(self, settings: Settings):
        """
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize clients
        self.lunarcrush = LunarCrushClient(
            api_key=settings.LUNARCRUSH_API_KEY,
            cache_ttl=settings.LUNARCRUSH_CACHE_TTL
        )
        
        self.mexc = MEXCClient(
            api_key=settings.MEXC_API_KEY,
            secret_key=settings.MEXC_SECRET_KEY,
            testnet=settings.MEXC_TESTNET
        )
        
        openrouter_key = settings.OPENROUTER_API_KEY if settings.ENABLE_MULTI_AI_CONSENSUS else None
        
        # Initialize core components
        self.candidate_filter = CandidateFilter()
        self.master_brain = MasterAIBrain(
            openrouter_api_key=openrouter_key
        )
        
        # State
        self.is_running = False
        self.scan_task = None
        self.monitor_task = None
        
        # Stats
        self.total_scans = 0
        self.total_signals = 0
        self.total_trades = 0
        
        logger.info("✅ Trading System initialized")
    
    async def start(self):
        """Start the trading system"""
        if self.is_running:
            logger.warning("Trading system already running")
            return
        
        self.is_running = True
        logger.info("🚀 Trading System starting...")
        
        # Start background tasks
        self.scan_task = asyncio.create_task(self._scan_loop())
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("✅ Trading System started")
    
    async def stop(self):
        """Stop the trading system"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🛑 Trading System stopping...")
        
        # Cancel background tasks
        if self.scan_task:
            self.scan_task.cancel()
        
        if self.monitor_task:
            self.monitor_task.cancel()
        
        logger.info("✅ Trading System stopped")
    
    async def _scan_loop(self):
        """
        Main scanning loop
        Runs every SCAN_INTERVAL seconds
        """
        while self.is_running:
            try:
                await self._run_scan()
                await asyncio.sleep(self.settings.SCAN_INTERVAL)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    async def _monitor_loop(self):
        """
        Position monitoring loop
        Checks open positions every minute
        """
        while self.is_running:
            try:
                await self._monitor_positions()
                await asyncio.sleep(60)  # Check every minute
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)
    
    async def _run_scan(self):
        """
        Run a complete market scan
        
        Steps:
        1. Fetch coins from LunarCrush
        2. Filter candidates
        3. Fetch MEXC data
        4. Analyze with Master Brain
        5. Execute trades (if enabled)
        """
        logger.info("🔍 Starting market scan...")
        self.total_scans += 1
        
        # Step 1: Fetch coins from LunarCrush
        try:
            coins = self.lunarcrush.get_coins_list(
                limit=self.settings.TOP_COINS_TO_SCAN,
                sort="social_volume_24h"
            )
            logger.info(f"📊 Fetched {len(coins)} coins from LunarCrush")
        
        except Exception as e:
            logger.error(f"Failed to fetch LunarCrush data: {e}")
            return
        
        # Step 2: Filter candidates
        candidates = self.candidate_filter.filter_candidates(coins)
        logger.info(f"🎯 Filtered to {len(candidates)} top candidates")
        
        # Store latest candidates
        self._latest_candidates = candidates
        
        if not candidates:
            logger.info("No candidates passed filters")
            return
        
        # Step 3: Fetch MEXC market data for candidates
        mexc_data = {}
        for candidate in candidates:
            symbol = candidate.get("symbol", "")
            try:
                ticker = self.mexc.fetch_ticker(f"{symbol}/USDT")
                ohlcv = self.mexc.fetch_ohlcv(f"{symbol}/USDT", "1h", limit=100)
                
                mexc_data[symbol] = {
                    "ticker": ticker,
                    "ohlcv": ohlcv
                }
            
            except Exception as e:
                logger.warning(f"Failed to fetch MEXC data for {symbol}: {e}")
                continue
        
        # Step 4: Analyze each candidate with Master Brain
        signals = []
        
        for candidate in candidates:
            symbol = candidate.get("symbol", "")
            
            if symbol not in mexc_data:
                continue
            
            try:
                # Get portfolio context
                context = await self._get_portfolio_context()
                
                # Analyze with Master Brain
                result = self.master_brain.analyze_candidate(
                    coin_data=candidate,
                    market_data=mexc_data[symbol],
                    context=context
                )
                
                # Check if it's a valid signal
                if result["decision"] in ["LONG", "SHORT"]:
                    signals.append(result)
                    self.total_signals += 1
                    
                    logger.info(
                        f"🎯 SIGNAL: {symbol} {result['decision']} "
                        f"({result['confidence']:.1f}/10)"
                    )
                    
                    # Broadcast signal via WebSocket
                    # await self._broadcast_signal(result)
            
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Step 5: Execute trades (if enabled)
        if self.settings.ENABLE_AUTO_TRADING and signals:
            for signal in signals:
                try:
                    await self._execute_trade(signal)
                except Exception as e:
                    logger.error(f"Failed to execute trade: {e}")
        
        logger.info(
            f"✅ Scan complete: {len(candidates)} candidates, "
            f"{len(signals)} signals generated"
        )
    
    async def _monitor_positions(self):
        """
        Monitor open positions and manage them
        
        Actions:
        - Move stop-loss to break-even
        - Trailing stop
        - Close on stop-loss/take-profit
        - Alert on significant P&L changes
        """
        try:
            # Fetch open positions from MEXC
            positions = self.mexc.fetch_positions()
            
            if not positions:
                return
            
            logger.info(f"📊 Monitoring {len(positions)} open positions...")
            
            for position in positions:
                symbol = position.get("symbol", "")
                
                # Get current market data
                try:
                    ticker = self.mexc.fetch_ticker(symbol)
                    current_price = ticker["last"]
                    
                    # Get coin data for context
                    # (In production, cache this or fetch less frequently)
                    
                    # Analyze with Trade Monitor Agent
                    from ..agents import TradeMonitorAgent
                    monitor_agent = TradeMonitorAgent()
                    
                    context = {
                        "position": {
                            **position,
                            "current_price": current_price
                        }
                    }
                    
                    decision = monitor_agent.analyze(
                        coin_data={"symbol": symbol, "price": current_price},
                        context=context
                    )
                    
                    # Take action based on decision
                    if decision["decision"] == "CLOSE":
                        logger.info(f"🔴 Closing position: {symbol}")
                        if self.settings.ENABLE_AUTO_TRADING:
                            await self._close_position(symbol)
                    
                    elif decision["decision"] == "ADJUST_SL":
                        logger.info(f"🔧 Adjusting stop-loss: {symbol}")
                        # Implement stop-loss adjustment
                
                except Exception as e:
                    logger.error(f"Failed to monitor position {symbol}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Position monitoring error: {e}")
    
    async def _execute_trade(self, signal: Dict):
        """
        Execute a trade based on signal
        
        Args:
            signal: Signal from Master Brain
        """
        symbol = signal["symbol"]
        decision = signal["decision"]
        confidence = signal["confidence"]
        
        logger.info(f"⚡ Executing trade: {symbol} {decision} ({confidence:.1f}/10)")
        
        # Get recommended position size from risk manager
        recommendation = signal.get("final_recommendation", {})
        agent_consensus = recommendation.get("agent_consensus", {})
        votes_summary = agent_consensus.get("votes_summary", {})
        risk_vote = votes_summary.get("risk-manager", {})
        
        position_size_usd = risk_vote.get("indicators", {}).get("position_size_usd", 100)
        leverage = risk_vote.get("indicators", {}).get("recommended_leverage", 1)
        
        # Get entry/exit levels from strategy agent
        strategy_vote = votes_summary.get("trading-strategy-agent", {})
        entry_price = strategy_vote.get("indicators", {}).get("entry_price", 0)
        stop_loss = strategy_vote.get("indicators", {}).get("stop_loss", 0)
        take_profit = strategy_vote.get("indicators", {}).get("take_profit", 0)
        
        # Calculate position size in base currency
        ticker = self.mexc.fetch_ticker(f"{symbol}/USDT")
        current_price = ticker["last"]
        position_size = position_size_usd / current_price
        
        # Determine market type (spot or futures)
        use_futures = (
            self.settings.ENABLE_FUTURES_TRADING and
            leverage > 1
        )
        
        try:
            if use_futures:
                # Execute futures order
                order = self.mexc.create_futures_market_order(
                    symbol=f"{symbol}/USDT:USDT",
                    side="buy" if decision == "LONG" else "sell",
                    amount=position_size,
                    leverage=leverage
                )
            else:
                # Execute spot order
                if decision == "LONG":
                    order = self.mexc.create_spot_market_order(
                        symbol=f"{symbol}/USDT",
                        side="buy",
                        amount=position_size
                    )
                else:
                    # For SHORT on spot, we'd need to borrow (margin)
                    # For now, skip spot shorts
                    logger.warning(f"Spot SHORT not supported for {symbol}")
                    return
            
            self.total_trades += 1
            
            logger.info(f"✅ Trade executed: {order}")
            
            # Save to database
            # await self._save_trade(signal, order)
            
            # Broadcast via WebSocket
            # await self._broadcast_trade(signal, order)
        
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            raise
    
    async def _close_position(self, symbol: str):
        """Close a position"""
        try:
            result = self.mexc.close_position(symbol)
            logger.info(f"✅ Position closed: {symbol}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            raise
    
    async def _get_portfolio_context(self) -> Dict:
        """Get current portfolio context"""
        try:
            balance = self.mexc.fetch_balance()
            positions = self.mexc.fetch_positions()
            
            portfolio_value = balance.get("USDT", {}).get("total", 10000)
            open_positions = len(positions)
            
            return {
                "portfolio_value": portfolio_value,
                "open_positions": open_positions,
                "open_positions_list": positions,
                "max_positions": self.settings.MAX_CONCURRENT_POSITIONS,
                "max_position_size_usd": self.settings.MAX_POSITION_SIZE_USD
            }
        
        except Exception as e:
            logger.error(f"Failed to get portfolio context: {e}")
            return {
                "portfolio_value": 10000,
                "open_positions": 0,
                "open_positions_list": [],
                "max_positions": self.settings.MAX_CONCURRENT_POSITIONS,
                "max_position_size_usd": self.settings.MAX_POSITION_SIZE_USD
            }
    
    def get_stats(self) -> Dict:
        """Get trading system statistics"""
        return {
            "is_running": self.is_running,
            "total_scans": self.total_scans,
            "total_signals": self.total_signals,
            "total_trades": self.total_trades,
            "lunarcrush_stats": self.lunarcrush.get_stats(),
            "master_brain_stats": self.master_brain.get_stats(),
            "filter_stats": self.candidate_filter.get_stats()
        }

    
    def get_latest_candidates(self) -> List[Dict]:
        """Get latest filtered candidates"""
        if not hasattr(self, '_latest_candidates'):
            return []
        return self._latest_candidates
    
    async def run_scan(self):
        """Manually trigger a market scan"""
        logger.info("📊 Manual scan triggered")
        await self._run_scan()
