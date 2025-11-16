"""
Alpha AI Autotrader - Web Research
Web scraping and research capabilities for agents
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from loguru import logger
from bs4 import BeautifulSoup
import re


class WebResearcher:
    """
    Web Researcher - Internet research capabilities
    
    Capabilities:
    - Scrape CoinGecko, CoinMarketCap
    - Search Twitter/Reddit for sentiment
    - Aggregate crypto news
    - Check for red flags (scams, exploits)
    - Whale tracking
    """
    
    def __init__(self):
        """Initialize web researcher"""
        self.session = None
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("✅ Web Researcher initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def research_coin(self, symbol: str) -> Dict:
        """
        Comprehensive research on a coin
        
        Args:
            symbol: Coin symbol (e.g., "BTC")
        
        Returns:
            Research report
        """
        logger.info(f"🔍 Researching {symbol}...")
        
        # Run research tasks in parallel
        tasks = [
            self.get_coingecko_data(symbol),
            self.get_coinmarketcap_data(symbol),
            self.search_news(symbol),
            self.check_red_flags(symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        coingecko_data = results[0] if not isinstance(results[0], Exception) else {}
        cmc_data = results[1] if not isinstance(results[1], Exception) else {}
        news = results[2] if not isinstance(results[2], Exception) else []
        red_flags = results[3] if not isinstance(results[3], Exception) else []
        
        report = {
            "symbol": symbol,
            "coingecko": coingecko_data,
            "coinmarketcap": cmc_data,
            "news": news,
            "red_flags": red_flags,
            "research_score": self._calculate_research_score(
                coingecko_data,
                cmc_data,
                news,
                red_flags
            )
        }
        
        logger.info(f"✅ Research complete for {symbol}: Score={report['research_score']:.1f}/10")
        
        return report
    
    async def get_coingecko_data(self, symbol: str) -> Dict:
        """
        Scrape CoinGecko for coin data
        
        Args:
            symbol: Coin symbol
        
        Returns:
            CoinGecko data
        """
        try:
            # CoinGecko API (free tier)
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            
            session = await self._get_session()
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "name": data.get("name", ""),
                        "description": data.get("description", {}).get("en", "")[:500],
                        "market_cap_rank": data.get("market_cap_rank", 0),
                        "developer_score": data.get("developer_score", 0),
                        "community_score": data.get("community_score", 0),
                        "liquidity_score": data.get("liquidity_score", 0),
                        "public_interest_score": data.get("public_interest_score", 0),
                        "categories": data.get("categories", []),
                        "links": {
                            "homepage": data.get("links", {}).get("homepage", []),
                            "twitter": data.get("links", {}).get("twitter_screen_name", ""),
                            "telegram": data.get("links", {}).get("telegram_channel_identifier", "")
                        }
                    }
                else:
                    logger.warning(f"CoinGecko API returned {response.status}")
                    return {}
        
        except Exception as e:
            logger.error(f"Failed to get CoinGecko data: {e}")
            return {}
    
    async def get_coinmarketcap_data(self, symbol: str) -> Dict:
        """
        Scrape CoinMarketCap for coin data
        
        Args:
            symbol: Coin symbol
        
        Returns:
            CoinMarketCap data
        """
        try:
            url = f"https://coinmarketcap.com/currencies/{symbol.lower()}/"
            
            session = await self._get_session()
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Extract basic info (this is simplified, actual scraping may need updates)
                    return {
                        "url": url,
                        "found": True,
                        "note": "CoinMarketCap data (simplified scraping)"
                    }
                else:
                    return {"found": False}
        
        except Exception as e:
            logger.error(f"Failed to get CoinMarketCap data: {e}")
            return {"found": False}
    
    async def search_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Search for recent news about the coin
        
        Args:
            symbol: Coin symbol
            limit: Max number of news items
        
        Returns:
            List of news items
        """
        try:
            # Use CryptoPanic API (free tier)
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies={symbol}&kind=news"
            
            session = await self._get_session()
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    news_items = []
                    for post in data.get("results", [])[:limit]:
                        news_items.append({
                            "title": post.get("title", ""),
                            "url": post.get("url", ""),
                            "published_at": post.get("published_at", ""),
                            "source": post.get("source", {}).get("title", ""),
                            "votes": post.get("votes", {})
                        })
                    
                    return news_items
                else:
                    return []
        
        except Exception as e:
            logger.error(f"Failed to search news: {e}")
            return []
    
    async def check_red_flags(self, symbol: str) -> List[str]:
        """
        Check for red flags (scams, exploits, warnings)
        
        Args:
            symbol: Coin symbol
        
        Returns:
            List of red flags
        """
        red_flags = []
        
        try:
            # Search for scam warnings
            search_terms = [
                f"{symbol} scam",
                f"{symbol} exploit",
                f"{symbol} rug pull",
                f"{symbol} hack"
            ]
            
            session = await self._get_session()
            
            for term in search_terms:
                # Simple Google search (note: may be rate-limited)
                url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
                
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Check if there are many results (simplified)
                            if "About" in html and "results" in html:
                                # Extract result count (very simplified)
                                match = re.search(r'About ([\d,]+) results', html)
                                if match:
                                    count = int(match.group(1).replace(',', ''))
                                    if count > 1000:
                                        red_flags.append(f"Many search results for '{term}' ({count:,})")
                except:
                    pass
            
            return red_flags
        
        except Exception as e:
            logger.error(f"Failed to check red flags: {e}")
            return []
    
    async def search_twitter_sentiment(self, symbol: str) -> Dict:
        """
        Search Twitter for sentiment (simplified - would need Twitter API)
        
        Args:
            symbol: Coin symbol
        
        Returns:
            Sentiment data
        """
        # Note: This would require Twitter API credentials
        # For now, return placeholder
        
        logger.info(f"Twitter sentiment search for {symbol} (placeholder)")
        
        return {
            "available": False,
            "note": "Twitter API integration required"
        }
    
    async def search_reddit_sentiment(self, symbol: str) -> Dict:
        """
        Search Reddit for sentiment
        
        Args:
            symbol: Coin symbol
        
        Returns:
            Sentiment data
        """
        try:
            # Reddit search (no API key needed for basic search)
            url = f"https://www.reddit.com/search.json?q={symbol}&sort=new&limit=10"
            
            session = await self._get_session()
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    posts = data.get("data", {}).get("children", [])
                    
                    # Analyze sentiment (simplified)
                    positive_keywords = ["bullish", "moon", "buy", "pump", "up"]
                    negative_keywords = ["bearish", "dump", "sell", "down", "crash"]
                    
                    positive_count = 0
                    negative_count = 0
                    
                    for post in posts:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "").lower()
                        
                        for keyword in positive_keywords:
                            if keyword in title:
                                positive_count += 1
                        
                        for keyword in negative_keywords:
                            if keyword in title:
                                negative_count += 1
                    
                    total = positive_count + negative_count
                    sentiment_score = (positive_count / total * 100) if total > 0 else 50
                    
                    return {
                        "posts_analyzed": len(posts),
                        "positive_mentions": positive_count,
                        "negative_mentions": negative_count,
                        "sentiment_score": sentiment_score,
                        "sentiment": "bullish" if sentiment_score > 60 else "bearish" if sentiment_score < 40 else "neutral"
                    }
                else:
                    return {"available": False}
        
        except Exception as e:
            logger.error(f"Failed to search Reddit: {e}")
            return {"available": False}
    
    def _calculate_research_score(
        self,
        coingecko_data: Dict,
        cmc_data: Dict,
        news: List[Dict],
        red_flags: List[str]
    ) -> float:
        """
        Calculate overall research score (0-10)
        
        Args:
            coingecko_data: CoinGecko data
            cmc_data: CoinMarketCap data
            news: News items
            red_flags: Red flags found
        
        Returns:
            Research score (0-10)
        """
        score = 5.0  # Base score
        
        # CoinGecko scores
        if coingecko_data:
            dev_score = coingecko_data.get("developer_score", 0)
            community_score = coingecko_data.get("community_score", 0)
            
            score += (dev_score / 100) * 2  # Up to +2
            score += (community_score / 100) * 1  # Up to +1
        
        # News sentiment
        if news:
            positive_news = sum(
                1 for n in news
                if n.get("votes", {}).get("positive", 0) > n.get("votes", {}).get("negative", 0)
            )
            news_ratio = positive_news / len(news)
            score += news_ratio * 1  # Up to +1
        
        # Red flags penalty
        score -= len(red_flags) * 0.5  # -0.5 per red flag
        
        # Clamp to 0-10
        return max(0, min(10, score))
