"""
Alpha AI Autotrader - LunarCrush API Integration
Smart caching strategy optimized for Individual plan (1000 calls/day)
"""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger


class LunarCrushCache:
    """In-memory cache for LunarCrush data"""
    
    def __init__(self, ttl: int = 300):
        """
        Args:
            ttl: Time-to-live in seconds (default 5 minutes)
        """
        self.ttl = ttl
        self.cache: Dict[str, Dict] = {}
        self.timestamps: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if fresh"""
        if key not in self.cache:
            return None
        
        if datetime.utcnow() - self.timestamps[key] > timedelta(seconds=self.ttl):
            # Cache expired
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        logger.debug(f"Cache HIT for {key}")
        return self.cache[key]
    
    def set(self, key: str, data: Dict):
        """Store data in cache"""
        self.cache[key] = data
        self.timestamps[key] = datetime.utcnow()
        logger.debug(f"Cache SET for {key}")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
        logger.info("Cache cleared")


class LunarCrushClient:
    """
    LunarCrush API Client with smart caching
    
    Optimized for Individual plan:
    - 1000 calls/day limit
    - Strategy: Fetch /coins/list every 5 min (288 calls/day)
    - Leaves 712 calls for backup/additional requests
    """
    
    BASE_URL = "https://lunarcrush.com/api4/public"
    
    def __init__(self, api_key: str, cache_ttl: int = 300):
        """
        Args:
            api_key: LunarCrush API key
            cache_ttl: Cache time-to-live in seconds (default 5 min)
        """
        self.api_key = api_key
        self.cache = LunarCrushCache(ttl=cache_ttl)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        # Stats
        self.total_requests = 0
        self.cache_hits = 0
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            self.total_requests += 1
            logger.info(f"LunarCrush API call #{self.total_requests}: {endpoint}")
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LunarCrush API error: {e}")
            raise
    
    def get_coins_list(
        self,
        limit: int = 100,
        sort: str = "social_volume_24h",
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        Get top coins with all metrics
        
        This is the PRIMARY endpoint - provides 30+ metrics per coin in one call
        
        Args:
            limit: Number of coins to fetch (max 500)
            sort: Sort field (interactions_24h, alt_rank, galaxy_score, social_volume_24h, etc.)
            force_refresh: Skip cache and fetch fresh data
        
        Returns:
            List of coin dictionaries with full metrics
        """
        cache_key = f"coins_list_{limit}_{sort}"
        
        # Check cache first
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        # Fetch from API (use v1 endpoint)
        data = self._make_request("coins/list/v1", params={
            "limit": limit,
            "sort": sort
        })
        
        coins = data.get("data", [])
        
        # Cache the result
        self.cache.set(cache_key, coins)
        
        logger.info(f"Fetched {len(coins)} coins from LunarCrush")
        return coins
    
    def get_coin_details(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get detailed data for a specific coin
        
        NOTE: Use sparingly - prefer get_coins_list() which gives 100+ coins in one call
        
        Args:
            symbol: Coin symbol (e.g., "BTC", "ETH")
            force_refresh: Skip cache
        
        Returns:
            Coin data dictionary or None
        """
        cache_key = f"coin_{symbol}"
        
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            data = self._make_request(f"coins/{symbol}")
            coin = data.get("data", {})
            
            self.cache.set(cache_key, coin)
            return coin
        
        except Exception as e:
            logger.warning(f"Failed to fetch coin {symbol}: {e}")
            return None
    
    def get_top_movers(self, limit: int = 20) -> List[Dict]:
        """
        Get coins with biggest AltRank jumps
        
        Uses cached data from get_coins_list()
        """
        coins = self.get_coins_list(limit=100, sort="alt_rank")
        
        # Calculate AltRank change
        movers = []
        for coin in coins:
            alt_rank = coin.get("alt_rank", 0)
            alt_rank_prev = coin.get("alt_rank_previous", 0)
            
            if alt_rank and alt_rank_prev:
                change = alt_rank_prev - alt_rank  # Positive = moved up
                if change > 0:
                    coin["alt_rank_change"] = change
                    movers.append(coin)
        
        # Sort by biggest jumps
        movers.sort(key=lambda x: x.get("alt_rank_change", 0), reverse=True)
        
        return movers[:limit]
    
    def get_high_sentiment_coins(self, min_sentiment: float = 80, limit: int = 20) -> List[Dict]:
        """
        Get coins with high sentiment scores
        
        Uses cached data from get_coins_list()
        """
        coins = self.get_coins_list(limit=100)
        
        high_sentiment = [
            coin for coin in coins
            if coin.get("sentiment", 0) >= min_sentiment
        ]
        
        # Sort by sentiment
        high_sentiment.sort(key=lambda x: x.get("sentiment", 0), reverse=True)
        
        return high_sentiment[:limit]
    
    def get_social_surge_coins(self, surge_multiplier: float = 2.0, limit: int = 20) -> List[Dict]:
        """
        Detect coins with social volume surge
        
        NOTE: Requires historical data to calculate average
        For now, uses simple heuristic based on social_dominance
        """
        coins = self.get_coins_list(limit=100)
        
        surge_coins = []
        for coin in coins:
            social_vol = coin.get("social_volume_24h", 0)
            social_dom = coin.get("social_dominance", 0)
            
            # Simple heuristic: high social dominance = surge
            if social_dom > 0.5:  # >0.5% of total social activity
                coin["social_surge_score"] = social_dom
                surge_coins.append(coin)
        
        surge_coins.sort(key=lambda x: x.get("social_surge_score", 0), reverse=True)
        
        return surge_coins[:limit]
    
    def get_quality_coins(self, min_galaxy_score: float = 70, limit: int = 20) -> List[Dict]:
        """
        Get high-quality coins based on Galaxy Score
        
        Uses cached data from get_coins_list()
        """
        coins = self.get_coins_list(limit=100)
        
        quality = [
            coin for coin in coins
            if coin.get("galaxy_score", 0) >= min_galaxy_score
        ]
        
        quality.sort(key=lambda x: x.get("galaxy_score", 0), reverse=True)
        
        return quality[:limit]
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": (
                self.cache_hits / self.total_requests * 100
                if self.total_requests > 0 else 0
            ),
            "estimated_daily_calls": self.total_requests * (86400 / (time.time() - self.last_request_time))
            if self.last_request_time > 0 else 0
        }
    
    def get_coin_timeseries(
        self,
        coin: str,
        bucket: str = "hour",
        interval: str = "1w"
    ) -> Dict:
        """
        Get time-series data for a specific coin
        
        ⚠️ EXPENSIVE: Use only for final deep analysis (1 call per coin)
        
        Args:
            coin: Coin ID or symbol
            bucket: "hour" or "day"
            interval: "1d", "1w", "1m", etc.
        
        Returns:
            Time-series data with historical metrics
        """
        cache_key = f"timeseries_{coin}_{bucket}_{interval}"
        
        # Check cache (longer TTL for time-series)
        cached = self.cache.get(cache_key)
        if cached:
            self.cache_hits += 1
            return cached
        
        try:
            logger.warning(f"⚠️ EXPENSIVE CALL: Fetching time-series for {coin}")
            
            data = self._make_request(
                f"coins/{coin}/time-series/v2",
                params={
                    "bucket": bucket,
                    "interval": interval
                }
            )
            
            timeseries = data.get("data", [])
            
            # Cache with longer TTL (30 min)
            self.cache.set(cache_key, timeseries)
            
            logger.info(f"✅ Fetched {len(timeseries)} time-series points for {coin}")
            return timeseries
        
        except Exception as e:
            logger.error(f"Failed to fetch time-series for {coin}: {e}")
            return []
    
    def analyze_trend(self, timeseries: List[Dict]) -> Dict:
        """
        Analyze trend from time-series data
        
        Args:
            timeseries: Time-series data from get_coin_timeseries()
        
        Returns:
            Trend analysis
        """
        if not timeseries or len(timeseries) < 2:
            return {"trend": "unknown", "strength": 0}
        
        # Extract metrics over time
        sentiments = [t.get("sentiment", 0) for t in timeseries if t.get("sentiment")]
        social_volumes = [t.get("social_volume", 0) for t in timeseries if t.get("social_volume")]
        altranks = [t.get("alt_rank", 0) for t in timeseries if t.get("alt_rank")]
        
        analysis = {}
        
        # Sentiment trend
        if len(sentiments) >= 2:
            sentiment_change = sentiments[-1] - sentiments[0]
            analysis["sentiment_trend"] = "rising" if sentiment_change > 5 else "falling" if sentiment_change < -5 else "stable"
            analysis["sentiment_change"] = sentiment_change
        
        # Social volume trend
        if len(social_volumes) >= 2:
            social_change_pct = ((social_volumes[-1] - social_volumes[0]) / social_volumes[0] * 100) if social_volumes[0] > 0 else 0
            analysis["social_trend"] = "surging" if social_change_pct > 50 else "declining" if social_change_pct < -50 else "stable"
            analysis["social_change_pct"] = social_change_pct
        
        # AltRank trend (lower is better)
        if len(altranks) >= 2:
            altrank_change = altranks[0] - altranks[-1]  # Positive = improved
            analysis["altrank_trend"] = "improving" if altrank_change > 100 else "declining" if altrank_change < -100 else "stable"
            analysis["altrank_change"] = altrank_change
        
        # Overall trend strength (0-10)
        strength = 5.0
        if analysis.get("sentiment_trend") == "rising":
            strength += 1.5
        if analysis.get("social_trend") == "surging":
            strength += 2.0
        if analysis.get("altrank_trend") == "improving":
            strength += 1.5
        
        analysis["overall_trend"] = "bullish" if strength > 6.5 else "bearish" if strength < 4.5 else "neutral"
        analysis["trend_strength"] = min(10, max(0, strength))
        
        return analysis
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
