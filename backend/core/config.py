"""
Alpha AI Autotrader - Configuration Management
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, List
import os
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = Field(default="Alpha AI Autotrader", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security - CORS
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ALLOWED_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")

    # Security - JWT Authentication
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # Security - API Keys
    api_key_header_name: str = Field(default="X-API-Key", alias="API_KEY_HEADER_NAME")
    require_api_key: bool = Field(default=False, alias="REQUIRE_API_KEY")
    api_keys: str = Field(default="", alias="API_KEYS")  # Comma-separated list

    # Security - Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")  # Requests per minute
    rate_limit_strategy: str = Field(default="fixed-window", alias="RATE_LIMIT_STRATEGY")  # fixed-window or moving-window

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./alpha_autotrader.db",
        alias="DATABASE_URL"
    )
    
    # LunarCrush
    lunarcrush_api_key: str = Field(default="", alias="LUNARCRUSH_API_KEY")
    lunarcrush_cache_ttl: int = Field(default=300, alias="LUNARCRUSH_CACHE_TTL")  # 5 min
    
    # MEXC
    mexc_api_key: str = Field(default="", alias="MEXC_API_KEY")
    mexc_secret_key: str = Field(default="", alias="MEXC_SECRET_KEY")
    mexc_testnet: bool = Field(default=False, alias="MEXC_TESTNET")
    
    # Trading
    trading_mode: Literal["testing", "live"] = Field(default="testing", alias="TRADING_MODE")
    max_position_size_usd: float = Field(default=500.0, alias="MAX_POSITION_SIZE_USD")
    max_concurrent_positions: int = Field(default=3, alias="MAX_CONCURRENT_POSITIONS")
    max_leverage: int = Field(default=5, alias="MAX_LEVERAGE")
    stop_loss_percent: float = Field(default=2.0, alias="STOP_LOSS_PERCENT")
    min_confidence_score: float = Field(default=7.5, alias="MIN_CONFIDENCE_SCORE")
    
    # Risk Management
    max_portfolio_risk_percent: float = Field(default=10.0, alias="MAX_PORTFOLIO_RISK_PERCENT")
    position_size_method: Literal["fixed", "kelly", "volatility"] = Field(
        default="fixed",
        alias="POSITION_SIZE_METHOD"
    )
    
    # Pattern Detection
    enable_pattern_discovery: bool = Field(default=True, alias="ENABLE_PATTERN_DISCOVERY")
    pattern_discovery_interval: int = Field(default=604800, alias="PATTERN_DISCOVERY_INTERVAL")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/alpha_autotrader.log", alias="LOG_FILE")
    
    # Telegram (Optional)
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    
    # Advanced
    enable_websocket: bool = Field(default=True, alias="ENABLE_WEBSOCKET")
    enable_auto_trading: bool = Field(default=False, alias="ENABLE_AUTO_TRADING")
    enable_futures_trading: bool = Field(default=True, alias="ENABLE_FUTURES_TRADING")
    enable_spot_trading: bool = Field(default=True, alias="ENABLE_SPOT_TRADING")
    
    # AI Models
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    claude_api_key: str = Field(default="", alias="CLAUDE_API_KEY")
    enable_multi_ai_consensus: bool = Field(default=True, alias="ENABLE_MULTI_AI_CONSENSUS")
    
    # Scanning
    scan_interval: int = Field(default=300, alias="SCAN_INTERVAL")  # 5 minutes
    top_coins_to_scan: int = Field(default=1000, alias="TOP_COINS_TO_SCAN")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def is_configured(self) -> bool:
        """Check if essential API keys are configured"""
        return bool(
            self.lunarcrush_api_key and
            self.mexc_api_key and
            self.mexc_secret_key
        )

    def is_live_trading_enabled(self) -> bool:
        """Check if live trading is enabled and configured"""
        return (
            self.trading_mode == "live" and
            self.enable_auto_trading and
            self.is_configured()
        )

    def get_cors_origins(self) -> List[str]:
        """Get list of allowed CORS origins"""
        if not self.cors_allowed_origins:
            return []
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    def get_cors_methods(self) -> List[str]:
        """Get list of allowed CORS methods"""
        if not self.cors_allow_methods:
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",")]

    def get_api_keys(self) -> List[str]:
        """Get list of valid API keys"""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(_settings.log_file), exist_ok=True)
    return _settings

# For backward compatibility
settings = get_settings()
