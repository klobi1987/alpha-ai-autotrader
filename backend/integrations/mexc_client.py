"""
Alpha AI Autotrader - MEXC Exchange Integration
Unified wrapper for Spot and Futures trading via ccxt
"""
import ccxt
from typing import Dict, List, Optional, Literal
from loguru import logger
from datetime import datetime


class MEXCClient:
    """
    Unified MEXC client for Spot and Futures trading
    
    Supports:
    - Spot trading
    - Futures/Perpetual trading
    - Market data (unlimited, free)
    - Position management
    - Risk management
    """
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        testnet: bool = False
    ):
        """
        Args:
            api_key: MEXC API key
            secret_key: MEXC secret key
            testnet: Use testnet (if available)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # Initialize ccxt exchange
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # Default to spot
            }
        })
        
        if testnet:
            # MEXC testnet URLs (if available)
            self.exchange.set_sandbox_mode(True)
        
        logger.info(f"MEXC client initialized (testnet={testnet})")
    
    # ==================== MARKET DATA (Public) ====================
    
    def fetch_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
        
        Returns:
            {last, bid, ask, volume, high, low, change, percentage}
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book depth
        
        Returns:
            {bids: [[price, amount], ...], asks: [[price, amount], ...]}
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            return orderbook
        except Exception as e:
            logger.error(f"Failed to fetch orderbook for {symbol}: {e}")
            raise
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[List]:
        """
        Get candlestick data
        
        Args:
            symbol: Trading pair
            timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
            limit: Number of candles
        
        Returns:
            [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            klines = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return klines
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise
    
    def fetch_markets(self) -> List[Dict]:
        """Get all available markets"""
        try:
            markets = self.exchange.fetch_markets()
            return markets
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            raise
    
    # ==================== ACCOUNT (Private) ====================
    
    def fetch_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            {
                'USDT': {free: 10000, used: 0, total: 10000},
                'BTC': {free: 0.5, used: 0.1, total: 0.6}
            }
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise
    
    def get_available_balance(self, currency: str = 'USDT') -> float:
        """Get available (free) balance for a currency"""
        try:
            balance = self.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
        except Exception as e:
            logger.error(f"Failed to get available balance: {e}")
            return 0.0
    
    # ==================== SPOT TRADING ====================
    
    def create_spot_market_order(
        self,
        symbol: str,
        side: Literal['buy', 'sell'],
        amount: float
    ) -> Dict:
        """
        Create spot market order (instant execution)
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: "buy" or "sell"
            amount: Quantity to trade
        
        Returns:
            Order info dict
        """
        try:
            self.exchange.options['defaultType'] = 'spot'
            
            if side == 'buy':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            logger.info(f"Spot market {side} order created: {symbol} {amount}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to create spot market order: {e}")
            raise
    
    def create_spot_limit_order(
        self,
        symbol: str,
        side: Literal['buy', 'sell'],
        amount: float,
        price: float
    ) -> Dict:
        """Create spot limit order"""
        try:
            self.exchange.options['defaultType'] = 'spot'
            
            if side == 'buy':
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            else:
                order = self.exchange.create_limit_sell_order(symbol, amount, price)
            
            logger.info(f"Spot limit {side} order created: {symbol} {amount} @ {price}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to create spot limit order: {e}")
            raise
    
    # ==================== FUTURES TRADING ====================
    
    def fetch_funding_rate(self, symbol: str) -> Dict:
        """
        Get current funding rate for perpetual futures
        
        Args:
            symbol: Futures symbol (e.g., "BTC/USDT:USDT")
        
        Returns:
            {symbol, rate, timestamp, nextFundingTime}
        """
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            return funding
        except Exception as e:
            logger.error(f"Failed to fetch funding rate for {symbol}: {e}")
            raise
    
    def fetch_open_interest(self, symbol: str) -> Dict:
        """Get open interest for futures"""
        try:
            oi = self.exchange.fetch_open_interest(symbol)
            return oi
        except Exception as e:
            logger.error(f"Failed to fetch open interest: {e}")
            raise
    
    def set_leverage(self, leverage: int, symbol: str):
        """
        Set leverage for futures trading
        
        Args:
            leverage: Leverage multiplier (1-200)
            symbol: Futures symbol
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise
    
    def create_futures_market_order(
        self,
        symbol: str,
        side: Literal['buy', 'sell'],
        amount: float,
        leverage: int = 1,
        reduce_only: bool = False
    ) -> Dict:
        """
        Create futures market order
        
        Args:
            symbol: Futures symbol (e.g., "BTC/USDT:USDT")
            side: "buy" (long) or "sell" (short)
            amount: Quantity
            leverage: Leverage multiplier
            reduce_only: Close position only (don't open new)
        
        Returns:
            Order info dict
        """
        try:
            self.exchange.options['defaultType'] = 'swap'  # Perpetual futures
            
            # Set leverage first
            if leverage > 1:
                self.set_leverage(leverage, symbol)
            
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
            
            if side == 'buy':
                order = self.exchange.create_market_buy_order(symbol, amount, params)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount, params)
            
            logger.info(f"Futures market {side} order created: {symbol} {amount} @ {leverage}x")
            return order
        
        except Exception as e:
            logger.error(f"Failed to create futures market order: {e}")
            raise
    
    def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open futures positions
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            List of position dicts
        """
        try:
            self.exchange.options['defaultType'] = 'swap'
            positions = self.exchange.fetch_positions(symbol)
            
            # Filter out zero positions
            open_positions = [
                pos for pos in positions
                if float(pos.get('contracts', 0)) > 0
            ]
            
            return open_positions
        
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            raise
    
    def close_position(self, symbol: str) -> Dict:
        """
        Close an open futures position
        
        Args:
            symbol: Futures symbol
        
        Returns:
            Order info
        """
        try:
            positions = self.fetch_positions(symbol)
            
            if not positions:
                logger.warning(f"No open position for {symbol}")
                return {}
            
            position = positions[0]
            side = position.get('side')  # 'long' or 'short'
            contracts = float(position.get('contracts', 0))
            
            # Close position (opposite side)
            close_side = 'sell' if side == 'long' else 'buy'
            
            order = self.create_futures_market_order(
                symbol,
                close_side,
                contracts,
                reduce_only=True
            )
            
            logger.info(f"Position closed: {symbol}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            raise
    
    # ==================== ORDER MANAGEMENT ====================
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an open order"""
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """Cancel all open orders for a symbol"""
        try:
            result = self.exchange.cancel_all_orders(symbol)
            logger.info(f"All orders cancelled for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise
    
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise
    
    def fetch_closed_orders(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get order history"""
        try:
            orders = self.exchange.fetch_closed_orders(symbol, limit=limit)
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch closed orders: {e}")
            raise
    
    # ==================== UTILITY ====================
    
    def calculate_position_size(
        self,
        symbol: str,
        risk_usd: float,
        stop_loss_percent: float
    ) -> float:
        """
        Calculate position size based on risk
        
        Args:
            symbol: Trading pair
            risk_usd: Amount willing to risk in USD
            stop_loss_percent: Stop-loss distance in %
        
        Returns:
            Position size in base currency
        """
        try:
            ticker = self.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Position size = Risk / (Price * Stop Loss %)
            position_size = risk_usd / (current_price * (stop_loss_percent / 100))
            
            return position_size
        
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            return 0.0
    
    def get_liquidation_price(
        self,
        entry_price: float,
        leverage: int,
        side: Literal['long', 'short']
    ) -> float:
        """
        Calculate liquidation price
        
        Args:
            entry_price: Entry price
            leverage: Leverage multiplier
            side: "long" or "short"
        
        Returns:
            Liquidation price
        """
        # Simplified calculation (actual may vary by exchange)
        if side == 'long':
            liq_price = entry_price * (1 - 1/leverage * 0.9)
        else:
            liq_price = entry_price * (1 + 1/leverage * 0.9)
        
        return liq_price

    # ==================== SPOT/FUTURES TRANSFER ====================
    
    def transfer_spot_to_futures(self, currency: str, amount: float) -> Dict:
        """
        Transfer funds from Spot wallet to Futures wallet
        
        Args:
            currency: Currency to transfer (e.g., "USDT")
            amount: Amount to transfer
        
        Returns:
            Transfer result
        """
        try:
            result = self.exchange.transfer(currency, amount, 'spot', 'swap')
            logger.info(f"✅ Transferred {amount} {currency} from Spot to Futures")
            return result
        except Exception as e:
            logger.error(f"Failed to transfer spot to futures: {e}")
            raise
    
    def transfer_futures_to_spot(self, currency: str, amount: float) -> Dict:
        """
        Transfer funds from Futures wallet to Spot wallet
        
        Args:
            currency: Currency to transfer (e.g., "USDT")
            amount: Amount to transfer
        
        Returns:
            Transfer result
        """
        try:
            result = self.exchange.transfer(currency, amount, 'swap', 'spot')
            logger.info(f"✅ Transferred {amount} {currency} from Futures to Spot")
            return result
        except Exception as e:
            logger.error(f"Failed to transfer futures to spot: {e}")
            raise
    
    async def execute_spot_trade(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Dict:
        """
        Execute spot trade (high-level wrapper)
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: "LONG" (buy) or "SHORT" (not supported on spot, will raise error)
            quantity: Amount to trade
        
        Returns:
            Trade result
        """
        if side == "SHORT":
            raise ValueError("SHORT not supported on spot market. Use futures instead.")
        
        # Convert LONG to buy
        mexc_side = "buy" if side == "LONG" else "sell"
        
        try:
            order = self.create_spot_market_order(symbol, mexc_side, quantity)
            
            return {
                "success": True,
                "order_id": order.get("id"),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": order.get("price"),
                "market": "SPOT"
            }
        except Exception as e:
            logger.error(f"Spot trade failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_futures_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        leverage: int = 1,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        Execute futures trade (high-level wrapper)
        
        Args:
            symbol: Futures symbol (e.g., "BTC/USDT:USDT")
            side: "LONG" (buy) or "SHORT" (sell)
            quantity: Amount to trade
            leverage: Leverage multiplier
            stop_loss: Stop-loss price (optional)
            take_profit: Take-profit price (optional)
        
        Returns:
            Trade result
        """
        # Convert LONG/SHORT to buy/sell
        mexc_side = "buy" if side == "LONG" else "sell"
        
        try:
            # Execute main order
            order = self.create_futures_market_order(
                symbol,
                mexc_side,
                quantity,
                leverage=leverage
            )
            
            # Set stop-loss if provided
            if stop_loss:
                self._set_stop_loss(symbol, side, quantity, stop_loss)
            
            # Set take-profit if provided
            if take_profit:
                self._set_take_profit(symbol, side, quantity, take_profit)
            
            return {
                "success": True,
                "order_id": order.get("id"),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "leverage": leverage,
                "price": order.get("price"),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "market": "FUTURES"
            }
        except Exception as e:
            logger.error(f"Futures trade failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _set_stop_loss(self, symbol: str, side: str, quantity: float, stop_price: float):
        """Set stop-loss order"""
        try:
            # Stop-loss is opposite side
            sl_side = "sell" if side == "LONG" else "buy"
            
            self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=sl_side,
                amount=quantity,
                params={
                    'stopPrice': stop_price,
                    'reduceOnly': True
                }
            )
            
            logger.info(f"Stop-loss set at {stop_price} for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set stop-loss: {e}")
    
    def _set_take_profit(self, symbol: str, side: str, quantity: float, take_profit_price: float):
        """Set take-profit order"""
        try:
            # Take-profit is opposite side
            tp_side = "sell" if side == "LONG" else "buy"
            
            self.exchange.create_limit_order(
                symbol=symbol,
                side=tp_side,
                amount=quantity,
                price=take_profit_price,
                params={'reduceOnly': True}
            )
            
            logger.info(f"Take-profit set at {take_profit_price} for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set take-profit: {e}")
    
    async def smart_position_transfer(
        self,
        symbol: str,
        from_market: Literal['SPOT', 'FUTURES'],
        to_market: Literal['SPOT', 'FUTURES'],
        reason: str = ""
    ) -> Dict:
        """
        Smart transfer between spot and futures
        
        Claude can use this to:
        - Move from spot to futures for leverage
        - Move from futures to spot for safety
        
        Args:
            symbol: Trading pair
            from_market: Current market
            to_market: Target market
            reason: Claude's reasoning
        
        Returns:
            Transfer result
        """
        logger.info(
            f"🔄 Smart transfer: {symbol} from {from_market} to {to_market}\n"
            f"   Reason: {reason}"
        )
        
        try:
            # Step 1: Close position in from_market
            if from_market == "SPOT":
                # Get spot balance
                balance = self.fetch_balance()
                base_currency = symbol.split("/")[0]
                amount = balance.get(base_currency, {}).get('free', 0)
                
                if amount > 0:
                    # Sell on spot
                    self.create_spot_market_order(symbol, "sell", amount)
                    logger.info(f"Sold {amount} {base_currency} on spot")
            
            else:  # FUTURES
                # Close futures position
                self.close_position(f"{symbol}:USDT")
                logger.info(f"Closed futures position for {symbol}")
            
            # Step 2: Transfer funds
            quote_currency = symbol.split("/")[1]  # Usually USDT
            balance = self.fetch_balance()
            usdt_amount = balance.get(quote_currency, {}).get('free', 0)
            
            if from_market == "SPOT" and to_market == "FUTURES":
                self.transfer_spot_to_futures(quote_currency, usdt_amount)
            elif from_market == "FUTURES" and to_market == "SPOT":
                self.transfer_futures_to_spot(quote_currency, usdt_amount)
            
            # Step 3: Open position in to_market
            # (Claude will decide this in next decision cycle)
            
            logger.info(f"✅ Smart transfer completed: {symbol} → {to_market}")
            
            return {
                "success": True,
                "symbol": symbol,
                "from": from_market,
                "to": to_market,
                "amount_transferred": usdt_amount,
                "reason": reason
            }
        
        except Exception as e:
            logger.error(f"Smart transfer failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
