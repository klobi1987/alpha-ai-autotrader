"""
Alpha AI Autotrader - Custom Exceptions
Specific exception types for better error handling and debugging
"""
from typing import Optional, Dict, Any


# ==================== Base Exceptions ====================

class AlphaTraderException(Exception):
    """Base exception for all Alpha AI Autotrader errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ==================== Configuration Exceptions ====================

class ConfigurationError(AlphaTraderException):
    """Raised when configuration is invalid or missing"""
    pass


class APIKeyMissingError(ConfigurationError):
    """Raised when required API key is not configured"""
    pass


class InvalidSettingsError(ConfigurationError):
    """Raised when settings are invalid"""
    pass


# ==================== Trading Exceptions ====================

class TradingError(AlphaTraderException):
    """Base exception for trading-related errors"""
    pass


class InsufficientBalanceError(TradingError):
    """Raised when account balance is insufficient for trade"""
    pass


class PositionNotFoundError(TradingError):
    """Raised when requested position does not exist"""
    pass


class OrderExecutionError(TradingError):
    """Raised when order execution fails"""
    pass


class InvalidOrderError(TradingError):
    """Raised when order parameters are invalid"""
    pass


class MarketClosedError(TradingError):
    """Raised when trying to trade while market is closed"""
    pass


class LeverageTooHighError(TradingError):
    """Raised when requested leverage exceeds limits"""
    pass


class RiskLimitExceededError(TradingError):
    """Raised when trade would exceed risk limits"""
    pass


# ==================== Exchange Exceptions ====================

class ExchangeError(AlphaTraderException):
    """Base exception for exchange-related errors"""
    pass


class ExchangeConnectionError(ExchangeError):
    """Raised when connection to exchange fails"""
    pass


class ExchangeAuthError(ExchangeError):
    """Raised when exchange authentication fails"""
    pass


class ExchangeRateLimitError(ExchangeError):
    """Raised when exchange rate limit is exceeded"""
    pass


class SymbolNotFoundError(ExchangeError):
    """Raised when trading symbol is not found on exchange"""
    pass


class ExchangeMaintenanceError(ExchangeError):
    """Raised when exchange is under maintenance"""
    pass


# ==================== Data Exceptions ====================

class DataError(AlphaTraderException):
    """Base exception for data-related errors"""
    pass


class DataFetchError(DataError):
    """Raised when data fetching fails"""
    pass


class InvalidDataError(DataError):
    """Raised when data is invalid or corrupted"""
    pass


class DataNotFoundError(DataError):
    """Raised when requested data is not found"""
    pass


class CacheError(DataError):
    """Raised when cache operations fail"""
    pass


# ==================== AI/ML Exceptions ====================

class AIError(AlphaTraderException):
    """Base exception for AI-related errors"""
    pass


class ModelLoadError(AIError):
    """Raised when ML model loading fails"""
    pass


class PredictionError(AIError):
    """Raised when prediction fails"""
    pass


class FeatureExtractionError(AIError):
    """Raised when feature extraction fails"""
    pass


class TrainingError(AIError):
    """Raised when model training fails"""
    pass


class AIProviderError(AIError):
    """Raised when AI provider (Claude, OpenRouter) returns error"""
    pass


class ConsensusError(AIError):
    """Raised when AI consensus cannot be reached"""
    pass


# ==================== Integration Exceptions ====================

class IntegrationError(AlphaTraderException):
    """Base exception for external integration errors"""
    pass


class LunarCrushError(IntegrationError):
    """Raised when LunarCrush API fails"""
    pass


class ClaudeAPIError(IntegrationError):
    """Raised when Claude API fails"""
    pass


class OpenRouterError(IntegrationError):
    """Raised when OpenRouter API fails"""
    pass


class WebResearchError(IntegrationError):
    """Raised when web research fails"""
    pass


# ==================== Database Exceptions ====================

class DatabaseError(AlphaTraderException):
    """Base exception for database errors"""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when database record is not found"""
    pass


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create duplicate record"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


# ==================== Validation Exceptions ====================

class ValidationError(AlphaTraderException):
    """Base exception for validation errors"""
    pass


class InvalidSymbolError(ValidationError):
    """Raised when trading symbol is invalid"""
    pass


class InvalidAmountError(ValidationError):
    """Raised when trade amount is invalid"""
    pass


class InvalidPriceError(ValidationError):
    """Raised when price is invalid"""
    pass


class InvalidTimeframeError(ValidationError):
    """Raised when timeframe is invalid"""
    pass


# ==================== WebSocket Exceptions ====================

class WebSocketError(AlphaTraderException):
    """Base exception for WebSocket errors"""
    pass


class WebSocketConnectionError(WebSocketError):
    """Raised when WebSocket connection fails"""
    pass


class WebSocketAuthError(WebSocketError):
    """Raised when WebSocket authentication fails"""
    pass


# ==================== Pattern Discovery Exceptions ====================

class PatternError(AlphaTraderException):
    """Base exception for pattern-related errors"""
    pass


class PatternNotFoundError(PatternError):
    """Raised when pattern is not found"""
    pass


class PatternValidationError(PatternError):
    """Raised when pattern validation fails"""
    pass


class ClusteringError(PatternError):
    """Raised when clustering algorithm fails"""
    pass


# ==================== Helper Functions ====================

def get_exception_details(exc: Exception) -> Dict[str, Any]:
    """Extract details from any exception for logging"""
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "details": getattr(exc, 'details', {}),
        "module": getattr(exc, '__module__', None)
    }


def is_retryable_error(exc: Exception) -> bool:
    """
    Determine if an error is retryable

    Retryable errors:
    - Connection errors
    - Rate limit errors
    - Temporary exchange errors

    Non-retryable errors:
    - Authentication errors
    - Validation errors
    - Configuration errors
    """
    retryable_exceptions = (
        ExchangeConnectionError,
        ExchangeRateLimitError,
        DataFetchError,
        CacheError,
        DatabaseConnectionError,
        WebSocketConnectionError,
        ExchangeMaintenanceError
    )

    return isinstance(exc, retryable_exceptions)


def should_alert_admin(exc: Exception) -> bool:
    """
    Determine if an error should trigger admin alert

    Alert for:
    - Critical trading errors
    - Authentication failures
    - Database errors
    - Exchange connection issues
    """
    critical_exceptions = (
        OrderExecutionError,
        InsufficientBalanceError,
        ExchangeAuthError,
        DatabaseConnectionError,
        APIKeyMissingError,
        ConfigurationError
    )

    return isinstance(exc, critical_exceptions)
