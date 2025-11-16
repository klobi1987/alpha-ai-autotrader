"""
Alpha AI Autotrader - Risk Calculator
Smart stop-loss detection and optimal leverage calculation
"""
from typing import Dict, Tuple, Optional
from loguru import logger


class RiskCalculator:
    """
    Risk Calculator - Smart Stop-Loss & Optimal Leverage
    
    Provides SUGGESTIONS to Claude, not rigid rules.
    Claude makes final decisions based on full context.
    """
    
    def __init__(self):
        """Initialize risk calculator"""
        self.maintenance_margin_rate = 0.10  # 10% (MEXC default)
        self.safety_buffer = 0.02  # 2% safety buffer
        
        logger.info("✅ Risk Calculator initialized")
    
    def calculate_liquidation_price(
        self,
        entry_price: float,
        leverage: int,
        side: str = "LONG"
    ) -> float:
        """
        Calculate liquidation price for a position
        
        Args:
            entry_price: Entry price
            leverage: Leverage multiplier
            side: "LONG" or "SHORT"
        
        Returns:
            Liquidation price
        """
        if side == "LONG":
            # Long liquidation = Entry * (1 - 1/leverage * (1 - maintenance_margin))
            liq_price = entry_price * (1 - (1 / leverage) * (1 - self.maintenance_margin_rate))
        else:  # SHORT
            # Short liquidation = Entry * (1 + 1/leverage * (1 - maintenance_margin))
            liq_price = entry_price * (1 + (1 / leverage) * (1 - self.maintenance_margin_rate))
        
        return liq_price
    
    def find_technical_stop_loss(
        self,
        entry_price: float,
        market_data: Dict,
        side: str = "LONG"
    ) -> Dict:
        """
        Find technical stop-loss level
        
        Uses:
        - Support/resistance levels
        - Recent swing lows/highs
        - ATR-based stops
        
        Args:
            entry_price: Entry price
            market_data: Market data (OHLCV, indicators)
            side: "LONG" or "SHORT"
        
        Returns:
            {
                "technical_sl": price,
                "safe_zone_sl": price (with buffer),
                "reasoning": explanation
            }
        """
        # Extract data
        recent_low = market_data.get("recent_low", entry_price * 0.95)
        recent_high = market_data.get("recent_high", entry_price * 1.05)
        support = market_data.get("support", entry_price * 0.97)
        resistance = market_data.get("resistance", entry_price * 1.03)
        atr = market_data.get("atr", entry_price * 0.02)  # 2% default
        
        if side == "LONG":
            # For LONG, stop-loss below entry
            
            # Option 1: Below support
            sl_support = support * 0.995  # 0.5% below support
            
            # Option 2: Below recent low
            sl_swing = recent_low * 0.995
            
            # Option 3: ATR-based (1.5x ATR below entry)
            sl_atr = entry_price - (atr * 1.5)
            
            # Choose the closest to entry (tightest stop)
            technical_sl = max(sl_support, sl_swing, sl_atr)
            
            # Add safety buffer (move stop further down)
            safe_zone_sl = technical_sl * (1 - self.safety_buffer)
            
            reasoning = f"Technical SL based on support (${support:.6f}), recent low (${recent_low:.6f}), and ATR"
        
        else:  # SHORT
            # For SHORT, stop-loss above entry
            
            # Option 1: Above resistance
            sl_resistance = resistance * 1.005
            
            # Option 2: Above recent high
            sl_swing = recent_high * 1.005
            
            # Option 3: ATR-based
            sl_atr = entry_price + (atr * 1.5)
            
            # Choose the closest to entry (tightest stop)
            technical_sl = min(sl_resistance, sl_swing, sl_atr)
            
            # Add safety buffer (move stop further up)
            safe_zone_sl = technical_sl * (1 + self.safety_buffer)
            
            reasoning = f"Technical SL based on resistance (${resistance:.6f}), recent high (${recent_high:.6f}), and ATR"
        
        return {
            "technical_sl": technical_sl,
            "safe_zone_sl": safe_zone_sl,
            "reasoning": reasoning,
            "sl_distance_pct": abs((entry_price - safe_zone_sl) / entry_price * 100)
        }
    
    def calculate_optimal_leverage(
        self,
        entry_price: float,
        stop_loss: float,
        side: str = "LONG",
        max_leverage: int = 100
    ) -> Dict:
        """
        Calculate optimal leverage where stop-loss is ABOVE liquidation price
        
        Args:
            entry_price: Entry price
            stop_loss: Desired stop-loss price
            side: "LONG" or "SHORT"
            max_leverage: Maximum leverage to consider
        
        Returns:
            {
                "max_safe_leverage": int,
                "recommended_leverage": int,
                "liquidation_price": float,
                "sl_vs_liq_buffer": float (%)
            }
        """
        # Find maximum leverage where SL > Liquidation
        max_safe_leverage = 1
        
        for lev in range(1, max_leverage + 1):
            liq_price = self.calculate_liquidation_price(entry_price, lev, side)
            
            if side == "LONG":
                # For LONG: stop_loss must be > liquidation_price
                if stop_loss > liq_price:
                    max_safe_leverage = lev
                else:
                    break
            else:  # SHORT
                # For SHORT: stop_loss must be < liquidation_price
                if stop_loss < liq_price:
                    max_safe_leverage = lev
                else:
                    break
        
        # Recommended leverage (conservative, 50-70% of max)
        recommended_leverage = int(max_safe_leverage * 0.6)
        recommended_leverage = max(1, min(recommended_leverage, max_leverage))
        
        # Calculate final liquidation price
        final_liq_price = self.calculate_liquidation_price(
            entry_price,
            recommended_leverage,
            side
        )
        
        # Buffer between SL and liquidation
        if side == "LONG":
            sl_vs_liq_buffer = (stop_loss - final_liq_price) / entry_price * 100
        else:
            sl_vs_liq_buffer = (final_liq_price - stop_loss) / entry_price * 100
        
        return {
            "max_safe_leverage": max_safe_leverage,
            "recommended_leverage": recommended_leverage,
            "liquidation_price": final_liq_price,
            "sl_vs_liq_buffer_pct": sl_vs_liq_buffer
        }
    
    def generate_risk_suggestion(
        self,
        entry_price: float,
        market_data: Dict,
        side: str = "LONG",
        confidence: float = 7.5,
        portfolio_exposure: float = 0.5
    ) -> Dict:
        """
        Generate comprehensive risk suggestion for Claude
        
        This is a SUGGESTION, not a rule. Claude decides final parameters.
        
        Args:
            entry_price: Entry price
            market_data: Market data
            side: "LONG" or "SHORT"
            confidence: Claude's confidence (0-10)
            portfolio_exposure: Current portfolio exposure (0-1)
        
        Returns:
            Comprehensive risk suggestion
        """
        logger.info(f"🎯 Generating risk suggestion for {side} @ ${entry_price:.6f}")
        
        # Step 1: Find technical stop-loss
        sl_data = self.find_technical_stop_loss(entry_price, market_data, side)
        technical_sl = sl_data["technical_sl"]
        safe_zone_sl = sl_data["safe_zone_sl"]
        
        # Step 2: Calculate optimal leverage
        leverage_data = self.calculate_optimal_leverage(
            entry_price,
            safe_zone_sl,
            side
        )
        
        # Step 3: Adjust based on confidence and exposure
        max_leverage = leverage_data["max_safe_leverage"]
        
        # Confidence adjustment
        if confidence >= 9.0:
            suggested_leverage = int(max_leverage * 0.8)  # 80% of max
        elif confidence >= 8.0:
            suggested_leverage = int(max_leverage * 0.6)  # 60% of max
        elif confidence >= 7.5:
            suggested_leverage = int(max_leverage * 0.4)  # 40% of max
        else:
            suggested_leverage = int(max_leverage * 0.2)  # 20% of max
        
        # Portfolio exposure adjustment
        if portfolio_exposure > 0.7:
            suggested_leverage = int(suggested_leverage * 0.5)  # Reduce by 50%
        elif portfolio_exposure > 0.5:
            suggested_leverage = int(suggested_leverage * 0.7)  # Reduce by 30%
        
        suggested_leverage = max(1, min(suggested_leverage, 100))
        
        # Step 4: Calculate take-profit
        sl_distance = abs(entry_price - safe_zone_sl)
        
        if side == "LONG":
            # Risk/reward 1:2 or 1:3
            take_profit_2r = entry_price + (sl_distance * 2)
            take_profit_3r = entry_price + (sl_distance * 3)
        else:
            take_profit_2r = entry_price - (sl_distance * 2)
            take_profit_3r = entry_price - (sl_distance * 3)
        
        # Build suggestion
        suggestion = {
            "entry_price": entry_price,
            "side": side,
            
            # Stop-loss
            "technical_sl": technical_sl,
            "safe_zone_sl": safe_zone_sl,
            "sl_reasoning": sl_data["reasoning"],
            "sl_distance_pct": sl_data["sl_distance_pct"],
            
            # Leverage
            "max_safe_leverage": max_leverage,
            "suggested_leverage": suggested_leverage,
            "liquidation_price": self.calculate_liquidation_price(
                entry_price, suggested_leverage, side
            ),
            "sl_vs_liq_buffer_pct": leverage_data["sl_vs_liq_buffer_pct"],
            
            # Take-profit
            "take_profit_2r": take_profit_2r,
            "take_profit_3r": take_profit_3r,
            
            # Context
            "confidence": confidence,
            "portfolio_exposure": portfolio_exposure,
            
            # Summary
            "summary": self._generate_summary(
                entry_price, safe_zone_sl, suggested_leverage,
                take_profit_2r, side, confidence
            )
        }
        
        logger.info(
            f"✅ Risk suggestion: {side} @ ${entry_price:.6f}, "
            f"SL: ${safe_zone_sl:.6f}, Leverage: {suggested_leverage}x"
        )
        
        return suggestion
    
    def _generate_summary(
        self,
        entry: float,
        sl: float,
        leverage: int,
        tp: float,
        side: str,
        confidence: float
    ) -> str:
        """Generate human-readable summary"""
        
        sl_distance = abs((entry - sl) / entry * 100)
        tp_distance = abs((tp - entry) / entry * 100)
        risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0
        
        summary = f"""
RISK SUGGESTION (Confidence: {confidence:.1f}/10):

Entry: ${entry:.6f}
Stop-Loss: ${sl:.6f} ({sl_distance:.2f}% from entry)
Take-Profit: ${tp:.6f} ({tp_distance:.2f}% from entry)
Leverage: {leverage}x
Risk/Reward: 1:{risk_reward:.1f}

This is a SUGGESTION based on technical analysis.
YOU (Claude) decide final parameters based on full context.
"""
        
        return summary.strip()
    
    def validate_position(
        self,
        entry_price: float,
        stop_loss: float,
        leverage: int,
        side: str
    ) -> Dict:
        """
        Validate position parameters
        
        Returns:
            {
                "valid": bool,
                "warnings": list,
                "liquidation_price": float
            }
        """
        warnings = []
        
        # Calculate liquidation
        liq_price = self.calculate_liquidation_price(entry_price, leverage, side)
        
        # Check if SL is safe
        if side == "LONG":
            if stop_loss <= liq_price:
                warnings.append(
                    f"⚠️ DANGER: Stop-loss (${stop_loss:.6f}) is BELOW liquidation (${liq_price:.6f})! "
                    f"You will be liquidated before stop-loss triggers!"
                )
        else:  # SHORT
            if stop_loss >= liq_price:
                warnings.append(
                    f"⚠️ DANGER: Stop-loss (${stop_loss:.6f}) is ABOVE liquidation (${liq_price:.6f})! "
                    f"You will be liquidated before stop-loss triggers!"
                )
        
        # Check leverage sanity
        if leverage > 20:
            warnings.append(f"⚠️ HIGH LEVERAGE: {leverage}x is very risky!")
        
        # Check SL distance
        sl_distance_pct = abs((entry_price - stop_loss) / entry_price * 100)
        if sl_distance_pct < 0.5:
            warnings.append(f"⚠️ TIGHT STOP: {sl_distance_pct:.2f}% SL may trigger on noise")
        elif sl_distance_pct > 10:
            warnings.append(f"⚠️ WIDE STOP: {sl_distance_pct:.2f}% SL is very far")
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "liquidation_price": liq_price
        }
