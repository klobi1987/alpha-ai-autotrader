"""
Alpha AI Autotrader - Candidate Ranker (NOT Filter!)
Ranks ALL coins by potential, Claude decides what to analyze
"""
from typing import List, Dict, Optional
from loguru import logger


class CandidateRanker:
    """
    Candidate Ranker - NO RIGID FILTERS!
    
    Philosophy:
    - Don't filter out degen gems (100x-1000x potential)
    - Rank ALL coins by multiple factors
    - Claude decides which ones to analyze deeply
    - Micro caps are OPPORTUNITIES, not risks!
    
    Ranking Factors:
    1. Social Surge (0 → 1000+ mentions = early pump signal)
    2. AltRank Jump (big moves = momentum)
    3. Early Stage Detection (low market cap = room to grow)
    4. Volume Spike (sudden interest)
    5. Sentiment Shift (bullish/bearish momentum)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Ranking configuration
        """
        self.config = config or self._default_config()
        self.stats = {
            "total_coins": 0,
            "degen_gems": 0,  # Micro caps (<$10M)
            "mid_caps": 0,  # $10M-$100M
            "large_caps": 0,  # >$100M
            "top_ranked": 0
        }
    
    def _default_config(self) -> Dict:
        """Default ranking configuration"""
        return {
            # Ranking weights
            "weight_social_surge": 0.30,  # 30% - Most important!
            "weight_altrank_jump": 0.25,  # 25% - Momentum
            "weight_early_stage": 0.20,  # 20% - Room to grow
            "weight_volume_spike": 0.15,  # 15% - Interest
            "weight_sentiment": 0.10,  # 10% - Direction
            
            # Thresholds for scoring (NOT filtering!)
            "social_surge_threshold": 500,  # +500% = strong surge
            "altrank_jump_threshold": 500,  # +500 = big move
            "micro_cap_threshold": 10_000_000,  # <$10M = micro
            "volume_spike_threshold": 3.0,  # 3x average = spike
            
            # Output
            "top_n": 20,  # Top 20 for Claude to review
            "include_all_surges": True  # Always include social surges
        }
    
    def rank_candidates(
        self,
        coins: List[Dict],
        mexc_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Rank ALL coins by potential
        
        NO FILTERING - just ranking!
        
        Args:
            coins: List of LunarCrush coin data (ALL 1000)
            mexc_data: Optional MEXC market data
        
        Returns:
            Top N ranked coins for Claude to analyze
        """
        self.stats["total_coins"] = len(coins)
        
        logger.info(f"📊 Ranking {len(coins)} coins (NO FILTERS!)...")
        
        # Calculate scores for ALL coins
        scored_coins = []
        
        for coin in coins:
            score_data = self._calculate_score(coin)
            
            # Add score to coin
            coin["rank_score"] = score_data["total_score"]
            coin["score_breakdown"] = score_data["breakdown"]
            coin["rank_reasons"] = score_data["reasons"]
            
            scored_coins.append(coin)
            
            # Stats
            market_cap = coin.get("market_cap", 0)
            if market_cap < 10_000_000:
                self.stats["degen_gems"] += 1
            elif market_cap < 100_000_000:
                self.stats["mid_caps"] += 1
            else:
                self.stats["large_caps"] += 1
        
        # Sort by score (highest first)
        scored_coins.sort(key=lambda x: x["rank_score"], reverse=True)
        
        # Get top N
        top_n = self.config["top_n"]
        top_candidates = scored_coins[:top_n]
        
        self.stats["top_ranked"] = len(top_candidates)
        
        # Log top candidates
        logger.info(f"🎯 Top {len(top_candidates)} ranked candidates:")
        for i, coin in enumerate(top_candidates[:10], 1):  # Show top 10
            symbol = coin.get("symbol", "UNKNOWN")
            score = coin["rank_score"]
            market_cap = coin.get("market_cap", 0)
            reasons = ", ".join(coin["rank_reasons"][:2])  # Top 2 reasons
            
            logger.info(
                f"#{i} {symbol}: Score={score:.2f}, "
                f"MCap=${market_cap/1e6:.1f}M, {reasons}"
            )
        
        logger.info(
            f"📈 Distribution: {self.stats['degen_gems']} degen gems, "
            f"{self.stats['mid_caps']} mid caps, {self.stats['large_caps']} large caps"
        )
        
        return top_candidates
    
    def _calculate_score(self, coin: Dict) -> Dict:
        """
        Calculate composite score for a coin
        
        Returns:
            {
                "total_score": float,
                "breakdown": dict,
                "reasons": list
            }
        """
        breakdown = {}
        reasons = []
        
        # Factor 1: Social Surge
        social_volume = coin.get("social_volume_24h", 0)
        social_volume_avg = coin.get("social_volume_avg", 1)
        social_surge_ratio = social_volume / social_volume_avg if social_volume_avg > 0 else 1
        
        if social_surge_ratio > self.config["social_surge_threshold"]:
            social_score = 100  # Max score!
            reasons.append(f"Social surge {social_surge_ratio:.0f}x")
        elif social_surge_ratio > 3:
            social_score = 50 + (social_surge_ratio / self.config["social_surge_threshold"] * 50)
            reasons.append(f"Social rising {social_surge_ratio:.1f}x")
        else:
            social_score = social_surge_ratio * 10
        
        breakdown["social_surge"] = social_score * self.config["weight_social_surge"]
        
        # Factor 2: AltRank Jump
        alt_rank = coin.get("alt_rank", 10000)
        alt_rank_prev = coin.get("alt_rank_previous", 10000)
        alt_rank_jump = alt_rank_prev - alt_rank  # Positive = improving
        
        if alt_rank_jump > self.config["altrank_jump_threshold"]:
            altrank_score = 100
            reasons.append(f"AltRank +{alt_rank_jump}")
        elif alt_rank_jump > 100:
            altrank_score = (alt_rank_jump / self.config["altrank_jump_threshold"]) * 100
            reasons.append(f"AltRank improving")
        else:
            altrank_score = max(0, alt_rank_jump / 10)
        
        breakdown["altrank_jump"] = altrank_score * self.config["weight_altrank_jump"]
        
        # Factor 3: Early Stage (Micro Cap Bonus)
        market_cap = coin.get("market_cap", 0)
        
        if market_cap < 1_000_000:  # <$1M = ultra degen
            early_stage_score = 100
            reasons.append(f"Ultra micro ${market_cap/1e6:.2f}M")
        elif market_cap < self.config["micro_cap_threshold"]:  # <$10M = degen
            early_stage_score = 80
            reasons.append(f"Micro cap ${market_cap/1e6:.1f}M")
        elif market_cap < 50_000_000:  # <$50M = small
            early_stage_score = 50
        elif market_cap < 100_000_000:  # <$100M = mid
            early_stage_score = 30
        else:  # >$100M = large (still ok!)
            early_stage_score = 10
        
        breakdown["early_stage"] = early_stage_score * self.config["weight_early_stage"]
        
        # Factor 4: Volume Spike
        volume_24h = coin.get("volume_24h", 0)
        volume_avg = coin.get("volume_avg", 1)
        volume_spike_ratio = volume_24h / volume_avg if volume_avg > 0 else 1
        
        if volume_spike_ratio > self.config["volume_spike_threshold"]:
            volume_score = min(100, volume_spike_ratio * 20)
            reasons.append(f"Volume {volume_spike_ratio:.1f}x")
        else:
            volume_score = volume_spike_ratio * 10
        
        breakdown["volume_spike"] = volume_score * self.config["weight_volume_spike"]
        
        # Factor 5: Sentiment
        sentiment = coin.get("sentiment", 50)
        
        if sentiment > 80:  # Extreme bullish
            sentiment_score = 100
            reasons.append(f"Bullish sentiment {sentiment:.0f}")
        elif sentiment < 20:  # Extreme bearish (contrarian opportunity)
            sentiment_score = 80
            reasons.append(f"Bearish (contrarian) {sentiment:.0f}")
        elif sentiment > 60:
            sentiment_score = 60
        elif sentiment < 40:
            sentiment_score = 40
        else:
            sentiment_score = 30  # Neutral
        
        breakdown["sentiment"] = sentiment_score * self.config["weight_sentiment"]
        
        # Total score
        total_score = sum(breakdown.values())
        
        # Bonus: If multiple strong signals, boost score
        strong_signals = 0
        if social_surge_ratio > 3:
            strong_signals += 1
        if alt_rank_jump > 200:
            strong_signals += 1
        if market_cap < 10_000_000:
            strong_signals += 1
        if volume_spike_ratio > 2:
            strong_signals += 1
        
        if strong_signals >= 3:
            total_score *= 1.2  # 20% bonus
            reasons.insert(0, f"{strong_signals} strong signals!")
        
        return {
            "total_score": total_score,
            "breakdown": breakdown,
            "reasons": reasons if reasons else ["Standard ranking"]
        }
    
    def get_stats(self) -> Dict:
        """Get ranking statistics"""
        return {
            **self.stats,
            "degen_ratio": (
                self.stats["degen_gems"] / self.stats["total_coins"] * 100
                if self.stats["total_coins"] > 0 else 0
            )
        }
    
    def explain_ranking(self, coin: Dict) -> str:
        """Generate human-readable explanation of ranking"""
        symbol = coin.get("symbol", "UNKNOWN")
        score = coin.get("rank_score", 0)
        breakdown = coin.get("score_breakdown", {})
        reasons = coin.get("rank_reasons", [])
        
        explanation = f"""
🎯 {symbol} Ranking: {score:.2f}/100

Top Reasons:
{chr(10).join(f"  • {reason}" for reason in reasons[:5])}

Score Breakdown:
  • Social Surge: {breakdown.get('social_surge', 0):.1f}
  • AltRank Jump: {breakdown.get('altrank_jump', 0):.1f}
  • Early Stage: {breakdown.get('early_stage', 0):.1f}
  • Volume Spike: {breakdown.get('volume_spike', 0):.1f}
  • Sentiment: {breakdown.get('sentiment', 0):.1f}

Market Data:
  • Market Cap: ${coin.get('market_cap', 0)/1e6:.2f}M
  • Volume 24h: ${coin.get('volume_24h', 0)/1e6:.2f}M
  • Social Volume: {coin.get('social_volume_24h', 0)}
  • AltRank: {coin.get('alt_rank', 'N/A')}
  • Sentiment: {coin.get('sentiment', 50)}/100
"""
        
        return explanation.strip()
