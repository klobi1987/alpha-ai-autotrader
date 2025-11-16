"""
Alpha AI Autotrader - Live Trade Manager
Real-time position monitoring and dynamic adjustments
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..integrations.mexc_client import MEXCClient
from ..integrations.claude_agent_client import ClaudeAgentClient


class LiveTradeManager:
    """
    Live Trade Manager - Real-time position management
    
    Capabilities:
    - Monitor open positions every minute
    - Dynamic stop-loss adjustment (move to break-even)
    - Trailing stop implementation
    - Partial profit taking
    - Emergency close on pattern failure
    - AI-powered position analysis
    """
    
    def __init__(
        self,
        mexc_client: MEXCClient,
        claude_client: Optional[ClaudeAgentClient] = None
    ):
        """
        Args:
            mexc_client: MEXC trading client
            claude_client: Claude Agent client for AI analysis
        """
        self.mexc = mexc_client
        self.claude = claude_client
        
        # State
        self.open_positions: Dict[str, Dict] = {}
        self.monitoring_task = None
        self.is_monitoring = False
        
        # Configuration
        self.config = {
            "check_interval": 60,  # Check every minute
            "breakeven_profit": 0.05,  # Move to BE at +5%
            "trailing_stop_profit": 0.10,  # Start trailing at +10%
            "trailing_stop_distance": 0.03,  # Trail 3% below peak
            "partial_take_profit": 0.15,  # Take 50% profit at +15%
            "max_loss_per_trade": 0.05,  # Max 5% loss per trade
            "emergency_close_confidence": 3.0  # Close if AI confidence drops below 3
        }
        
        logger.info("✅ Live Trade Manager initialized")
    
    async def start_monitoring(self):
        """Start monitoring open positions"""
        if self.is_monitoring:
            logger.warning("Already monitoring positions")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("🔍 Started position monitoring")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        logger.info("🛑 Stopped position monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._check_all_positions()
                await asyncio.sleep(self.config["check_interval"])
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_all_positions(self):
        """Check all open positions"""
        try:
            # Fetch open positions from MEXC
            positions = await self.mexc.get_open_positions()
            
            if not positions:
                return
            
            logger.info(f"📊 Checking {len(positions)} open positions...")
            
            for position in positions:
                await self._check_position(position)
        
        except Exception as e:
            logger.error(f"Failed to check positions: {e}")
    
    async def _check_position(self, position: Dict):
        """
        Check and manage a single position
        
        Args:
            position: Position data from MEXC
        """
        symbol = position["symbol"]
        entry_price = position["entry_price"]
        current_price = position["current_price"]
        side = position["side"]
        quantity = position["quantity"]
        unrealized_pnl = position["unrealized_pnl"]
        unrealized_pnl_pct = position["unrealized_pnl_pct"]
        
        logger.debug(
            f"Checking {symbol} {side}: "
            f"Entry=${entry_price:.2f}, Current=${current_price:.2f}, "
            f"P&L={unrealized_pnl_pct:.1%}"
        )
        
        # Update position tracking
        if symbol not in self.open_positions:
            self.open_positions[symbol] = {
                "entry_price": entry_price,
                "peak_price": current_price,
                "opened_at": datetime.utcnow(),
                "adjustments": []
            }
        
        tracked = self.open_positions[symbol]
        
        # Update peak price
        if side == "LONG":
            if current_price > tracked["peak_price"]:
                tracked["peak_price"] = current_price
        else:  # SHORT
            if current_price < tracked["peak_price"]:
                tracked["peak_price"] = current_price
        
        # Decision: What to do with this position?
        
        # 1. Check for emergency close
        if await self._should_emergency_close(position):
            await self._close_position(position, reason="Emergency close (AI signal)")
            return
        
        # 2. Check for stop-loss hit
        if unrealized_pnl_pct <= -self.config["max_loss_per_trade"]:
            await self._close_position(position, reason=f"Stop-loss hit ({unrealized_pnl_pct:.1%})")
            return
        
        # 3. Move to break-even if profitable
        if unrealized_pnl_pct >= self.config["breakeven_profit"]:
            if "moved_to_breakeven" not in tracked:
                await self._move_to_breakeven(position)
                tracked["moved_to_breakeven"] = True
                tracked["adjustments"].append({
                    "type": "breakeven",
                    "at": datetime.utcnow(),
                    "price": current_price
                })
        
        # 4. Partial profit taking
        if unrealized_pnl_pct >= self.config["partial_take_profit"]:
            if "partial_profit_taken" not in tracked:
                await self._take_partial_profit(position, percent=0.5)
                tracked["partial_profit_taken"] = True
                tracked["adjustments"].append({
                    "type": "partial_profit",
                    "at": datetime.utcnow(),
                    "price": current_price,
                    "percent": 0.5
                })
        
        # 5. Trailing stop
        if unrealized_pnl_pct >= self.config["trailing_stop_profit"]:
            await self._update_trailing_stop(position, tracked)
    
    async def _should_emergency_close(self, position: Dict) -> bool:
        """
        Check if position should be emergency closed
        
        Uses AI to re-analyze the position
        
        Args:
            position: Position data
        
        Returns:
            True if should close immediately
        """
        if not self.claude:
            return False
        
        try:
            symbol = position["symbol"]
            
            # Ask Claude to re-analyze
            prompt = f"""Analyze this open position and determine if it should be closed immediately.

Position:
- Symbol: {symbol}
- Side: {position['side']}
- Entry Price: ${position['entry_price']:.2f}
- Current Price: ${position['current_price']:.2f}
- P&L: {position['unrealized_pnl_pct']:.1%}
- Time Held: {(datetime.utcnow() - self.open_positions[symbol]['opened_at']).total_seconds() / 3600:.1f} hours

Should this position be closed immediately? Answer YES or NO with reasoning.
"""
            
            response = await self.claude.chat(prompt)
            
            # Parse response
            if "YES" in response.upper():
                logger.warning(f"⚠️ AI recommends emergency close for {symbol}: {response[:100]}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Emergency close check failed: {e}")
            return False
    
    async def _close_position(self, position: Dict, reason: str):
        """
        Close a position
        
        Args:
            position: Position data
            reason: Reason for closing
        """
        symbol = position["symbol"]
        
        try:
            logger.info(f"🔴 Closing {symbol}: {reason}")
            
            # Execute close on MEXC
            result = await self.mexc.close_position(
                symbol=symbol,
                side=position["side"],
                quantity=position["quantity"]
            )
            
            # Remove from tracking
            if symbol in self.open_positions:
                del self.open_positions[symbol]
            
            logger.info(f"✅ Closed {symbol}: P&L=${result.get('pnl', 0):.2f}")
        
        except Exception as e:
            logger.error(f"Failed to close {symbol}: {e}")
    
    async def _move_to_breakeven(self, position: Dict):
        """
        Move stop-loss to break-even
        
        Args:
            position: Position data
        """
        symbol = position["symbol"]
        entry_price = position["entry_price"]
        
        try:
            logger.info(f"⚡ Moving {symbol} to break-even (${entry_price:.2f})")
            
            # Update stop-loss on MEXC
            await self.mexc.update_stop_loss(
                symbol=symbol,
                side=position["side"],
                stop_price=entry_price
            )
            
            logger.info(f"✅ {symbol} stop-loss moved to break-even")
        
        except Exception as e:
            logger.error(f"Failed to move {symbol} to break-even: {e}")
    
    async def _take_partial_profit(self, position: Dict, percent: float = 0.5):
        """
        Take partial profit
        
        Args:
            position: Position data
            percent: Percentage to close (0-1)
        """
        symbol = position["symbol"]
        quantity = position["quantity"]
        close_quantity = quantity * percent
        
        try:
            logger.info(f"💰 Taking {percent:.0%} profit on {symbol}")
            
            # Close partial position
            result = await self.mexc.close_position(
                symbol=symbol,
                side=position["side"],
                quantity=close_quantity
            )
            
            logger.info(f"✅ Closed {percent:.0%} of {symbol}: P&L=${result.get('pnl', 0):.2f}")
        
        except Exception as e:
            logger.error(f"Failed to take partial profit on {symbol}: {e}")
    
    async def _update_trailing_stop(self, position: Dict, tracked: Dict):
        """
        Update trailing stop-loss
        
        Args:
            position: Position data
            tracked: Tracked position data
        """
        symbol = position["symbol"]
        side = position["side"]
        peak_price = tracked["peak_price"]
        current_price = position["current_price"]
        
        # Calculate trailing stop price
        if side == "LONG":
            stop_price = peak_price * (1 - self.config["trailing_stop_distance"])
        else:  # SHORT
            stop_price = peak_price * (1 + self.config["trailing_stop_distance"])
        
        try:
            # Update stop-loss on MEXC
            await self.mexc.update_stop_loss(
                symbol=symbol,
                side=side,
                stop_price=stop_price
            )
            
            logger.debug(f"📈 Updated trailing stop for {symbol}: ${stop_price:.2f}")
        
        except Exception as e:
            logger.error(f"Failed to update trailing stop for {symbol}: {e}")
    
    def get_position_stats(self) -> Dict:
        """Get statistics about managed positions"""
        if not self.open_positions:
            return {
                "open_positions": 0,
                "total_adjustments": 0
            }
        
        total_adjustments = sum(
            len(pos.get("adjustments", []))
            for pos in self.open_positions.values()
        )
        
        return {
            "open_positions": len(self.open_positions),
            "total_adjustments": total_adjustments,
            "positions": list(self.open_positions.keys())
        }
