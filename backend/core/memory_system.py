"""
Alpha AI Autotrader - Memory System
Long-term memory for learning from past trades and decisions
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import Trade, Signal, Pattern, Performance


class MemorySystem:
    """
    Memory System - Long-term learning and pattern recognition
    
    Capabilities:
    - Remember all trades (successful and failed)
    - Remember market conditions for each trade
    - Identify successful patterns
    - Identify failed patterns
    - Provide context for new decisions
    - Learn from mistakes
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.cache = {
            "successful_patterns": [],
            "failed_patterns": [],
            "best_conditions": {},
            "worst_conditions": {}
        }
        
        logger.info("✅ Memory System initialized")
    
    async def remember_trade(
        self,
        trade_data: Dict,
        market_conditions: Dict,
        decision_context: Dict
    ) -> None:
        """
        Remember a trade for future learning
        
        Args:
            trade_data: Trade information
            market_conditions: Market conditions at trade time
            decision_context: Agent votes, patterns, confidence
        """
        try:
            # Create Trade record
            trade = Trade(
                symbol=trade_data["symbol"],
                side=trade_data["side"],
                entry_price=trade_data["entry_price"],
                exit_price=trade_data.get("exit_price"),
                quantity=trade_data["quantity"],
                leverage=trade_data.get("leverage", 1),
                stop_loss=trade_data.get("stop_loss"),
                take_profit=trade_data.get("take_profit"),
                pnl=trade_data.get("pnl", 0),
                status=trade_data.get("status", "open"),
                opened_at=datetime.utcnow(),
                closed_at=trade_data.get("closed_at"),
                metadata={
                    "market_conditions": market_conditions,
                    "decision_context": decision_context
                }
            )
            
            self.db.add(trade)
            await self.db.commit()
            
            logger.info(f"💾 Trade remembered: {trade_data['symbol']} {trade_data['side']}")
        
        except Exception as e:
            logger.error(f"Failed to remember trade: {e}")
            await self.db.rollback()
    
    async def remember_pattern(
        self,
        pattern_name: str,
        coin_data: Dict,
        outcome: str,
        confidence: float
    ) -> None:
        """
        Remember a pattern occurrence and its outcome
        
        Args:
            pattern_name: Name of the pattern
            coin_data: Coin data when pattern was detected
            outcome: "success" | "failure" | "pending"
            confidence: Pattern confidence (0-10)
        """
        try:
            pattern = Pattern(
                name=pattern_name,
                symbol=coin_data.get("symbol", "UNKNOWN"),
                confidence=confidence,
                outcome=outcome,
                detected_at=datetime.utcnow(),
                metadata={
                    "coin_data": coin_data
                }
            )
            
            self.db.add(pattern)
            await self.db.commit()
            
            # Update cache
            if outcome == "success":
                self.cache["successful_patterns"].append(pattern_name)
            elif outcome == "failure":
                self.cache["failed_patterns"].append(pattern_name)
        
        except Exception as e:
            logger.error(f"Failed to remember pattern: {e}")
            await self.db.rollback()
    
    async def get_pattern_success_rate(self, pattern_name: str) -> float:
        """
        Get success rate for a specific pattern
        
        Args:
            pattern_name: Pattern name
        
        Returns:
            Success rate (0-1)
        """
        try:
            # Query all occurrences of this pattern
            result = await self.db.execute(
                select(Pattern).where(Pattern.name == pattern_name)
            )
            patterns = result.scalars().all()
            
            if not patterns:
                return 0.5  # Default (no data)
            
            # Calculate success rate
            successful = sum(1 for p in patterns if p.outcome == "success")
            total = len([p for p in patterns if p.outcome in ["success", "failure"]])
            
            if total == 0:
                return 0.5
            
            return successful / total
        
        except Exception as e:
            logger.error(f"Failed to get pattern success rate: {e}")
            return 0.5
    
    async def get_similar_trades(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get similar past trades for this symbol
        
        Args:
            symbol: Coin symbol
            limit: Max number of trades to return
        
        Returns:
            List of similar trades
        """
        try:
            result = await self.db.execute(
                select(Trade)
                .where(Trade.symbol == symbol)
                .where(Trade.status == "closed")
                .order_by(Trade.closed_at.desc())
                .limit(limit)
            )
            trades = result.scalars().all()
            
            return [
                {
                    "symbol": t.symbol,
                    "side": t.side,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "leverage": t.leverage,
                    "opened_at": t.opened_at,
                    "closed_at": t.closed_at,
                    "metadata": t.metadata
                }
                for t in trades
            ]
        
        except Exception as e:
            logger.error(f"Failed to get similar trades: {e}")
            return []
    
    async def get_best_conditions(self) -> Dict:
        """
        Get market conditions that led to best trades
        
        Returns:
            Dict with best conditions
        """
        try:
            # Get top 10 most profitable trades
            result = await self.db.execute(
                select(Trade)
                .where(Trade.status == "closed")
                .where(Trade.pnl > 0)
                .order_by(Trade.pnl.desc())
                .limit(10)
            )
            trades = result.scalars().all()
            
            if not trades:
                return {}
            
            # Extract common conditions
            conditions = {
                "avg_altrank": [],
                "avg_galaxy_score": [],
                "avg_sentiment": [],
                "common_patterns": []
            }
            
            for trade in trades:
                metadata = trade.metadata or {}
                market_cond = metadata.get("market_conditions", {})
                decision_ctx = metadata.get("decision_context", {})
                
                if "altrank" in market_cond:
                    conditions["avg_altrank"].append(market_cond["altrank"])
                
                if "galaxy_score" in market_cond:
                    conditions["avg_galaxy_score"].append(market_cond["galaxy_score"])
                
                if "sentiment" in market_cond:
                    conditions["avg_sentiment"].append(market_cond["sentiment"])
                
                patterns = decision_ctx.get("patterns", [])
                conditions["common_patterns"].extend(patterns)
            
            # Calculate averages
            best_conditions = {}
            
            if conditions["avg_altrank"]:
                best_conditions["altrank_range"] = (
                    min(conditions["avg_altrank"]),
                    max(conditions["avg_altrank"])
                )
            
            if conditions["avg_galaxy_score"]:
                best_conditions["min_galaxy_score"] = min(conditions["avg_galaxy_score"])
            
            if conditions["avg_sentiment"]:
                best_conditions["min_sentiment"] = min(conditions["avg_sentiment"])
            
            # Most common patterns
            from collections import Counter
            pattern_counts = Counter(conditions["common_patterns"])
            best_conditions["best_patterns"] = [
                p for p, count in pattern_counts.most_common(3)
            ]
            
            return best_conditions
        
        except Exception as e:
            logger.error(f"Failed to get best conditions: {e}")
            return {}
    
    async def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Get performance statistics for last N days
        
        Args:
            days: Number of days to look back
        
        Returns:
            Performance statistics
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get all closed trades in period
            result = await self.db.execute(
                select(Trade)
                .where(Trade.status == "closed")
                .where(Trade.closed_at >= since)
            )
            trades = result.scalars().all()
            
            if not trades:
                return {
                    "total_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "best_trade": 0,
                    "worst_trade": 0
                }
            
            # Calculate stats
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            total_pnl = sum(t.pnl for t in trades)
            avg_pnl = total_pnl / len(trades)
            win_rate = len(winning_trades) / len(trades) if trades else 0
            
            best_trade = max((t.pnl for t in trades), default=0)
            worst_trade = min((t.pnl for t in trades), default=0)
            
            return {
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl,
                "best_trade": best_trade,
                "worst_trade": worst_trade,
                "period_days": days
            }
        
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    async def learn_from_mistakes(self) -> List[Dict]:
        """
        Analyze failed trades and extract lessons
        
        Returns:
            List of lessons learned
        """
        try:
            # Get last 20 losing trades
            result = await self.db.execute(
                select(Trade)
                .where(Trade.status == "closed")
                .where(Trade.pnl < 0)
                .order_by(Trade.closed_at.desc())
                .limit(20)
            )
            trades = result.scalars().all()
            
            if not trades:
                return []
            
            lessons = []
            
            # Analyze common factors in losing trades
            low_confidence_losses = [
                t for t in trades
                if t.metadata and t.metadata.get("decision_context", {}).get("confidence", 10) < 7.5
            ]
            
            if len(low_confidence_losses) > len(trades) * 0.5:
                lessons.append({
                    "lesson": "Avoid trades with confidence <7.5",
                    "evidence": f"{len(low_confidence_losses)}/{len(trades)} losses had low confidence",
                    "severity": "high"
                })
            
            # Check for pattern failures
            failed_patterns = {}
            for trade in trades:
                metadata = trade.metadata or {}
                patterns = metadata.get("decision_context", {}).get("patterns", [])
                
                for pattern in patterns:
                    failed_patterns[pattern] = failed_patterns.get(pattern, 0) + 1
            
            for pattern, count in failed_patterns.items():
                if count >= 3:
                    lessons.append({
                        "lesson": f"Pattern '{pattern}' has high failure rate",
                        "evidence": f"{count} losses with this pattern",
                        "severity": "medium"
                    })
            
            return lessons
        
        except Exception as e:
            logger.error(f"Failed to learn from mistakes: {e}")
            return []
    
    async def get_context_for_decision(self, coin_data: Dict) -> Dict:
        """
        Get relevant context from memory for a new decision
        
        Args:
            coin_data: Current coin data
        
        Returns:
            Context dict with historical insights
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        # Get similar trades
        similar_trades = await self.get_similar_trades(symbol, limit=5)
        
        # Get best conditions
        best_conditions = await self.get_best_conditions()
        
        # Get performance stats
        performance = await self.get_performance_stats(days=7)
        
        # Get lessons
        lessons = await self.learn_from_mistakes()
        
        return {
            "similar_trades": similar_trades,
            "best_conditions": best_conditions,
            "recent_performance": performance,
            "lessons_learned": lessons,
            "has_history": len(similar_trades) > 0
        }
