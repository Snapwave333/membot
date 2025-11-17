"""
Solana Market Watcher for real-time price and volume tracking.

Monitors Solana-based token markets for price movements, volume changes,
and new token discoveries.
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.utils.logger import get_logger
from src.data.solana_rpc_connector import SolanaRPCConnector

logger = get_logger(__name__)


@dataclass
class SolanaTokenMarketData:
    """Market data for a single Solana token."""
    address: str
    symbol: str = ""
    name: str = ""
    price_usd: float = 0.0
    price_sol: float = 0.0
    volume_24h: float = 0.0
    liquidity_usd: float = 0.0
    market_cap: float = 0.0
    total_supply: float = 0.0
    holder_count: int = 0
    price_change_24h: float = 0.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class SolanaMarketEvent:
    """Solana market event notification."""
    event_type: str  # "new_token", "price_alert", "volume_spike", "liquidity_change"
    token_address: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SolanaMarketWatcher:
    """
    Monitors Solana-based token markets.

    Features:
    - Real-time price tracking
    - Volume monitoring
    - New token discovery
    - Market alerts and notifications
    - Historical data tracking
    """

    def __init__(
        self,
        rpc_connector: Optional[SolanaRPCConnector] = None,
        watch_interval: float = 30.0,
        price_alert_threshold: float = 10.0,  # 10% change
        volume_spike_threshold: float = 100.0  # 100% increase
    ):
        """
        Initialize the Solana Market Watcher.

        Args:
            rpc_connector: Optional Solana RPC connector for blockchain data
            watch_interval: Interval between market checks in seconds
            price_alert_threshold: Percentage change to trigger price alert
            volume_spike_threshold: Percentage increase to trigger volume alert
        """
        self.rpc_connector = rpc_connector
        self.watch_interval = watch_interval
        self.price_alert_threshold = price_alert_threshold
        self.volume_spike_threshold = volume_spike_threshold

        # Token tracking
        self.tracked_tokens: Dict[str, SolanaTokenMarketData] = {}
        self.token_history: Dict[str, List[SolanaTokenMarketData]] = {}

        # Market events
        self.events: List[SolanaMarketEvent] = []
        self.event_callbacks: List[callable] = []

        # Monitoring state
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Default tokens to track (major Solana tokens)
        self.default_tokens = {
            "So11111111111111111111111111111111111111112": "WSOL",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": "POPCAT",
        }

        logger.info(
            "Solana Market Watcher initialized",
            watch_interval=watch_interval,
            price_alert_threshold=price_alert_threshold,
            volume_spike_threshold=volume_spike_threshold
        )

    async def start_monitoring(self):
        """Start Solana market monitoring."""
        if self.is_monitoring:
            logger.warning("Solana market monitoring already active")
            return

        self.is_monitoring = True

        # Initialize default tokens
        for address, symbol in self.default_tokens.items():
            self.tracked_tokens[address] = SolanaTokenMarketData(
                address=address,
                symbol=symbol
            )

        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Solana Market monitoring started", token_count=len(self.tracked_tokens))

    async def stop_monitoring(self):
        """Stop Solana market monitoring."""
        self.is_monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info("Solana Market monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._update_market_data()
                await asyncio.sleep(self.watch_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in Solana monitoring loop", error=str(e))
                await asyncio.sleep(self.watch_interval)

    async def _update_market_data(self):
        """Update market data for all tracked Solana tokens."""
        logger.debug("Updating Solana market data", token_count=len(self.tracked_tokens))

        for address in list(self.tracked_tokens.keys()):
            try:
                old_data = self.tracked_tokens[address]
                new_data = await self._fetch_token_data(address)

                if new_data:
                    # Check for alerts
                    await self._check_alerts(old_data, new_data)

                    # Update tracked data
                    self.tracked_tokens[address] = new_data

                    # Store in history
                    if address not in self.token_history:
                        self.token_history[address] = []
                    self.token_history[address].append(new_data)

                    # Limit history size
                    if len(self.token_history[address]) > 1000:
                        self.token_history[address] = self.token_history[address][-1000:]

            except Exception as e:
                logger.warning("Failed to update Solana token data", address=address, error=str(e))

    async def _fetch_token_data(self, address: str) -> Optional[SolanaTokenMarketData]:
        """
        Fetch market data for a Solana token.

        Args:
            address: Token mint address

        Returns:
            SolanaTokenMarketData or None if fetch failed
        """
        try:
            # In paper mode, generate simulated data
            # In live mode, this would fetch from Jupiter, Raydium, Birdeye, etc.
            current_data = self.tracked_tokens.get(address)

            if current_data:
                # Simulate price movement
                import random
                price_change = random.uniform(-0.05, 0.08)  # -5% to +8%
                new_price = max(0.0000001, current_data.price_usd * (1 + price_change))

                volume_change = random.uniform(-0.2, 0.5)  # -20% to +50%
                new_volume = max(0, current_data.volume_24h * (1 + volume_change))

                return SolanaTokenMarketData(
                    address=address,
                    symbol=current_data.symbol,
                    name=current_data.name or current_data.symbol,
                    price_usd=new_price,
                    price_sol=new_price / 150,  # Simulated SOL price
                    volume_24h=new_volume or random.uniform(10000, 1000000),
                    liquidity_usd=current_data.liquidity_usd or random.uniform(50000, 5000000),
                    market_cap=new_price * (current_data.total_supply or 1000000000),
                    total_supply=current_data.total_supply or 1000000000,
                    holder_count=current_data.holder_count or random.randint(100, 10000),
                    price_change_24h=(new_price - current_data.price_usd) / current_data.price_usd * 100 if current_data.price_usd > 0 else 0,
                    last_updated=time.time()
                )
            else:
                # Initial data for new token
                import random
                return SolanaTokenMarketData(
                    address=address,
                    symbol=self.default_tokens.get(address, "UNKNOWN"),
                    name=self.default_tokens.get(address, "Unknown Token"),
                    price_usd=random.uniform(0.0000001, 0.01),
                    price_sol=random.uniform(0.00000001, 0.000005),
                    volume_24h=random.uniform(10000, 1000000),
                    liquidity_usd=random.uniform(50000, 5000000),
                    market_cap=random.uniform(100000, 100000000),
                    total_supply=1000000000,
                    holder_count=random.randint(100, 10000),
                    price_change_24h=0,
                    last_updated=time.time()
                )

        except Exception as e:
            logger.error("Error fetching Solana token data", address=address, error=str(e))
            return None

    async def _check_alerts(self, old_data: SolanaTokenMarketData, new_data: SolanaTokenMarketData):
        """
        Check for alert conditions.

        Args:
            old_data: Previous market data
            new_data: Current market data
        """
        # Price alert
        if old_data.price_usd > 0:
            price_change = abs((new_data.price_usd - old_data.price_usd) / old_data.price_usd * 100)
            if price_change >= self.price_alert_threshold:
                event = SolanaMarketEvent(
                    event_type="price_alert",
                    token_address=new_data.address,
                    data={
                        "old_price": old_data.price_usd,
                        "new_price": new_data.price_usd,
                        "change_percent": price_change,
                        "symbol": new_data.symbol
                    }
                )
                await self._emit_event(event)

        # Volume spike
        if old_data.volume_24h > 0:
            volume_change = (new_data.volume_24h - old_data.volume_24h) / old_data.volume_24h * 100
            if volume_change >= self.volume_spike_threshold:
                event = SolanaMarketEvent(
                    event_type="volume_spike",
                    token_address=new_data.address,
                    data={
                        "old_volume": old_data.volume_24h,
                        "new_volume": new_data.volume_24h,
                        "change_percent": volume_change,
                        "symbol": new_data.symbol
                    }
                )
                await self._emit_event(event)

    async def _emit_event(self, event: SolanaMarketEvent):
        """
        Emit a Solana market event.

        Args:
            event: Market event to emit
        """
        self.events.append(event)

        # Limit event history
        if len(self.events) > 10000:
            self.events = self.events[-10000:]

        logger.info(
            "Solana market event",
            event_type=event.event_type,
            token=event.token_address,
            data=event.data
        )

        # Call registered callbacks
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error("Error in Solana event callback", error=str(e))

    def add_token(self, address: str, symbol: str = "", name: str = ""):
        """
        Add a Solana token to track.

        Args:
            address: Token mint address
            symbol: Token symbol
            name: Token name
        """
        if address not in self.tracked_tokens:
            self.tracked_tokens[address] = SolanaTokenMarketData(
                address=address,
                symbol=symbol,
                name=name
            )
            logger.info("Solana token added to tracking", address=address, symbol=symbol)

    def remove_token(self, address: str):
        """
        Remove a Solana token from tracking.

        Args:
            address: Token mint address
        """
        if address in self.tracked_tokens:
            del self.tracked_tokens[address]
            logger.info("Solana token removed from tracking", address=address)

    def get_token_data(self, address: str) -> Optional[SolanaTokenMarketData]:
        """
        Get current market data for a Solana token.

        Args:
            address: Token mint address

        Returns:
            SolanaTokenMarketData or None
        """
        return self.tracked_tokens.get(address)

    def get_all_tokens(self) -> Dict[str, SolanaTokenMarketData]:
        """
        Get all tracked Solana tokens.

        Returns:
            Dictionary of address to SolanaTokenMarketData
        """
        return self.tracked_tokens.copy()

    def get_recent_events(self, limit: int = 100) -> List[SolanaMarketEvent]:
        """
        Get recent Solana market events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent SolanaMarketEvent objects
        """
        return self.events[-limit:]

    def register_callback(self, callback: callable):
        """
        Register a callback for Solana market events.

        Args:
            callback: Function to call on market events
        """
        self.event_callbacks.append(callback)
        logger.info("Solana event callback registered")

    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current Solana market state.

        Returns:
            Dictionary with market summary data
        """
        if not self.tracked_tokens:
            return {
                "total_tokens": 0,
                "total_volume": 0,
                "total_liquidity": 0,
                "average_price_change": 0,
                "top_gainers": [],
                "top_losers": [],
                "is_monitoring": self.is_monitoring
            }

        tokens = list(self.tracked_tokens.values())
        total_volume = sum(t.volume_24h for t in tokens)
        total_liquidity = sum(t.liquidity_usd for t in tokens)
        avg_change = sum(t.price_change_24h for t in tokens) / len(tokens)

        # Sort by price change
        sorted_by_change = sorted(tokens, key=lambda t: t.price_change_24h, reverse=True)
        top_gainers = sorted_by_change[:3]
        top_losers = sorted_by_change[-3:]

        return {
            "total_tokens": len(tokens),
            "total_volume": total_volume,
            "total_liquidity": total_liquidity,
            "average_price_change": avg_change,
            "top_gainers": [
                {"symbol": t.symbol, "change": t.price_change_24h} for t in top_gainers
            ],
            "top_losers": [
                {"symbol": t.symbol, "change": t.price_change_24h} for t in top_losers
            ],
            "is_monitoring": self.is_monitoring
        }


# Global Solana market watcher instance
_solana_market_watcher: Optional[SolanaMarketWatcher] = None


def get_solana_market_watcher(rpc_connector: Optional[SolanaRPCConnector] = None) -> SolanaMarketWatcher:
    """
    Get or create the global Solana market watcher instance.

    Args:
        rpc_connector: Optional Solana RPC connector

    Returns:
        SolanaMarketWatcher instance
    """
    global _solana_market_watcher

    if _solana_market_watcher is None:
        _solana_market_watcher = SolanaMarketWatcher(rpc_connector=rpc_connector)
        logger.info("Global Solana market watcher created")

    return _solana_market_watcher
