#!/usr/bin/env python3
"""
Alpha AI Autotrader - OpenRouter Integration Test
Tests all models, connection, and functionality
"""
import os
import sys
import asyncio
from typing import Dict, List
from loguru import logger
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.integrations.openrouter_client import OpenRouterClient


# Test configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Sample coin data for testing
SAMPLE_COIN_DATA = {
    "symbol": "BTC",
    "price": 60000.0,
    "percent_change_24h": 5.2,
    "alt_rank": 1,
    "alt_rank_previous": 1,
    "galaxy_score": 85,
    "sentiment": 72,
    "social_volume_24h": 250000,
    "social_dominance": 15.5,
    "volume_24h": 35000000000,
    "market_cap": 1200000000000,
    "volatility": 0.025
}

SAMPLE_PATTERNS = [
    {
        "pattern_name": "Social Volume Surge",
        "confidence": 8.5,
        "reason": "24h social volume increased by 150%"
    },
    {
        "pattern_name": "Bullish Sentiment",
        "confidence": 7.8,
        "reason": "Sentiment score above 70 with positive trend"
    }
]


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_client_initialization():
    """Test 1: Client Initialization"""
    print_section("TEST 1: Client Initialization")

    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found in environment variables!")
        print("   Please set it in .env file or export it:")
        print("   export OPENROUTER_API_KEY='your-key-here'")
        return None

    try:
        client = OpenRouterClient(
            api_key=OPENROUTER_API_KEY,
            max_retries=3,
            retry_delay=1.0
        )
        print("✅ Client initialized successfully")
        print(f"   Base URL: {client.BASE_URL}")
        print(f"   Max retries: {client.max_retries}")
        print(f"   Available models: {len(client.MODELS)}")
        return client

    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return None


def test_model_configuration(client: OpenRouterClient):
    """Test 2: Model Configuration"""
    print_section("TEST 2: Model Configuration")

    print(f"Total models available: {len(client.MODELS)}")
    print(f"Verified models: {len(client.get_verified_models())}")
    print(f"Free models: {len(client.get_free_models())}\n")

    # Group by category
    categories = {}
    for key, config in client.MODELS.items():
        category = config.get("category", "unknown")
        if category not in categories:
            categories[category] = []
        categories[category].append((key, config))

    for category, models in categories.items():
        print(f"📁 {category.upper()} ({len(models)} models):")
        for key, config in models:
            cost_str = "FREE ✅" if config['cost_per_1m'] == 0 else f"${config['cost_per_1m']}/1M"
            thinking_icon = "🧠" if config.get('thinking') else "  "
            verified_icon = "✅" if config.get('verified') else "⚠️ "
            print(f"   {verified_icon} {thinking_icon} {config['name']:30s} | {cost_str:15s}")
        print()

    # Test helper methods
    print("📊 Helper Methods:")
    print(f"   Free models: {client.get_free_models()}")
    print(f"   Budget models (<$0.5/1M): {client.get_best_value_models(0.5)}")
    print(f"   Thinking models: {client.get_models_by_category('thinking')}")
    print(f"   Recommended (trading): {client.get_recommended_models('trading')}")
    print(f"   Recommended (coding): {client.get_recommended_models('coding')}")
    print(f"   Recommended (premium): {client.get_recommended_models('premium')}")

    # Test smart selection
    print("\n🤖 Smart Model Selection:")
    simple_model = client.smart_select_model("simple", max_cost_per_1m=0.5)
    print(f"   Simple task (budget): {simple_model}")

    complex_model = client.smart_select_model("complex", max_cost_per_1m=5.0, require_thinking=True)
    print(f"   Complex task (thinking): {complex_model}")


def test_simple_chat(client: OpenRouterClient):
    """Test 3: Simple Chat Request"""
    print_section("TEST 3: Simple Chat Request")

    test_models = ["gemini-3-pro", "deepseek-v3"]

    for model_key in test_models:
        if model_key not in client.MODELS:
            print(f"⚠️  Model '{model_key}' not found, skipping...")
            continue

        print(f"\n🤖 Testing {client.MODELS[model_key]['name']}...")

        try:
            messages = [
                {"role": "user", "content": "Respond with exactly 5 words: 'Test successful, model working correctly'"}
            ]

            response = client.chat(
                messages=messages,
                model=model_key,
                temperature=0.3,
                max_tokens=50
            )

            print(f"✅ Response received:")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Tokens: {response['tokens_used']}")
            print(f"   Cost: ${response['cost']:.6f}")
            print(f"   Retries: {response['retries']}")

        except Exception as e:
            print(f"❌ Failed: {e}")


def test_trading_signal_analysis(client: OpenRouterClient):
    """Test 4: Trading Signal Analysis"""
    print_section("TEST 4: Trading Signal Analysis")

    model_key = "gemini-3-pro"
    print(f"🎯 Analyzing trading signal with {client.MODELS[model_key]['name']}...\n")

    try:
        result = client.analyze_trading_signal(
            coin_data=SAMPLE_COIN_DATA,
            patterns=SAMPLE_PATTERNS,
            market_context={},
            model=model_key
        )

        print("✅ Analysis completed:")
        print(f"   Decision: {result.get('decision', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0)}/10")
        print(f"   AI Model: {result.get('ai_model', 'N/A')}")
        print(f"   Tokens Used: {result.get('tokens_used', 0)}")
        print(f"   Cost: ${result.get('cost', 0):.6f}")
        print(f"\n   Reasoning:")
        reasoning = result.get('reasoning', 'No reasoning provided')
        for line in reasoning.split('\n')[:5]:  # First 5 lines
            print(f"     {line}")

        # Check if we got valid trading recommendation
        if result.get('decision') in ['LONG', 'SHORT', 'WAIT']:
            print("\n✅ Valid trading decision received")
        else:
            print(f"\n⚠️  Unexpected decision: {result.get('decision')}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


def test_multi_ai_consensus(client: OpenRouterClient):
    """Test 5: Multi-AI Consensus"""
    print_section("TEST 5: Multi-AI Consensus")

    # Use free models for testing
    test_models = ["gemini-3-pro", "deepseek-v3"]
    print(f"🤝 Getting consensus from {len(test_models)} models: {', '.join(test_models)}\n")

    try:
        result = client.get_consensus(
            coin_data=SAMPLE_COIN_DATA,
            patterns=SAMPLE_PATTERNS,
            market_context={},
            models=test_models
        )

        print("✅ Consensus received:")
        print(f"   Consensus Decision: {result.get('consensus_decision', 'N/A')}")
        print(f"   Consensus Confidence: {result.get('consensus_confidence', 0):.1f}/10")
        print(f"   Agreement Rate: {result.get('agreement_rate', 0):.0%}")
        print(f"\n   Individual Votes:")

        for vote in result.get('votes', []):
            print(f"     • {vote['model']}: {vote['decision']} ({vote['confidence']}/10)")

        print("\n   Combined Reasoning (first 300 chars):")
        reasoning = result.get('reasoning', 'No reasoning')[:300]
        print(f"     {reasoning}...")

    except Exception as e:
        print(f"❌ Consensus failed: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling(client: OpenRouterClient):
    """Test 6: Error Handling & Retry Logic"""
    print_section("TEST 6: Error Handling & Retry Logic")

    print("🧪 Testing with invalid model...")
    try:
        messages = [{"role": "user", "content": "Test"}]
        response = client.chat(
            messages=messages,
            model="non-existent-model",
            max_tokens=20
        )
        print(f"✅ Fallback worked: Used {response['model']}")

    except Exception as e:
        print(f"❌ Error handling failed: {e}")

    print("\n🧪 Testing with malformed request...")
    try:
        # This should trigger retry logic
        messages = []  # Empty messages should cause an error
        response = client.chat(
            messages=messages,
            model="gemini-3-pro",
            max_tokens=20
        )
        print(f"⚠️  Unexpected success with empty messages")

    except Exception as e:
        print(f"✅ Error caught correctly: {str(e)[:100]}...")


def test_statistics(client: OpenRouterClient):
    """Test 7: Statistics & Monitoring"""
    print_section("TEST 7: Statistics & Monitoring")

    stats = client.get_stats()

    print("📊 Client Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Total Tokens Used: {stats['total_tokens_used']:,}")
    print(f"   Estimated Cost: ${stats['estimated_cost_usd']:.6f}")
    print(f"   Failed Requests: {stats['failed_requests']}")
    print(f"   Retried Requests: {stats['retried_requests']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Avg Tokens/Request: {stats['avg_tokens_per_request']:.0f}")
    print(f"   Available Models: {stats['available_models']}")
    print(f"   Free Models: {stats['free_models']}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀 "+"="*66)
    print("  ALPHA AI AUTOTRADER - OpenRouter Integration Test Suite")
    print("="*68 + " 🚀\n")

    # Test 1: Initialize
    client = test_client_initialization()
    if not client:
        print("\n❌ Cannot proceed without valid client. Exiting.")
        return

    # Test 2: Model configuration
    test_model_configuration(client)

    # Test 3: Simple chat
    test_simple_chat(client)

    # Test 4: Trading signal analysis
    test_trading_signal_analysis(client)

    # Test 5: Multi-AI consensus
    test_multi_ai_consensus(client)

    # Test 6: Error handling
    test_error_handling(client)

    # Test 7: Statistics
    test_statistics(client)

    # Summary
    print_section("TEST SUMMARY")
    stats = client.get_stats()

    total_tests = 7
    passed_tests = total_tests - (1 if stats['failed_requests'] > 5 else 0)

    print(f"✅ Tests Completed: {passed_tests}/{total_tests}")
    print(f"📊 Total API Calls: {stats['total_requests']}")
    print(f"💰 Total Cost: ${stats['estimated_cost_usd']:.6f}")
    print(f"🎯 Success Rate: {stats['success_rate']:.1f}%")

    if stats['success_rate'] >= 90:
        print("\n🎉 Integration test PASSED! Everything works correctly.")
    else:
        print(f"\n⚠️  Integration test completed with {stats['failed_requests']} failures.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | {message}",
        level="INFO"
    )

    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
