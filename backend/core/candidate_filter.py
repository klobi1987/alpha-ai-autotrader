"""
Alpha AI Autotrader - Candidate Filter System
Intelligent filtering to reduce AI analysis load
"""
from typing import List, Dict, Optional
from loguru import logger


class CandidateFilter:
    """
    Smart filtering system to identify top trading candidates
    
    Filters coins through multiple stages BEFORE AI analysis:
    1. LunarCrush social metrics
    2. Market cap & volume thresholds
    3. Technical indicators
    4. MEXC market data validation
    
    Goal: Reduce 100+ coins to 5-10 TOP candidates for AI analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Filter configuration
        """
        self.config = config or self._default_config()
        self.stats = {
            "total_scanned": 0,
            "passed_social_filter": 0,
            "passed_market_filter": 0,
            "passed_technical_filter": 0,
            "final_candidates": 0
        }
    
    def _default_config(self) -> Dict:
        """Default filter configuration"""
        return {
            # Social filters (LunarCrush)
            "min_social_dominance": 0.1,  # >0.1% of total social activity
            "min_interactions_24h": 1000,  # Minimum engagement
            "min_galaxy_score": 40,  # Quality threshold
            
            # Market filters
            "min_market_cap": 10_000_000,  # $10M minimum
            "min_volume_24h": 1_000_000,  # $1M minimum
            "max_volatility": 0.30,  # <30% volatility (too risky)
            
            # Technical filters
            "min_price_change_24h": -20,  # Not crashing
            "max_price_change_24h": 100,  # Not pumping too hard
            
            # Output limits
            "max_candidates": 10  # Maximum candidates to pass to AI
        }
    
    def filter_candidates(
        self,
        coins: List[Dict],
        mexc_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Filter coins through all stages
        
        Args:
            coins: List of LunarCrush coin data
            mexc_data: Optional MEXC market data for validation
        
        Returns:
            List of top candidates (5-10 coins)
        """
        self.stats["total_scanned"] = len(coins)
        
        logger.info(f"🔍 Filtering {len(coins)} coins...")
        
        # Stage 1: Social filters
        social_passed = self._filter_social_metrics(coins)
        self.stats["passed_social_filter"] = len(social_passed)
        logger.info(f"✅ Social filter: {len(social_passed)}/{len(coins)} passed")
        
        # Stage 2: Market filters
        market_passed = self._filter_market_metrics(social_passed)
        self.stats["passed_market_filter"] = len(market_passed)
        logger.info(f"✅ Market filter: {len(market_passed)}/{len(social_passed)} passed")
        
        # Stage 3: Technical filters
        technical_passed = self._filter_technical_metrics(market_passed)
        self.stats["passed_technical_filter"] = len(technical_passed)
        logger.info(f"✅ Technical filter: {len(technical_passed)}/{len(market_passed)} passed")
        
        # Stage 4: MEXC validation (if data available)
        if mexc_data:
            validated = self._validate_with_mexc(technical_passed, mexc_data)
            logger.info(f"✅ MEXC validation: {len(validated)}/{len(technical_passed)} passed")
        else:
            validated = technical_passed
        
        # Stage 5: Rank and limit
        final_candidates = self._rank_and_limit(validated)
        self.stats["final_candidates"] = len(final_candidates)
        
        logger.info(f"🎯 Final candidates: {len(final_candidates)}")
        
        return final_candidates
    
    def _filter_social_metrics(self, coins: List[Dict]) -> List[Dict]:
        """Filter by social metrics (LunarCrush)"""
        filtered = []
        
        for coin in coins:
            # Social dominance check
            social_dom = coin.get("social_dominance", 0)
            if social_dom < self.config["min_social_dominance"]:
                continue
            
            # Interactions check
            interactions = coin.get("interactions_24h", 0)
            if interactions < self.config["min_interactions_24h"]:
                continue
            
            # Galaxy score (quality) check
            galaxy = coin.get("galaxy_score", 0)
            if galaxy < self.config["min_galaxy_score"]:
                continue
            
            # Passed all social filters
            filtered.append(coin)
        
        return filtered
    
    def _filter_market_metrics(self, coins: List[Dict]) -> List[Dict]:
        """Filter by market cap and volume"""
        filtered = []
        
        for coin in coins:
            # Market cap check
            market_cap = coin.get("market_cap", 0)
            if market_cap < self.config["min_market_cap"]:
                continue
            
            # Volume check
            volume_24h = coin.get("volume_24h", 0)
            if volume_24h < self.config["min_volume_24h"]:
                continue
            
            # Volatility check (if too high, too risky)
            volatility = coin.get("volatility", 0)
            if volatility > self.config["max_volatility"]:
                continue
            
            # Passed all market filters
            filtered.append(coin)
        
        return filtered
    
    def _filter_technical_metrics(self, coins: List[Dict]) -> List[Dict]:
        """Filter by technical indicators"""
        filtered = []
        
        for coin in coins:
            # Price change check (avoid extreme moves)
            price_change_24h = coin.get("percent_change_24h", 0)
            
            if price_change_24h < self.config["min_price_change_24h"]:
                # Crashing too hard
                continue
            
            if price_change_24h > self.config["max_price_change_24h"]:
                # Pumping too hard (likely to dump)
                continue
            
            # AltRank momentum (optional bonus)
            alt_rank = coin.get("alt_rank", 0)
            alt_rank_prev = coin.get("alt_rank_previous", 0)
            
            if alt_rank and alt_rank_prev:
                alt_rank_change = alt_rank_prev - alt_rank
                coin["alt_rank_change"] = alt_rank_change
                
                # Bonus for improving AltRank
                if alt_rank_change > 0:
                    coin["filter_score"] = coin.get("filter_score", 0) + 1
            
            # Sentiment bonus
            sentiment = coin.get("sentiment", 50)
            if sentiment > 70 or sentiment < 30:  # Extreme sentiment
                coin["filter_score"] = coin.get("filter_score", 0) + 1
            
            # Passed all technical filters
            filtered.append(coin)
        
        return filtered
    
    def _validate_with_mexc(
        self,
        coins: List[Dict],
        mexc_data: Dict
    ) -> List[Dict]:
        """
        Validate candidates with MEXC market data
        
        Checks:
        - Symbol exists on MEXC
        - Sufficient liquidity
        - Order book depth
        """
        validated = []
        
        for coin in coins:
            symbol = coin.get("symbol", "")
            
            # Check if symbol exists in MEXC data
            mexc_symbol = f"{symbol}/USDT"
            if mexc_symbol not in mexc_data:
                continue
            
            # Get MEXC ticker
            ticker = mexc_data.get(mexc_symbol, {})
            
            # Validate volume
            mexc_volume = ticker.get("quoteVolume", 0)
            if mexc_volume < self.config["min_volume_24h"]:
                continue
            
            # Add MEXC data to coin
            coin["mexc_ticker"] = ticker
            
            validated.append(coin)
        
        return validated
    
    def _rank_and_limit(self, coins: List[Dict]) -> List[Dict]:
        """
        Rank candidates and limit to top N
        
        Ranking factors:
        - Social dominance (weight: 30%)
        - Interactions (weight: 25%)
        - Galaxy score (weight: 20%)
        - AltRank change (weight: 15%)
        - Filter score (weight: 10%)
        """
        # Calculate composite score
        for coin in coins:
            social_dom = coin.get("social_dominance", 0)
            interactions = coin.get("interactions_24h", 0)
            galaxy = coin.get("galaxy_score", 0)
            alt_rank_change = coin.get("alt_rank_change", 0)
            filter_score = coin.get("filter_score", 0)
            
            # Normalize and weight
            score = (
                (social_dom / 1.0) * 30 +  # Normalize to max 1%
                (interactions / 100000) * 25 +  # Normalize to 100k
                (galaxy / 100) * 20 +
                (alt_rank_change / 1000) * 15 +
                filter_score * 10
            )
            
            coin["candidate_score"] = score
        
        # Sort by score
        coins.sort(key=lambda x: x.get("candidate_score", 0), reverse=True)
        
        # Limit to top N
        max_candidates = self.config["max_candidates"]
        top_candidates = coins[:max_candidates]
        
        # Log top candidates
        for i, coin in enumerate(top_candidates, 1):
            logger.info(
                f"#{i} {coin.get('symbol', 'UNKNOWN')}: "
                f"Score={coin.get('candidate_score', 0):.2f}, "
                f"Social={coin.get('social_dominance', 0):.3f}%, "
                f"Galaxy={coin.get('galaxy_score', 0):.1f}"
            )
        
        return top_candidates
    
    def get_stats(self) -> Dict:
        """Get filter statistics"""
        return {
            **self.stats,
            "filter_rate": (
                (1 - self.stats["final_candidates"] / self.stats["total_scanned"])
                * 100
                if self.stats["total_scanned"] > 0 else 0
            )
        }
