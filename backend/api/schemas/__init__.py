"""
Alpha AI Autotrader - Pydantic Schemas
"""
from .auth import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    ChangePasswordRequest,
    MessageResponse
)

from .trading import (
    APIKeyConfig,
    TradingConfig,
    ChatMessage,
    ChatResponse,
    ClosePositionRequest,
    ManualTradeRequest,
    SignalResponse,
    PositionResponse,
    PerformanceResponse,
    TradingStatusResponse
)

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "ChangePasswordRequest",
    "MessageResponse",
    # Trading schemas
    "APIKeyConfig",
    "TradingConfig",
    "ChatMessage",
    "ChatResponse",
    "ClosePositionRequest",
    "ManualTradeRequest",
    "SignalResponse",
    "PositionResponse",
    "PerformanceResponse",
    "TradingStatusResponse",
]
