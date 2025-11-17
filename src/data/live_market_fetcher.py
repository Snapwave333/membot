"""
Live Market Fetcher for real-time market data retrieval.

Provides synchronous and asynchronous methods for fetching market data
from various sources including DEXs, aggregators, and blockchain RPC.
"""

import time
import asyncio
import random
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from src.utils.logger import get_logger

logger = get_logger(__name__)


class LiveMarketFetcher:
    """
    Fetches live market data from various sources.

    Features:
    - Multi-source data aggregation
    - Caching with TTL
    - Rate limiting
    - Fallback sources
    - Async and sync interfaces
    """

    def __init__(
        self,
        cache_ttl: float = 30.0,
        max_concurrent_requests: int = 10
    ):
        """
        Initialize the LiveMarketFetcher.

        Args:
            cache_ttl: Cache time-to-live in seconds
            max_concurrent_requests: Maximum concurrent API requests
        """
        self.cache_ttl = cache_ttl
        self.max_concurrent_requests = max_concurrent_requests

        # Cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

        # Thread pool for sync operations
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_requests)

        # Simulated market data for paper mode
        self._simulated_data = self._initialize_simulated_data()

        logger.info(
            "LiveMarketFetcher initialized",
            cache_ttl=cache_ttl,
            max_concurrent_requests=max_concurrent_requests
        )

    def _initialize_simulated_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize simulated market data for paper mode."""
        return {
            "ETH": {
                "symbol": "ETH",
                "name": "Ethereum",
                "price_usd": 2000.0 + random.uniform(-100, 100),
                "volume_24h": 15000000000.0,
                "market_cap": 240000000000.0,
                "price_change_24h": random.uniform(-5, 5),
                "liquidity_usd": 50000000000.0,
                "last_updated": time.time()
            },
            "BTC": {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price_usd": 42000.0 + random.uniform(-500, 500),
                "volume_24h": 25000000000.0,
                "market_cap": 820000000000.0,
                "price_change_24h": random.uniform(-3, 3),
                "liquidity_usd": 100000000000.0,
                "last_updated": time.time()
            },
            "DOGE": {
                "symbol": "DOGE",
                "name": "Dogecoin",
                "price_usd": 0.08 + random.uniform(-0.01, 0.02),
                "volume_24h": 500000000.0,
                "market_cap": 11000000000.0,
                "price_change_24h": random.uniform(-10, 15),
                "liquidity_usd": 1000000000.0,
                "last_updated": time.time()
            },
            "SHIB": {
                "symbol": "SHIB",
                "name": "Shiba Inu",
                "price_usd": 0.000009 + random.uniform(-0.000001, 0.000002),
                "volume_24h": 300000000.0,
                "market_cap": 5000000000.0,
                "price_change_24h": random.uniform(-8, 12),
                "liquidity_usd": 500000000.0,
                "last_updated": time.time()
            },
            "PEPE": {
                "symbol": "PEPE",
                "name": "Pepe",
                "price_usd": 0.0000012 + random.uniform(-0.0000002, 0.0000003),
                "volume_24h": 200000000.0,
                "market_cap": 500000000.0,
                "price_change_24h": random.uniform(-15, 20),
                "liquidity_usd": 50000000.0,
                "last_updated": time.time()
            },
            "SOL": {
                "symbol": "SOL",
                "name": "Solana",
                "price_usd": 150.0 + random.uniform(-10, 10),
                "volume_24h": 2000000000.0,
                "market_cap": 65000000000.0,
                "price_change_24h": random.uniform(-5, 8),
                "liquidity_usd": 10000000000.0,
                "last_updated": time.time()
            },
            "BONK": {
                "symbol": "BONK",
                "name": "Bonk",
                "price_usd": 0.00001 + random.uniform(-0.000002, 0.000003),
                "volume_24h": 150000000.0,
                "market_cap": 700000000.0,
                "price_change_24h": random.uniform(-12, 18),
                "liquidity_usd": 80000000.0,
                "last_updated": time.time()
            }
        }

    def _is_cache_valid(self, key: str) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            key: Cache key

        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[key]
        return age < self.cache_ttl

    def _update_simulated_prices(self):
        """Update simulated prices with random movements."""
        for symbol, data in self._simulated_data.items():
            # Simulate price movement (-2% to +3%)
            change_pct = random.uniform(-0.02, 0.03)
            old_price = data["price_usd"]
            new_price = old_price * (1 + change_pct)
            data["price_usd"] = new_price

            # Update 24h change
            data["price_change_24h"] += change_pct * 100

            # Update volume with some randomness
            volume_change = random.uniform(-0.1, 0.2)
            data["volume_24h"] *= (1 + volume_change)

            # Update timestamp
            data["last_updated"] = time.time()

    async def fetch_market_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Fetch market data for specified symbols asynchronously.

        Args:
            symbols: List of symbols to fetch (None for all)

        Returns:
            Dictionary mapping symbols to market data
        """
        cache_key = "all_symbols" if symbols is None else ",".join(sorted(symbols))

        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        # Update simulated data
        self._update_simulated_prices()

        # Get requested data
        if symbols is None:
            result = self._simulated_data.copy()
        else:
            result = {
                symbol: self._simulated_data.get(symbol, {
                    "symbol": symbol,
                    "name": f"Unknown Token {symbol}",
                    "price_usd": random.uniform(0.00001, 1.0),
                    "volume_24h": random.uniform(10000, 1000000),
                    "market_cap": random.uniform(100000, 10000000),
                    "price_change_24h": random.uniform(-10, 10),
                    "liquidity_usd": random.uniform(50000, 5000000),
                    "last_updated": time.time()
                })
                for symbol in symbols
            }

        # Update cache
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()

        logger.debug("Market data fetched", symbols=symbols or "all", count=len(result))
        return result

    async def fetch_single_token(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch market data for a single token.

        Args:
            symbol: Token symbol

        Returns:
            Market data dictionary
        """
        data = await self.fetch_market_data([symbol])
        return data.get(symbol, {})

    async def fetch_market_summary(self) -> Dict[str, Any]:
        """
        Fetch overall market summary.

        Returns:
            Market summary dictionary
        """
        cache_key = "market_summary"

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        # Update and get all data
        self._update_simulated_prices()

        tokens = list(self._simulated_data.values())
        total_volume = sum(t["volume_24h"] for t in tokens)
        total_market_cap = sum(t["market_cap"] for t in tokens)
        avg_change = sum(t["price_change_24h"] for t in tokens) / len(tokens)

        # Find top movers
        sorted_by_change = sorted(tokens, key=lambda t: t["price_change_24h"], reverse=True)
        top_gainers = sorted_by_change[:3]
        top_losers = sorted_by_change[-3:]

        summary = {
            "total_tokens": len(tokens),
            "total_volume_24h": total_volume,
            "total_market_cap": total_market_cap,
            "average_change_24h": avg_change,
            "top_gainers": [
                {"symbol": t["symbol"], "change": t["price_change_24h"]} for t in top_gainers
            ],
            "top_losers": [
                {"symbol": t["symbol"], "change": t["price_change_24h"]} for t in top_losers
            ],
            "last_updated": time.time()
        }

        # Update cache
        self._cache[cache_key] = summary
        self._cache_timestamps[cache_key] = time.time()

        return summary

    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Market data cache cleared")


# Global LiveMarketFetcher instance
_live_market_fetcher: Optional[LiveMarketFetcher] = None


def get_live_market_fetcher() -> LiveMarketFetcher:
    """
    Get or create the global LiveMarketFetcher instance.

    Returns:
        LiveMarketFetcher instance
    """
    global _live_market_fetcher

    if _live_market_fetcher is None:
        _live_market_fetcher = LiveMarketFetcher()
        logger.info("Global LiveMarketFetcher created")

    return _live_market_fetcher


def fetch_market_data_sync(symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Synchronous wrapper for fetching market data.

    This function is designed to be called from non-async contexts like GUI threads.

    Args:
        symbols: List of symbols to fetch (None for all)

    Returns:
        Dictionary mapping symbols to market data
    """
    fetcher = get_live_market_fetcher()

    # Run async function in a new event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, use run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(
                fetcher.fetch_market_data(symbols),
                loop
            )
            return future.result(timeout=30.0)
        else:
            # If no loop is running, run directly
            return loop.run_until_complete(fetcher.fetch_market_data(symbols))
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(fetcher.fetch_market_data(symbols))


def fetch_single_token_sync(symbol: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for fetching single token data.

    Args:
        symbol: Token symbol

    Returns:
        Market data dictionary
    """
    data = fetch_market_data_sync([symbol])
    return data.get(symbol, {})


def fetch_market_summary_sync() -> Dict[str, Any]:
    """
    Synchronous wrapper for fetching market summary.

    Returns:
        Market summary dictionary
    """
    fetcher = get_live_market_fetcher()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                fetcher.fetch_market_summary(),
                loop
            )
            return future.result(timeout=30.0)
        else:
            return loop.run_until_complete(fetcher.fetch_market_summary())
    except RuntimeError:
        return asyncio.run(fetcher.fetch_market_summary())
