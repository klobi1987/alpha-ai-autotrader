#!/usr/bin/env python3
"""
Check which OpenRouter models are actually available and working
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Models to test (based on OpenRouter's actual catalog)
MODELS_TO_TEST = [
    # Google models
    "google/gemini-3-pro-preview",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",

    # DeepSeek models
    "deepseek/deepseek-chat",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-coder",

    # OpenAI models
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/o1-mini",

    # Anthropic
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-opus",

    # xAI
    "x-ai/grok-beta",
    "x-ai/grok-2",

    # Qwen
    "qwen/qwen-2.5-coder-32b-instruct",
    "qwen/qvq-72b-preview",

    # Other
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large",
    "perplexity/llama-3.1-sonar-large-128k-online",
]

print("🔍 Testing OpenRouter Models...\n")

working_models = []
failed_models = []

for model_id in MODELS_TO_TEST:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )

        tokens = response.usage.total_tokens
        working_models.append(model_id)
        print(f"✅ {model_id:50s} | {tokens} tokens")

    except Exception as e:
        failed_models.append((model_id, str(e)))
        error_msg = str(e)[:80]
        print(f"❌ {model_id:50s} | {error_msg}")

print(f"\n{'='*80}")
print(f"✅ Working: {len(working_models)}")
print(f"❌ Failed:  {len(failed_models)}")
print(f"{'='*80}\n")

# Save results
results = {
    "working": working_models,
    "failed": [{"model": m, "error": e} for m, e in failed_models]
}

with open("openrouter_model_check.json", "w") as f:
    json.dump(results, f, indent=2)

print("📝 Results saved to openrouter_model_check.json")
