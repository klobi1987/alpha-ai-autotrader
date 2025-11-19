# Exception Handling Improvement Guide

## Overview

This guide explains how to replace generic `except Exception` handlers with specific exception types for better error handling and debugging.

**Status**: ✅ Critical API routes completed (routes.py partially done)
**Remaining**: 28 files with generic exception handlers

---

## Why Specific Exceptions Matter

### ❌ Bad Practice (Generic)
```python
try:
    result = exchange.place_order(symbol, amount)
except Exception as e:
    logger.error(f"Error: {e}")
    return None
```

**Problems**:
- Catches ALL exceptions (even KeyboardInterrupt, SystemExit)
- Difficult to debug (no context about error type)
- Can't retry only retryable errors
- Hides programming bugs
- Poor logging (no structured details)

### ✅ Good Practice (Specific)
```python
from backend.core.exceptions import (
    ExchangeConnectionError,
    OrderExecutionError,
    InsufficientBalanceError,
    get_exception_details
)

try:
    result = exchange.place_order(symbol, amount)
except ExchangeConnectionError as e:
    logger.warning(f"Connection error (retryable): {get_exception_details(e)}")
    # Retry logic here
    return None
except InsufficientBalanceError as e:
    logger.error(f"Insufficient balance: {get_exception_details(e)}")
    # Alert admin
    raise
except OrderExecutionError as e:
    logger.error(f"Order execution failed: {get_exception_details(e)}")
    # Don't retry, log and handle
    return None
except Exception as e:
    logger.critical(f"Unexpected error: {get_exception_details(e)}")
    # Something unexpected happened
    raise
```

**Benefits**:
- Know exactly what went wrong
- Can retry only retryable errors
- Better logging with structured details
- Alerts admins for critical issues
- Debugging is 10x easier

---

## Custom Exception Hierarchy

All custom exceptions are defined in `backend/core/exceptions.py`:

```
AlphaTraderException (base)
├── ConfigurationError
│   ├── APIKeyMissingError
│   └── InvalidSettingsError
├── TradingError
│   ├── InsufficientBalanceError
│   ├── PositionNotFoundError
│   ├── OrderExecutionError
│   ├── InvalidOrderError
│   ├── MarketClosedError
│   ├── LeverageTooHighError
│   └── RiskLimitExceededError
├── ExchangeError
│   ├── ExchangeConnectionError
│   ├── ExchangeAuthError
│   ├── ExchangeRateLimitError
│   ├── SymbolNotFoundError
│   └── ExchangeMaintenanceError
├── DataError
│   ├── DataFetchError
│   ├── InvalidDataError
│   ├── DataNotFoundError
│   └── CacheError
├── AIError
│   ├── ModelLoadError
│   ├── PredictionError
│   ├── FeatureExtractionError
│   ├── TrainingError
│   ├── AIProviderError
│   └── ConsensusError
├── IntegrationError
│   ├── LunarCrushError
│   ├── ClaudeAPIError
│   ├── OpenRouterError
│   └── WebResearchError
├── DatabaseError
│   ├── RecordNotFoundError
│   ├── DuplicateRecordError
│   └── DatabaseConnectionError
├── ValidationError
│   ├── InvalidSymbolError
│   ├── InvalidAmountError
│   ├── InvalidPriceError
│   └── InvalidTimeframeError
├── WebSocketError
│   ├── WebSocketConnectionError
│   └── WebSocketAuthError
└── PatternError
    ├── PatternNotFoundError
    ├── PatternValidationError
    └── ClusteringError
```

---

## Step-by-Step Refactoring

### Step 1: Import Custom Exceptions

At the top of your file:

```python
from backend.core.exceptions import (
    # Import specific exceptions you need
    ExchangeError,
    ExchangeConnectionError,
    DataFetchError,
    ConfigurationError,
    # Helper functions
    get_exception_details,
    is_retryable_error,
    should_alert_admin
)
```

### Step 2: Identify Exception Patterns

Find generic handlers in your code:

```bash
# Find all files with generic exception handlers
grep -r "except Exception" backend/ --include="*.py"

# Count occurrences
grep -r "except Exception" backend/ --include="*.py" | wc -l
```

### Step 3: Replace With Specific Exceptions

**Before:**
```python
def fetch_coin_data(symbol: str):
    try:
        response = requests.get(f"https://api.example.com/coin/{symbol}")
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None
```

**After:**
```python
def fetch_coin_data(symbol: str):
    try:
        response = requests.get(
            f"https://api.example.com/coin/{symbol}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.Timeout as e:
        logger.warning(f"Request timeout for {symbol}: {get_exception_details(e)}")
        raise DataFetchError(f"Timeout fetching {symbol}", details={"symbol": symbol})
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {symbol}: {get_exception_details(e)}")
        raise DataFetchError(f"Connection failed for {symbol}", details={"symbol": symbol})
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Symbol not found: {symbol}")
            raise InvalidSymbolError(f"Symbol {symbol} not found")
        logger.error(f"HTTP error for {symbol}: {get_exception_details(e)}")
        raise DataFetchError(f"HTTP error for {symbol}", details={"status_code": e.response.status_code})
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid JSON response for {symbol}: {get_exception_details(e)}")
        raise InvalidDataError(f"Invalid data for {symbol}")
    except Exception as e:
        # Unexpected errors only
        logger.critical(f"Unexpected error fetching {symbol}: {get_exception_details(e)}")
        raise
```

---

## Common Patterns by Module

### API Routes (`backend/api/*.py`)

```python
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from backend.core.exceptions import (
    ConfigurationError,
    PositionNotFoundError,
    TradingError,
    DatabaseError,
    get_exception_details
)

@app.get("/endpoint")
async def endpoint():
    try:
        # Your code here
        pass
    except PositionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConfigurationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error: {get_exception_details(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.critical(f"Unexpected error: {get_exception_details(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Exchange Clients (`backend/integrations/mexc_client.py`)

```python
from backend.core.exceptions import (
    ExchangeConnectionError,
    ExchangeAuthError,
    ExchangeRateLimitError,
    OrderExecutionError,
    SymbolNotFoundError,
    get_exception_details,
    is_retryable_error
)

def place_order(symbol: str, amount: float):
    try:
        result = self.client.create_order(...)
        return result
    except ccxt.NetworkError as e:
        logger.warning(f"Network error (retryable): {get_exception_details(e)}")
        raise ExchangeConnectionError(str(e))
    except ccxt.AuthenticationError as e:
        logger.error(f"Auth error: {get_exception_details(e)}")
        raise ExchangeAuthError(str(e))
    except ccxt.RateLimitExceeded as e:
        logger.warning(f"Rate limit (retryable): {get_exception_details(e)}")
        raise ExchangeRateLimitError(str(e))
    except ccxt.InvalidOrder as e:
        logger.error(f"Invalid order: {get_exception_details(e)}")
        raise OrderExecutionError(str(e))
    except ccxt.ExchangeError as e:
        logger.error(f"Exchange error: {get_exception_details(e)}")
        raise OrderExecutionError(str(e))
    except Exception as e:
        logger.critical(f"Unexpected error: {get_exception_details(e)}")
        raise
```

### ML Models (`backend/ml/*.py`)

```python
from backend.core.exceptions import (
    ModelLoadError,
    PredictionError,
    FeatureExtractionError,
    InvalidDataError,
    get_exception_details
)

def predict(features):
    try:
        if len(features) != self.expected_features:
            raise FeatureExtractionError(
                f"Expected {self.expected_features} features, got {len(features)}"
            )

        prediction = self.model.predict(features)
        return prediction
    except FeatureExtractionError:
        raise  # Re-raise our custom exception
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid features: {get_exception_details(e)}")
        raise InvalidDataError("Invalid feature data")
    except AttributeError as e:
        logger.error(f"Model not loaded: {get_exception_details(e)}")
        raise ModelLoadError("Model not initialized")
    except Exception as e:
        logger.critical(f"Prediction failed: {get_exception_details(e)}")
        raise PredictionError(str(e))
```

### AI Integrations (`backend/integrations/openrouter_client.py`)

```python
from backend.core.exceptions import (
    AIProviderError,
    OpenRouterError,
    ConsensusError,
    InvalidDataError,
    get_exception_details
)

def get_analysis(data):
    try:
        response = self.client.chat.completions.create(...)
        result = self.extract_json_from_markdown(response.content)
        return json.loads(result)
    except openai.APIConnectionError as e:
        logger.warning(f"API connection error: {get_exception_details(e)}")
        raise OpenRouterError("Connection to OpenRouter failed")
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit: {get_exception_details(e)}")
        raise OpenRouterError("OpenRouter rate limit exceeded")
    except openai.APIError as e:
        logger.error(f"OpenRouter API error: {get_exception_details(e)}")
        raise AIProviderError(str(e))
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid JSON response: {get_exception_details(e)}")
        raise InvalidDataError("AI returned invalid JSON")
    except Exception as e:
        logger.critical(f"Unexpected AI error: {get_exception_details(e)}")
        raise AIProviderError(str(e))
```

---

## Helper Functions

Use these helper functions from `exceptions.py`:

### `get_exception_details(exc)`
Extracts structured details from any exception for logging:

```python
try:
    # Your code
    pass
except SomeError as e:
    details = get_exception_details(e)
    # Returns: {"type": "SomeError", "message": "...", "details": {...}, "module": "..."}
    logger.error(f"Error occurred: {details}")
```

### `is_retryable_error(exc)`
Determines if an error should be retried:

```python
try:
    result = fetch_data()
except Exception as e:
    if is_retryable_error(e):
        # Retry with exponential backoff
        time.sleep(2 ** attempt)
        retry()
    else:
        # Don't retry, handle or raise
        raise
```

### `should_alert_admin(exc)`
Determines if admin should be alerted:

```python
try:
    execute_trade()
except Exception as e:
    if should_alert_admin(e):
        send_telegram_alert(f"CRITICAL: {e}")
    raise
```

---

## Files to Update (28 total)

### ✅ Completed:
1. `backend/api/routes.py` (partially - config, signals, positions, close_position, start_trading)

### 🔄 In Progress:
1. `backend/api/routes.py` (remaining endpoints: stop_trading, performance, chat, agents, market, system)

### 📋 TODO (Priority Order):

**HIGH Priority** (API & Integrations):
1. `backend/api/auth_routes.py`
2. `backend/api/advanced_ml_routes.py`
3. `backend/api/ml_patterns_routes.py`
4. `backend/api/settings_routes.py`
5. `backend/api/websocket.py`
6. `backend/api/chat_handler.py`
7. `backend/integrations/openrouter_client.py`
8. `backend/integrations/lunarcrush.py`
9. `backend/integrations/mexc_client.py`
10. `backend/integrations/claude_agent_client.py`

**MEDIUM Priority** (Core Logic):
11. `backend/core/trading_system.py`
12. `backend/core/master_brain_v2.py`
13. `backend/core/master_brain.py`
14. `backend/core/live_trade_manager.py`
15. `backend/core/settings_manager.py`
16. `backend/core/ml_engine.py`
17. `backend/core/memory_system.py`
18. `backend/core/web_research.py`

**LOW Priority** (ML & Agents):
19. `backend/ml/ensemble_methods.py`
20. `backend/ml/feature_selector.py`
21. `backend/ml/hyperparameter_tuner.py`
22. `backend/ml/lstm_network.py`
23. `backend/ml/online_learner.py`
24. `backend/ml/pattern_learner.py`
25. `backend/agents/base_agent.py`
26. `backend/ai/agents/ml_pattern_agent.py`
27. `backend/api/main.py`

---

## Automated Helper Script

Use this script to find and list all generic exception handlers:

```bash
#!/bin/bash
# find_generic_exceptions.sh

echo "=== Finding Generic Exception Handlers ==="
echo ""

for file in $(grep -r "except Exception" backend/ --include="*.py" -l); do
    count=$(grep "except Exception" "$file" | wc -l)
    echo "📁 $file: $count occurrences"
    grep -n "except Exception" "$file" | head -3
    echo ""
done

echo "Total files: $(grep -r "except Exception" backend/ --include="*.py" -l | wc -l)"
echo "Total occurrences: $(grep -r "except Exception" backend/ --include="*.py" | wc -l)"
```

Make it executable and run:
```bash
chmod +x find_generic_exceptions.sh
./find_generic_exceptions.sh
```

---

## Testing Exception Handling

After refactoring, test your exception handling:

```python
import pytest
from backend.core.exceptions import *

def test_specific_exceptions():
    """Test that specific exceptions are raised correctly"""

    with pytest.raises(PositionNotFoundError):
        raise PositionNotFoundError("Position not found", details={"symbol": "BTCUSDT"})

    with pytest.raises(ExchangeConnectionError):
        raise ExchangeConnectionError("Connection failed")

def test_exception_details():
    """Test get_exception_details helper"""
    try:
        raise PositionNotFoundError("Test", details={"test": "value"})
    except PositionNotFoundError as e:
        details = get_exception_details(e)
        assert details["type"] == "PositionNotFoundError"
        assert details["details"]["test"] == "value"

def test_retryable_errors():
    """Test is_retryable_error helper"""
    assert is_retryable_error(ExchangeConnectionError("test"))
    assert is_retryable_error(ExchangeRateLimitError("test"))
    assert not is_retryable_error(ExchangeAuthError("test"))
    assert not is_retryable_error(ConfigurationError("test"))
```

---

## Commit Message Template

When you complete a file:

```
fix: Improve exception handling in <module_name>

- Replace generic Exception handlers with specific exception types
- Add structured logging with get_exception_details()
- Implement retry logic for retryable errors
- Add admin alerts for critical errors

Affected file: backend/<path>/<file>.py
Exceptions replaced: <count>
```

---

## Progress Tracking

Update this section as you complete files:

```markdown
Progress: 1/28 files completed (3.6%)

✅ backend/api/routes.py (partial - 6/10 endpoints)
⬜ backend/api/auth_routes.py
⬜ backend/api/advanced_ml_routes.py
...
```

---

## Best Practices Summary

1. **Always use specific exceptions** - Never catch bare `Exception` unless truly unexpected
2. **Use get_exception_details()** - Structured logging with context
3. **Implement retry logic** - Use `is_retryable_error()` to determine retry strategy
4. **Alert on critical errors** - Use `should_alert_admin()` for notifications
5. **Rollback database on errors** - Use `db.rollback()` in SQLAlchemy exception handlers
6. **Re-raise custom exceptions** - Don't swallow custom exceptions
7. **Log at appropriate levels**:
   - `DEBUG`: Detailed diagnostic info
   - `INFO`: Confirmations that things are working
   - `WARNING`: Recoverable issues (retries, degraded functionality)
   - `ERROR`: Serious problems (failed operations, data issues)
   - `CRITICAL`: System-level failures (require immediate admin action)

---

## Questions or Issues?

If you encounter difficulties:
1. Check existing refactored code in `backend/api/routes.py` for examples
2. Review exception definitions in `backend/core/exceptions.py`
3. Test exception behavior with pytest
4. Refer to this guide for common patterns

Good luck! 🚀
