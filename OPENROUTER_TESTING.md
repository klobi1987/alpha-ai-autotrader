# OpenRouter Integration - Testing Guide

## 🎯 Overview

Alpha AI Autotrader sada podržava **13 naprednih AI modela** preko OpenRouter platforme, uključujući:

### 🚀 Frontier Models (Najnoviji i najmoćniji)
- **Gemini 3.0 Pro Preview** - FREE, 1M tokens context
- **GPT-5.1** - Latest OpenAI flagship model

### 🧠 Thinking Models (Specijalizirani za reasoning)
- **Sherlock Think Alpha** - FREE
- **Kimi K2 Thinking** - Advanced reasoning
- **DeepSeek V3** - Latest version
- **DeepSeek R1** - Original thinking model
- **Gemini 2.0 Flash Thinking** - FREE

### 💻 Coding Models
- **Grok Code Fast 1** - xAI's ultra-fast model
- **Qwen 2.5 Coder 32B** - Specialized for code

### 🎯 General Purpose
- **MiniMax M2** - Balanced performance
- **Claude 3.5 Sonnet** - Premium quality
- **GPT-4o Mini** - Fast and cheap

---

## 📋 Setup

### 1. Get OpenRouter API Key

1. Idi na: https://openrouter.ai/
2. Sign up / Log in
3. Go to Keys: https://openrouter.ai/keys
4. Create new key
5. Copy API key

### 2. Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your API key
nano .env
```

Add:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
PRIMARY_AI_MODEL=gemini-3-pro
SECONDARY_AI_MODEL=sherlock-think
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## 🧪 Running Tests

### Quick Test (checks configuration only)

```bash
python3 test_openrouter_integration.py
```

### Full Integration Test

Requires valid OPENROUTER_API_KEY in .env:

```bash
# Set API key first
export OPENROUTER_API_KEY="your-key-here"

# Run tests
python3 test_openrouter_integration.py
```

### Test Output Example

```
🚀 ======================================================================
  ALPHA AI AUTOTRADER - OpenRouter Integration Test Suite
======================================================================== 🚀

======================================================================
  TEST 1: Client Initialization
======================================================================

✅ Client initialized successfully
   Base URL: https://openrouter.ai/api/v1
   Max retries: 3
   Available models: 13

======================================================================
  TEST 2: Model Configuration
======================================================================

Total models available: 13

📁 FRONTIER (2 models):
   🧠 Gemini 3.0 Pro Preview          | FREE            | google/gemini-3-pro-preview
   🧠 GPT-5.1                          | $15.0/1M        | openai/gpt-5.1

📁 THINKING (5 models):
   🧠 Sherlock Think Alpha             | FREE            | stealth/sherlock-think-alpha
   🧠 Kimi K2 Thinking                 | $2.5/1M         | parasail/kimi-k2-thinking
   🧠 DeepSeek V3 0324                 | $0.60/1M        | chutes/deepseek-v3-0324
   ...

✅ Tests Completed: 7/7
💰 Total Cost: $0.000123
🎯 Success Rate: 100.0%

🎉 Integration test PASSED! Everything works correctly.
```

---

## 🔧 Usage Examples

### 1. Simple Chat

```python
from backend.integrations.openrouter_client import OpenRouterClient

client = OpenRouterClient(api_key="your-key")

messages = [
    {"role": "user", "content": "Analyze Bitcoin's current market trend"}
]

response = client.chat(
    messages=messages,
    model="gemini-3-pro",  # FREE model
    temperature=0.7,
    max_tokens=1000
)

print(f"Response: {response['content']}")
print(f"Cost: ${response['cost']:.6f}")
```

### 2. Trading Signal Analysis

```python
coin_data = {
    "symbol": "BTC",
    "price": 60000.0,
    "percent_change_24h": 5.2,
    "social_volume_24h": 250000,
    # ... more data
}

patterns = [
    {"pattern_name": "Volume Surge", "confidence": 8.5, "reason": "..."}
]

analysis = client.analyze_trading_signal(
    coin_data=coin_data,
    patterns=patterns,
    market_context={},
    model="gemini-3-pro"
)

print(f"Decision: {analysis['decision']}")
print(f"Confidence: {analysis['confidence']}/10")
```

### 3. Multi-AI Consensus

```python
# Get consensus from multiple free models
consensus = client.get_consensus(
    coin_data=coin_data,
    patterns=patterns,
    market_context={},
    models=["gemini-3-pro", "sherlock-think", "deepseek-v3"]
)

print(f"Consensus: {consensus['consensus_decision']}")
print(f"Agreement: {consensus['agreement_rate']:.0%}")
print(f"Confidence: {consensus['consensus_confidence']:.1f}/10")
```

### 4. Using Helper Methods

```python
# Get all free models
free_models = client.get_free_models()
print(f"Free models: {free_models}")

# Get models by category
thinking_models = client.get_models_by_category("thinking")
print(f"Thinking models: {thinking_models}")

# Get recommended models for trading
recommended = client.get_recommended_models("trading")
print(f"Recommended: {recommended}")

# Get budget models (<$1/1M tokens)
budget_models = client.get_best_value_models(max_cost_per_1m=1.0)
print(f"Budget models: {budget_models}")
```

---

## 📊 Features

### ✅ Retry Logic with Exponential Backoff
- Automatically retries failed requests
- Configurable max_retries (default: 3)
- Exponential backoff: 1s, 2s, 4s, 8s...

### ✅ Cost Tracking
- Tracks tokens used per request
- Calculates estimated costs
- Reports total spending

### ✅ Error Handling
- Graceful fallbacks to default models
- Detailed error logging
- Success rate tracking

### ✅ Model Categories
- Filter by category (frontier, thinking, coding, general)
- Get free models only
- Get budget-friendly models

### ✅ Statistics
- Total requests
- Total tokens used
- Failed/retried requests
- Success rate
- Average tokens per request

---

## 🎯 Recommended Model Combinations

### Budget Trading (FREE)
```python
models = ["gemini-3-pro", "sherlock-think", "gemini-flash-thinking"]
# Cost: $0 per consensus
```

### Balanced Trading
```python
models = ["gemini-3-pro", "deepseek-v3", "kimi-k2"]
# Cost: ~$0.003 per consensus (3 models × 1000 tokens × cost)
```

### Premium Trading
```python
models = ["gpt-5.1", "claude-sonnet", "kimi-k2"]
# Cost: ~$0.020 per consensus (higher quality)
```

### Coding Assistant
```python
models = ["grok-code-fast", "qwen-coder", "gemini-3-pro"]
# Cost: ~$0.0002 per request (very cheap)
```

---

## 🐛 Troubleshooting

### Error: "OPENROUTER_API_KEY not found"

**Solution:**
```bash
# Make sure .env file exists
cp .env.example .env

# Add your key
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" >> .env

# Or export it
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

### Error: "Model not found"

**Solution:**
Check available models:
```python
client = OpenRouterClient(api_key="...")
print(client.MODELS.keys())
```

Use correct model key (not the full ID):
- ✅ `model="gemini-3-pro"`
- ❌ `model="google/gemini-3-pro-preview"`

### Error: "Rate limit exceeded"

**Solution:**
- Use free models: `client.get_free_models()`
- Increase retry delay: `OpenRouterClient(api_key="...", retry_delay=2.0)`
- Reduce concurrent requests

### High Costs

**Solution:**
- Use free models: `gemini-3-pro`, `sherlock-think`, `gemini-flash-thinking`
- Reduce `max_tokens` in requests
- Use `get_best_value_models(max_cost_per_1m=0.5)` for cheap options

---

## 📈 Next Steps

1. ✅ Test integration with `python3 test_openrouter_integration.py`
2. ✅ Configure preferred models in `.env`
3. ✅ Enable multi-AI consensus: `ENABLE_MULTI_AI_CONSENSUS=true`
4. 🚀 Start trading system: `python3 backend/main.py`
5. 📊 Monitor costs in dashboard

---

## 💡 Pro Tips

1. **Start with free models** - Gemini 3 Pro and Sherlock Think are excellent and FREE
2. **Use consensus for important decisions** - 3 models is a good balance
3. **Monitor costs** - Check `client.get_stats()` regularly
4. **Adjust temperature** - Lower (0.3) for trading, higher (0.7) for creative tasks
5. **Set max_tokens wisely** - Trading analysis needs 1000-2000 tokens

---

## 📚 Resources

- OpenRouter Dashboard: https://openrouter.ai/
- OpenRouter Docs: https://openrouter.ai/docs
- Model Pricing: https://openrouter.ai/models
- API Keys: https://openrouter.ai/keys

---

**Questions?** Check logs in `logs/alpha_autotrader.log` or run tests with `DEBUG=true`
