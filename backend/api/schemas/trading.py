"""
Alpha AI Autotrader - Trading API Schemas
Pydantic models for trading endpoints with comprehensive validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


class APIKeyConfig(BaseModel):
    """API keys configuration with validation"""
    lunarcrush_api_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="LunarCrush API key"
    )
    mexc_api_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="MEXC API key"
    )
    mexc_secret_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="MEXC secret key"
    )
    openrouter_api_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="OpenRouter API key"
    )
    claude_api_key: Optional[str] = Field(
        None,
        min_length=10,
        max_length=200,
        description="Claude API key"
    )

    @validator('*')
    def no_whitespace_only(cls, v):
        """Ensure strings are not just whitespace"""
        if isinstance(v, str) and v and not v.strip():
            raise ValueError('Must not be whitespace only')
        return v.strip() if isinstance(v, str) and v else v


class TradingConfig(BaseModel):
    """Trading configuration with strict validation"""
    trading_mode: Literal["testing", "live"] = Field(
        default="testing",
        description="Trading mode: testing (paper trading) or live (real money)"
    )
    max_position_size_usd: float = Field(
        default=500,
        ge=10,  # Greater than or equal to $10
        le=100000,  # Less than or equal to $100k
        description="Maximum position size in USD"
    )
    max_concurrent_positions: int = Field(
        default=3,
        ge=1,
        le=50,
        description="Maximum number of concurrent open positions"
    )
    max_leverage: int = Field(
        default=5,
        ge=1,
        le=125,  # MEXC max leverage
        description="Maximum leverage multiplier"
    )
    stop_loss_percent: float = Field(
        default=2.0,
        gt=0,  # Greater than 0
        le=50,  # Max 50% stop loss
        description="Stop loss percentage"
    )
    min_confidence_score: float = Field(
        default=7.5,
        ge=0,
        le=10,
        description="Minimum AI confidence score to execute trades (0-10)"
    )
    enable_auto_trading: bool = Field(
        default=False,
        description="Enable automatic trade execution"
    )

    @validator('max_leverage')
    def validate_leverage(cls, v, values):
        """Warn about high leverage in live mode"""
        if values.get('trading_mode') == 'live' and v > 20:
            # Note: Pydantic validators can't warn, only validate or raise
            # Consider logging this warning in the route handler instead
            pass
        return v


class ChatMessage(BaseModel):
    """Chat message with validation"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message to AI assistant"
    )

    @validator('message')
    def not_empty(cls, v):
        """Ensure message is not just whitespace"""
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response"""
    message: str = Field(..., description="AI assistant response")
    timestamp: str = Field(..., description="ISO format timestamp")


class ClosePositionRequest(BaseModel):
    """Request to close a position"""
    symbol: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Trading symbol (e.g., BTCUSDT)"
    )
    quantity: Optional[float] = Field(
        None,
        gt=0,
        description="Quantity to close (optional, closes all if not specified)"
    )

    @validator('symbol')
    def validate_symbol(cls, v):
        """Ensure symbol is uppercase and alphanumeric"""
        v = v.strip().upper()
        if not v.replace('/', '').isalnum():
            raise ValueError('Symbol must be alphanumeric (slashes allowed)')
        return v


class ManualTradeRequest(BaseModel):
    """Manual trade execution request"""
    symbol: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Trading symbol"
    )
    side: Literal["LONG", "SHORT", "BUY", "SELL"] = Field(
        ...,
        description="Trade direction"
    )
    quantity: float = Field(
        ...,
        gt=0,
        description="Trade quantity"
    )
    leverage: int = Field(
        default=1,
        ge=1,
        le=125,
        description="Leverage multiplier"
    )
    stop_loss: Optional[float] = Field(
        None,
        gt=0,
        description="Stop loss price"
    )
    take_profit: Optional[float] = Field(
        None,
        gt=0,
        description="Take profit price"
    )
    order_type: Literal["market", "limit"] = Field(
        default="market",
        description="Order type"
    )
    limit_price: Optional[float] = Field(
        None,
        gt=0,
        description="Limit price (required if order_type=limit)"
    )

    @validator('symbol')
    def validate_symbol(cls, v):
        """Uppercase and validate symbol"""
        return v.strip().upper()

    @validator('limit_price')
    def validate_limit_price(cls, v, values):
        """Ensure limit price is provided for limit orders"""
        if values.get('order_type') == 'limit' and not v:
            raise ValueError('limit_price is required for limit orders')
        return v


class SignalResponse(BaseModel):
    """Trading signal response"""
    id: int
    symbol: str
    decision: str
    confidence: float
    reasoning: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    leverage: int
    timestamp: str


class PositionResponse(BaseModel):
    """Position response"""
    id: int
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    leverage: int
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl_usd: float
    pnl_pct: float
    opened_at: str


class PerformanceResponse(BaseModel):
    """Performance metrics response"""
    total_trades: int
    win_rate: float
    profit_factor: float
    total_pnl_usd: float
    total_pnl_pct: float
    best_trade: Optional[dict]
    worst_trade: Optional[dict]


class TradingStatusResponse(BaseModel):
    """Trading system status"""
    status: str
    running: bool
    last_scan: Optional[str]
    total_scans: int
    message: Optional[str] = None
