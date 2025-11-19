"""
Alpha AI Autotrader - OpenRouter AI Client
Multi-AI consensus using cost-effective thinking models and latest frontier models
"""
from typing import Dict, List, Optional, Literal
from openai import OpenAI
from loguru import logger
import os
import time
import re


class OpenRouterClient:
    """
    OpenRouter API client for accessing multiple AI models

    Supported models:
    - Gemini 3 Pro Preview: FREE (frontier model, 1M context)
    - GPT-5.1: Latest OpenAI flagship model
    - DeepSeek V3: Latest DeepSeek model
    - Grok Code Fast 1: xAI's fast coding model
    - Kimi K2 Thinking: Advanced thinking model
    - Sherlock Think Alpha: Specialized reasoning model
    - MiniMax M2: Cost-effective alternative
    - Plus legacy models (DeepSeek R1, Gemini 2.0, Claude, etc.)
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Model configurations
    MODELS = {
        # === FRONTIER MODELS (Latest & Most Powerful) ===
        "gemini-3-pro": {
            "id": "google/gemini-3-pro-preview",
            "name": "Gemini 3.0 Pro Preview",
            "cost_per_1m": 0.0,  # FREE
            "thinking": True,
            "speed": "fast",
            "context_length": 1000000,  # 1M tokens
            "category": "frontier"
        },
        "gpt-5.1": {
            "id": "openai/gpt-5.1",
            "name": "GPT-5.1",
            "cost_per_1m": 15.0,  # Premium pricing
            "thinking": True,
            "speed": "medium",
            "context_length": 128000,
            "category": "frontier"
        },

        # === THINKING MODELS (Specialized for reasoning) ===
        "deepseek-v3": {
            "id": "deepseek/deepseek-chat",
            "name": "DeepSeek V3",
            "cost_per_1m": 0.27,
            "thinking": True,
            "speed": "fast",
            "category": "thinking"
        },
        "deepseek-r1": {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1",
            "cost_per_1m": 0.14,
            "thinking": True,
            "speed": "fast",
            "category": "thinking"
        },
        "gemini-flash": {
            "id": "google/gemini-2.0-flash-exp:free",
            "name": "Gemini 2.0 Flash",
            "cost_per_1m": 0.0,  # FREE
            "thinking": False,
            "speed": "very_fast",
            "category": "thinking"
        },

        # === CODING MODELS (Optimized for code) ===
        "grok-beta": {
            "id": "x-ai/grok-beta",
            "name": "Grok Beta",
            "cost_per_1m": 5.0,
            "thinking": False,
            "speed": "fast",
            "category": "coding"
        },
        "qwen-coder": {
            "id": "qwen/qwen-2.5-coder-32b-instruct",
            "name": "Qwen 2.5 Coder 32B",
            "cost_per_1m": 0.18,
            "thinking": False,
            "speed": "fast",
            "category": "coding"
        },

        # === GENERAL PURPOSE (Balanced) ===
        "minimax-m2": {
            "id": "minimax/minimax-m2",
            "name": "MiniMax M2",
            "cost_per_1m": 1.04,
            "thinking": False,
            "speed": "fast",
            "category": "general"
        },
        "claude-sonnet": {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet",
            "cost_per_1m": 3.0,
            "thinking": True,
            "speed": "medium",
            "category": "general"
        },
        "gpt-4o-mini": {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "cost_per_1m": 0.15,
            "thinking": False,
            "speed": "very_fast",
            "category": "general"
        }
    }
    
    def __init__(self, api_key: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Args:
            api_key: OpenRouter API key
            max_retries: Maximum number of retries for failed requests
            retry_delay: Base delay between retries (exponential backoff)
        """
        self.api_key = api_key
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=api_key,
            timeout=60.0
        )

        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Stats
        self.total_requests = 0
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
        self.failed_requests = 0
        self.retried_requests = 0
    
    @staticmethod
    def extract_json_from_markdown(text: str) -> str:
        """
        Extract JSON from markdown code block

        Args:
            text: Text that may contain ```json ... ``` wrapper

        Returns:
            Clean JSON string
        """
        # Try to find JSON in markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Try to find plain JSON object
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        return text

    def get_models_by_category(self, category: str) -> List[str]:
        """
        Get all models in a specific category

        Args:
            category: Category name (frontier, thinking, coding, general)

        Returns:
            List of model keys
        """
        return [
            key for key, config in self.MODELS.items()
            if config.get("category") == category
        ]

    def get_free_models(self) -> List[str]:
        """Get all free models"""
        return [
            key for key, config in self.MODELS.items()
            if config.get("cost_per_1m", 0) == 0.0
        ]

    def get_best_value_models(self, max_cost_per_1m: float = 1.0) -> List[str]:
        """
        Get models under a certain cost threshold

        Args:
            max_cost_per_1m: Maximum cost per 1M tokens

        Returns:
            List of model keys sorted by cost (cheapest first)
        """
        filtered = [
            (key, config) for key, config in self.MODELS.items()
            if config.get("cost_per_1m", 0) <= max_cost_per_1m
        ]
        # Sort by cost
        filtered.sort(key=lambda x: x[1].get("cost_per_1m", 0))
        return [key for key, _ in filtered]

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-3-pro",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        retry: bool = True
    ) -> Dict:
        """
        Send chat completion request with retry logic

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model: Model key (see MODELS dict)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            retry: Enable retry on failure

        Returns:
            {
                "content": "AI response",
                "model": "model_name",
                "model_id": "provider/model-id",
                "tokens_used": 1234,
                "cost": 0.00017,
                "retries": 0
            }
        """
        model_config = self.MODELS.get(model)

        if not model_config:
            logger.warning(f"Unknown model '{model}', falling back to gemini-3-pro")
            model_config = self.MODELS["gemini-3-pro"]

        model_id = model_config["id"]
        retries = 0
        last_error = None

        for attempt in range(self.max_retries if retry else 1):
            try:
                response = self.client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Extract response
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens

                # Calculate cost
                cost = (tokens_used / 1_000_000) * model_config["cost_per_1m"]

                # Update stats
                self.total_requests += 1
                self.total_tokens_used += tokens_used
                self.estimated_cost += cost

                if retries > 0:
                    self.retried_requests += 1

                logger.info(
                    f"✅ AI request #{self.total_requests}: {model_config['name']} "
                    f"({tokens_used} tokens, ${cost:.6f})"
                    + (f" [retried {retries}x]" if retries > 0 else "")
                )

                return {
                    "content": content,
                    "model": model_config["name"],
                    "model_id": model_id,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    "retries": retries,
                    "category": model_config.get("category", "unknown")
                }

            except Exception as e:
                last_error = e
                retries += 1

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"⚠️  AI request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"❌ AI request failed after {self.max_retries} attempts: {e}")
                    self.failed_requests += 1

        # All retries failed
        raise Exception(f"OpenRouter API error after {self.max_retries} retries: {last_error}")
    
    def analyze_trading_signal(
        self,
        coin_data: Dict,
        patterns: List[Dict],
        market_context: Dict,
        model: str = "deepseek-r1"
    ) -> Dict:
        """
        Ask AI to analyze a trading signal
        
        Args:
            coin_data: LunarCrush coin data
            patterns: Detected patterns
            market_context: Additional market context
            model: AI model to use
        
        Returns:
            {
                "decision": "LONG" | "SHORT" | "WAIT",
                "confidence": 8.5,
                "reasoning": "...",
                "entry_price": 60000,
                "stop_loss": 59200,
                "take_profit": 62500,
                "position_size": 0.01,
                "leverage": 3
            }
        """
        symbol = coin_data.get("symbol", "UNKNOWN")
        
        # Build prompt
        prompt = f"""Analyze this cryptocurrency trading signal:

**Coin**: {symbol}
**Price**: ${coin_data.get('price', 0):.6f}
**24h Change**: {coin_data.get('percent_change_24h', 0):.2f}%

**Social Metrics**:
- AltRank: {coin_data.get('alt_rank', 'N/A')} (prev: {coin_data.get('alt_rank_previous', 'N/A')})
- Galaxy Score: {coin_data.get('galaxy_score', 'N/A')}/100
- Sentiment: {coin_data.get('sentiment', 'N/A')}/100
- Social Volume 24h: {coin_data.get('social_volume_24h', 'N/A')}
- Social Dominance: {coin_data.get('social_dominance', 0):.2f}%

**Detected Patterns** ({len(patterns)} total):
"""
        
        for i, pattern in enumerate(patterns, 1):
            prompt += f"\n{i}. {pattern['pattern_name']} - Confidence: {pattern['confidence']:.1f}/10"
            prompt += f"\n   Reason: {pattern['reason']}"
        
        prompt += f"""

**Market Context**:
- Volume 24h: ${coin_data.get('volume_24h', 0):,.0f}
- Market Cap: ${coin_data.get('market_cap', 0):,.0f}
- Volatility: {coin_data.get('volatility', 0):.2%}

**Your Task**:
Analyze this signal and provide a trading recommendation. Consider:
1. Pattern strength and confluence
2. Social sentiment vs price action
3. Risk/reward ratio
4. Market conditions

Respond in JSON format:
{{
  "decision": "LONG" | "SHORT" | "WAIT",
  "confidence": 0-10,
  "reasoning": "detailed explanation",
  "entry_price": number,
  "stop_loss": number,
  "take_profit": number,
  "risk_reward_ratio": number,
  "recommended_leverage": 1-5,
  "position_size_percent": 1-10
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert cryptocurrency trading analyst. Analyze signals objectively and provide clear, actionable recommendations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.chat(messages, model=model, temperature=0.3)

        # Parse JSON response
        import json
        try:
            # Extract JSON from markdown if needed
            content = self.extract_json_from_markdown(response["content"])

            analysis = json.loads(content)
            analysis["ai_model"] = response["model"]
            analysis["tokens_used"] = response["tokens_used"]
            analysis["cost"] = response["cost"]
            return analysis
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response content: {response['content'][:500]}")
            return {
                "decision": "WAIT",
                "confidence": 5.0,
                "reasoning": response["content"],
                "ai_model": response["model"]
            }
    
    def get_consensus(
        self,
        coin_data: Dict,
        patterns: List[Dict],
        market_context: Dict,
        models: Optional[List[str]] = None,
        use_recommended: bool = True
    ) -> Dict:
        """
        Get consensus from multiple AI models

        Args:
            coin_data: Coin data
            patterns: Detected patterns
            market_context: Market context
            models: List of models to consult (if None, uses recommended)
            use_recommended: If True and models is None, use recommended trading models

        Returns:
            {
                "consensus_decision": "LONG" | "SHORT" | "WAIT",
                "consensus_confidence": 8.2,
                "votes": [{"model": "...", "decision": "...", "confidence": ...}],
                "reasoning": "Combined reasoning"
            }
        """
        # Use recommended models if not specified
        if models is None:
            if use_recommended:
                models = self.get_recommended_models(use_case="trading")
            else:
                models = ["gemini-3-pro", "deepseek-v3", "gemini-flash"]

        logger.info(f"🤖 Getting AI consensus from {len(models)} models: {', '.join(models)}")

        votes = []

        for model in models:
            try:
                analysis = self.analyze_trading_signal(
                    coin_data,
                    patterns,
                    market_context,
                    model=model
                )
                
                votes.append({
                    "model": analysis.get("ai_model", model),
                    "decision": analysis.get("decision", "WAIT"),
                    "confidence": analysis.get("confidence", 5.0),
                    "reasoning": analysis.get("reasoning", "")
                })
            
            except Exception as e:
                logger.error(f"Failed to get vote from {model}: {e}")
                continue
        
        if not votes:
            return {
                "consensus_decision": "WAIT",
                "consensus_confidence": 0.0,
                "votes": [],
                "reasoning": "No AI models responded"
            }
        
        # Calculate consensus
        decisions = [v["decision"] for v in votes]
        confidences = [v["confidence"] for v in votes]
        
        # Most common decision
        from collections import Counter
        decision_counts = Counter(decisions)
        consensus_decision = decision_counts.most_common(1)[0][0]
        
        # Average confidence
        consensus_confidence = sum(confidences) / len(confidences)
        
        # Combined reasoning
        reasoning = "\n\n".join([
            f"**{v['model']}** ({v['decision']}, {v['confidence']}/10):\n{v['reasoning']}"
            for v in votes
        ])
        
        return {
            "consensus_decision": consensus_decision,
            "consensus_confidence": consensus_confidence,
            "votes": votes,
            "reasoning": reasoning,
            "agreement_rate": decision_counts[consensus_decision] / len(votes)
        }
    
    def get_recommended_models(
        self,
        use_case: Literal["trading", "coding", "thinking", "budget"] = "trading"
    ) -> List[str]:
        """
        Get recommended models for a specific use case

        Args:
            use_case: Use case type

        Returns:
            List of recommended model keys
        """
        if use_case == "trading":
            # For trading: prioritize thinking models + free options
            return ["gemini-3-pro", "deepseek-v3", "gemini-flash"]

        elif use_case == "coding":
            return ["qwen-coder", "gemini-3-pro", "deepseek-v3"]

        elif use_case == "thinking":
            return ["deepseek-v3", "gemini-3-pro", "deepseek-r1"]

        elif use_case == "budget":
            # Free or very cheap models
            return self.get_best_value_models(max_cost_per_1m=0.5)

        else:
            return ["gemini-3-pro", "deepseek-v3"]

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": round(self.estimated_cost, 6),
            "failed_requests": self.failed_requests,
            "retried_requests": self.retried_requests,
            "success_rate": (
                (self.total_requests - self.failed_requests) / self.total_requests * 100
                if self.total_requests > 0 else 100.0
            ),
            "avg_tokens_per_request": (
                self.total_tokens_used / self.total_requests
                if self.total_requests > 0 else 0
            ),
            "available_models": len(self.MODELS),
            "free_models": len(self.get_free_models())
        }
