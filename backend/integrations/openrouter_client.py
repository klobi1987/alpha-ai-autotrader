"""
Alpha AI Autotrader - OpenRouter AI Client
Multi-AI consensus using cost-effective thinking models
"""
from typing import Dict, List, Optional, Literal
from openai import OpenAI
from loguru import logger
import os


class OpenRouterClient:
    """
    OpenRouter API client for accessing multiple AI models
    
    Supported models (cost-effective thinking models):
    - DeepSeek R1: $0.14/1M tokens (best value thinking model)
    - Gemini 2.0 Flash Thinking: FREE
    - Qwen 2.5 Coder 32B: $0.18/1M tokens
    - Claude 3.5 Sonnet: Premium (for critical decisions)
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Model configurations
    MODELS = {
        "deepseek-r1": {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1",
            "cost_per_1m": 0.14,
            "thinking": True,
            "speed": "fast"
        },
        "gemini-flash-thinking": {
            "id": "google/gemini-2.0-flash-thinking-exp",
            "name": "Gemini 2.0 Flash Thinking",
            "cost_per_1m": 0.0,  # FREE
            "thinking": True,
            "speed": "very_fast"
        },
        "qwen-coder": {
            "id": "qwen/qwen-2.5-coder-32b-instruct",
            "name": "Qwen 2.5 Coder 32B",
            "cost_per_1m": 0.18,
            "thinking": False,
            "speed": "fast"
        },
        "claude-sonnet": {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet",
            "cost_per_1m": 3.0,
            "thinking": True,
            "speed": "medium"
        },
        "gpt-4o-mini": {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "cost_per_1m": 0.15,
            "thinking": False,
            "speed": "very_fast"
        }
    }
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=api_key
        )
        
        # Stats
        self.total_requests = 0
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-r1",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model: Model key (see MODELS dict)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        
        Returns:
            {
                "content": "AI response",
                "model": "model_name",
                "tokens_used": 1234,
                "cost": 0.00017
            }
        """
        model_config = self.MODELS.get(model, self.MODELS["deepseek-r1"])
        model_id = model_config["id"]
        
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
            
            logger.info(
                f"AI request #{self.total_requests}: {model_config['name']} "
                f"({tokens_used} tokens, ${cost:.6f})"
            )
            
            return {
                "content": content,
                "model": model_config["name"],
                "tokens_used": tokens_used,
                "cost": cost
            }
        
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
    
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
            analysis = json.loads(response["content"])
            analysis["ai_model"] = response["model"]
            analysis["tokens_used"] = response["tokens_used"]
            analysis["cost"] = response["cost"]
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning(f"Failed to parse AI response as JSON: {response['content'][:200]}")
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
        models: List[str] = ["deepseek-r1", "gemini-flash-thinking"]
    ) -> Dict:
        """
        Get consensus from multiple AI models
        
        Args:
            coin_data: Coin data
            patterns: Detected patterns
            market_context: Market context
            models: List of models to consult
        
        Returns:
            {
                "consensus_decision": "LONG" | "SHORT" | "WAIT",
                "consensus_confidence": 8.2,
                "votes": [{"model": "...", "decision": "...", "confidence": ...}],
                "reasoning": "Combined reasoning"
            }
        """
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
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": self.estimated_cost,
            "avg_tokens_per_request": (
                self.total_tokens_used / self.total_requests
                if self.total_requests > 0 else 0
            )
        }
