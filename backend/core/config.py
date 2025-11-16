"""
Alpha AI Autotrader - Configuration Management
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = Field(default="Alpha AI Autotrader", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
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


# Global settings instance
settings = Settings()


# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
