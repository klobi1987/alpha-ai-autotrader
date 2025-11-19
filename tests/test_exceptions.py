"""
Alpha AI Autotrader - Exception Tests
Tests for custom exception hierarchy and helpers
"""
import pytest
from backend.core.exceptions import (
    # Base
    AlphaTraderException,
    # Configuration
    ConfigurationError,
    APIKeyMissingError,
    # Trading
    TradingError,
    PositionNotFoundError,
    OrderExecutionError,
    InsufficientBalanceError,
    # Exchange
    ExchangeError,
    ExchangeConnectionError,
    ExchangeRateLimitError,
    # Data
    DataError,
    DataFetchError,
    InvalidDataError,
    # AI
    AIError,
    ModelLoadError,
    PredictionError,
    # Database
    DatabaseError,
    RecordNotFoundError,
    # Helpers
    get_exception_details,
    is_retryable_error,
    should_alert_admin
)


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy"""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from AlphaTraderException"""
        exceptions_to_test = [
            ConfigurationError,
            TradingError,
            ExchangeError,
            DataError,
            AIError,
            DatabaseError
        ]

        for exc_class in exceptions_to_test:
            exc = exc_class("Test message")
            assert isinstance(exc, AlphaTraderException)
            assert isinstance(exc, Exception)

    def test_specific_exceptions_inherit_from_category(self):
        """Test that specific exceptions inherit from their category"""
        # Trading exceptions
        assert issubclass(PositionNotFoundError, TradingError)
        assert issubclass(OrderExecutionError, TradingError)
        assert issubclass(InsufficientBalanceError, TradingError)

        # Exchange exceptions
        assert issubclass(ExchangeConnectionError, ExchangeError)
        assert issubclass(ExchangeRateLimitError, ExchangeError)

        # Data exceptions
        assert issubclass(DataFetchError, DataError)
        assert issubclass(InvalidDataError, DataError)

        # AI exceptions
        assert issubclass(ModelLoadError, AIError)
        assert issubclass(PredictionError, AIError)

        # Database exceptions
        assert issubclass(RecordNotFoundError, DatabaseError)


class TestExceptionCreation:
    """Test creating exceptions with messages and details"""

    def test_create_exception_with_message(self):
        """Test creating exception with message"""
        exc = ConfigurationError("API key missing")

        assert str(exc) == "API key missing"
        assert exc.message == "API key missing"

    def test_create_exception_with_details(self):
        """Test creating exception with details dict"""
        exc = PositionNotFoundError(
            "Position not found",
            details={"symbol": "BTCUSDT", "user_id": 123}
        )

        assert exc.message == "Position not found"
        assert exc.details["symbol"] == "BTCUSDT"
        assert exc.details["user_id"] == 123

    def test_exception_without_details(self):
        """Test creating exception without details"""
        exc = DataFetchError("Failed to fetch data")

        assert exc.message == "Failed to fetch data"
        assert exc.details == {}


class TestExceptionRaising:
    """Test raising and catching custom exceptions"""

    def test_raise_and_catch_specific_exception(self):
        """Test raising and catching specific exception"""
        with pytest.raises(PositionNotFoundError) as exc_info:
            raise PositionNotFoundError("Position not found")

        assert "Position not found" in str(exc_info.value)

    def test_catch_base_exception(self):
        """Test catching via base exception class"""
        try:
            raise PositionNotFoundError("Test")
        except TradingError:
            # Should catch because PositionNotFoundError inherits from TradingError
            pass
        else:
            pytest.fail("Should have caught TradingError")

    def test_catch_alpha_trader_exception(self):
        """Test catching via AlphaTraderException base"""
        try:
            raise DataFetchError("Test")
        except AlphaTraderException:
            # Should catch any custom exception
            pass
        else:
            pytest.fail("Should have caught AlphaTraderException")


class TestGetExceptionDetails:
    """Test get_exception_details helper"""

    def test_get_details_from_custom_exception(self):
        """Test extracting details from custom exception"""
        exc = PositionNotFoundError(
            "Position not found",
            details={"symbol": "BTCUSDT"}
        )

        details = get_exception_details(exc)

        assert details["type"] == "PositionNotFoundError"
        assert details["message"] == "Position not found"
        assert details["details"]["symbol"] == "BTCUSDT"

    def test_get_details_from_standard_exception(self):
        """Test extracting details from standard Python exception"""
        exc = ValueError("Invalid value")

        details = get_exception_details(exc)

        assert details["type"] == "ValueError"
        assert details["message"] == "Invalid value"

    def test_get_details_includes_module(self):
        """Test that details include module information"""
        exc = DataFetchError("Test")

        details = get_exception_details(exc)

        assert "module" in details


class TestIsRetryableError:
    """Test is_retryable_error helper"""

    def test_retryable_errors(self):
        """Test that certain errors are marked as retryable"""
        retryable = [
            ExchangeConnectionError("Connection failed"),
            ExchangeRateLimitError("Rate limit exceeded"),
            DataFetchError("Fetch failed"),
        ]

        for exc in retryable:
            assert is_retryable_error(exc) is True

    def test_non_retryable_errors(self):
        """Test that certain errors are not retryable"""
        non_retryable = [
            ConfigurationError("Config error"),
            APIKeyMissingError("API key missing"),
            InvalidDataError("Invalid data"),
            PositionNotFoundError("Position not found"),
        ]

        for exc in non_retryable:
            assert is_retryable_error(exc) is False

    def test_standard_exceptions_not_retryable(self):
        """Test that standard exceptions are not retryable"""
        exc = ValueError("Test")

        assert is_retryable_error(exc) is False


class TestShouldAlertAdmin:
    """Test should_alert_admin helper"""

    def test_critical_errors_trigger_alert(self):
        """Test that critical errors trigger admin alerts"""
        critical = [
            OrderExecutionError("Order failed"),
            InsufficientBalanceError("Insufficient balance"),
            ConfigurationError("Config error"),
            APIKeyMissingError("API key missing"),
        ]

        for exc in critical:
            assert should_alert_admin(exc) is True

    def test_non_critical_errors_no_alert(self):
        """Test that non-critical errors don't trigger alerts"""
        non_critical = [
            DataFetchError("Fetch failed"),
            InvalidDataError("Invalid data"),
            ModelLoadError("Model not found"),
        ]

        for exc in non_critical:
            assert should_alert_admin(exc) is False


class TestExceptionUsagePatterns:
    """Test common exception usage patterns"""

    def test_reraise_custom_exception(self):
        """Test re-raising custom exception"""
        def inner_function():
            raise DataFetchError("Inner error")

        def outer_function():
            try:
                inner_function()
            except DataError:
                raise  # Re-raise

        with pytest.raises(DataFetchError):
            outer_function()

    def test_catch_and_wrap_exception(self):
        """Test catching one exception and raising another"""
        def problematic_function():
            raise ValueError("Invalid input")

        def wrapper_function():
            try:
                problematic_function()
            except ValueError as e:
                raise InvalidDataError(f"Data validation failed: {e}")

        with pytest.raises(InvalidDataError) as exc_info:
            wrapper_function()

        assert "Data validation failed" in str(exc_info.value)
        assert "Invalid input" in str(exc_info.value)

    def test_exception_chaining(self):
        """Test exception chaining with from"""
        def inner():
            raise ValueError("Original error")

        def outer():
            try:
                inner()
            except ValueError as e:
                raise DataFetchError("Failed to fetch") from e

        with pytest.raises(DataFetchError) as exc_info:
            outer()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)


class TestExceptionMessages:
    """Test exception message formatting"""

    def test_exception_str_representation(self):
        """Test string representation of exception"""
        exc = PositionNotFoundError("Position BTCUSDT not found")

        assert str(exc) == "Position BTCUSDT not found"

    def test_exception_with_details_str(self):
        """Test string representation includes message"""
        exc = OrderExecutionError(
            "Order failed",
            details={"order_id": "12345"}
        )

        # String representation should include the message
        assert "Order failed" in str(exc)


class TestMultipleExceptionTypes:
    """Test handling multiple exception types"""

    def test_catch_multiple_specific_exceptions(self):
        """Test catching multiple specific exception types"""
        def raise_random_error(error_type: str):
            if error_type == "position":
                raise PositionNotFoundError("Position not found")
            elif error_type == "balance":
                raise InsufficientBalanceError("Insufficient balance")
            elif error_type == "order":
                raise OrderExecutionError("Order failed")

        # Test catching each type
        with pytest.raises(PositionNotFoundError):
            raise_random_error("position")

        with pytest.raises(InsufficientBalanceError):
            raise_random_error("balance")

        with pytest.raises(OrderExecutionError):
            raise_random_error("order")

    def test_catch_multiple_with_trading_error(self):
        """Test catching multiple trading errors with base class"""
        errors_caught = []

        for error_type in ["position", "balance", "order"]:
            try:
                if error_type == "position":
                    raise PositionNotFoundError("Position not found")
                elif error_type == "balance":
                    raise InsufficientBalanceError("Insufficient balance")
                elif error_type == "order":
                    raise OrderExecutionError("Order failed")
            except TradingError as e:
                errors_caught.append(type(e).__name__)

        assert len(errors_caught) == 3
        assert "PositionNotFoundError" in errors_caught
        assert "InsufficientBalanceError" in errors_caught
        assert "OrderExecutionError" in errors_caught
