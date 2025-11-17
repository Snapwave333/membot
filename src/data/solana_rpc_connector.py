"""
Solana RPC connector with failover and health monitoring.

Provides reliable connection to Solana nodes with automatic failover,
rate limiting, and health tracking.
"""

import os
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import deque

import aiohttp

# Try to import Solana libraries (optional dependency)
try:
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Commitment
    from solders.pubkey import Pubkey
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    AsyncClient = None
    Commitment = None
    Pubkey = None

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SolanaConnectionStatus(Enum):
    """Connection status for Solana RPC endpoints."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class SolanaEndpointHealth:
    """Health tracking for a Solana RPC endpoint."""
    status: SolanaConnectionStatus = SolanaConnectionStatus.UNKNOWN
    consecutive_failures: int = 0
    response_time_avg: float = 0.0
    last_successful_request: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class SolanaRPCResponse:
    """Response from a Solana RPC request."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    endpoint_used: Optional[str] = None
    response_time: Optional[float] = None


class SolanaRPCConnector:
    """
    Solana RPC connector with failover and health monitoring.

    Features:
    - Multiple endpoint support with automatic failover
    - Health tracking and monitoring
    - Rate limiting
    - Async context manager support
    - Detailed error tracking
    """

    def __init__(
        self,
        primary_endpoint: str,
        secondary_endpoint: Optional[str] = None,
        max_requests_per_minute: int = 100,
        request_timeout: float = 30.0,
        max_retries: int = 3,
        commitment: str = "confirmed"
    ):
        """
        Initialize the Solana RPC connector.

        Args:
            primary_endpoint: Primary RPC endpoint URL
            secondary_endpoint: Optional secondary endpoint for failover
            max_requests_per_minute: Rate limit for requests
            request_timeout: Timeout for individual requests in seconds
            max_retries: Maximum number of retry attempts
            commitment: Commitment level for requests
        """
        self.primary_endpoint = primary_endpoint
        self.secondary_endpoint = secondary_endpoint
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.commitment = Commitment(commitment) if SOLANA_AVAILABLE and Commitment else commitment

        # Build endpoint list
        self.endpoints: List[str] = [primary_endpoint]
        if secondary_endpoint:
            self.endpoints.append(secondary_endpoint)

        # Health tracking
        self.endpoint_health: Dict[str, SolanaEndpointHealth] = {
            endpoint: SolanaEndpointHealth() for endpoint in self.endpoints
        }

        # Rate limiting
        self.request_timestamps: deque = deque(maxlen=max_requests_per_minute)

        # Client instances
        self._clients: Dict[str, AsyncClient] = {}

        logger.info(
            "Solana RPC connector initialized",
            primary_endpoint=primary_endpoint,
            secondary_endpoint=secondary_endpoint,
            endpoints_count=len(self.endpoints)
        )

    async def start(self):
        """Start the Solana RPC connector and initialize clients."""
        if not SOLANA_AVAILABLE:
            logger.warning("Solana libraries not available, using simulation mode")
            self._simulation_mode = True
        else:
            self._simulation_mode = False
            for endpoint in self.endpoints:
                try:
                    self._clients[endpoint] = AsyncClient(
                        endpoint,
                        commitment=self.commitment,
                        timeout=self.request_timeout
                    )
                    logger.debug("Solana client created", endpoint=endpoint)
                except Exception as e:
                    logger.error("Failed to create Solana client", endpoint=endpoint, error=str(e))

        logger.info("Solana RPC connector started", simulation_mode=getattr(self, '_simulation_mode', False))

    async def close(self):
        """Close the Solana RPC connector and cleanup resources."""
        for endpoint, client in self._clients.items():
            try:
                await client.close()
            except Exception as e:
                logger.warning("Error closing client", endpoint=endpoint, error=str(e))

        self._clients.clear()
        logger.info("Solana RPC connector closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_healthy_endpoints(self) -> List[str]:
        """Get list of healthy endpoints."""
        healthy = []
        for endpoint in self.endpoints:
            health = self.endpoint_health[endpoint]
            if health.status == SolanaConnectionStatus.CONNECTED:
                healthy.append(endpoint)
        return healthy

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if request can proceed, False if rate limited
        """
        current_time = time.time()

        # Remove old timestamps (older than 1 minute)
        while self.request_timestamps and current_time - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()

        # Check if we're at the limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            return False

        # Add current timestamp
        self.request_timestamps.append(current_time)
        return True

    async def _make_rpc_request(
        self,
        endpoint: str,
        method: str,
        params: List[Any]
    ) -> SolanaRPCResponse:
        """
        Make a Solana RPC request to a specific endpoint.

        Args:
            endpoint: RPC endpoint URL
            method: RPC method name
            params: Method parameters

        Returns:
            SolanaRPCResponse with success/failure and data
        """
        start_time = time.time()
        health = self.endpoint_health[endpoint]

        # If in simulation mode, return simulated data
        if getattr(self, '_simulation_mode', False):
            return self._simulate_rpc_request(method, params, endpoint, start_time)

        try:
            if not SOLANA_AVAILABLE:
                return self._simulate_rpc_request(method, params, endpoint, start_time)

            client = self._clients.get(endpoint)
            if not client:
                client = AsyncClient(endpoint, commitment=self.commitment)
                self._clients[endpoint] = client

            # Execute the RPC call
            result = None
            if method == "getSlot":
                response = await client.get_slot()
                result = response.value
            elif method == "getBalance":
                pubkey = Pubkey.from_string(params[0])
                response = await client.get_balance(pubkey)
                result = response.value
            elif method == "getAccountInfo":
                pubkey = Pubkey.from_string(params[0])
                response = await client.get_account_info(pubkey)
                result = response.value
            elif method == "getTokenAccountBalance":
                pubkey = Pubkey.from_string(params[0])
                response = await client.get_token_account_balance(pubkey)
                result = response.value
            elif method == "getSignaturesForAddress":
                pubkey = Pubkey.from_string(params[0])
                limit = params[1] if len(params) > 1 else 10
                response = await client.get_signatures_for_address(pubkey, limit=limit)
                result = response.value
            elif method == "getTransaction":
                response = await client.get_transaction(params[0])
                result = response.value
            elif method == "getRecentBlockhash":
                response = await client.get_latest_blockhash()
                result = response.value
            elif method == "sendTransaction":
                response = await client.send_transaction(params[0])
                result = response.value
            elif method == "getTokenSupply":
                pubkey = Pubkey.from_string(params[0])
                response = await client.get_token_supply(pubkey)
                result = response.value
            elif method == "getTokenLargestAccounts":
                pubkey = Pubkey.from_string(params[0])
                response = await client.get_token_largest_accounts(pubkey)
                result = response.value
            else:
                # Generic RPC call
                result = await client._provider.make_request(method, params)

            # Update health tracking
            response_time = time.time() - start_time
            health.status = SolanaConnectionStatus.CONNECTED
            health.consecutive_failures = 0
            health.last_successful_request = time.time()
            health.total_requests += 1
            health.response_times.append(response_time)
            health.response_time_avg = sum(health.response_times) / len(health.response_times)

            logger.debug(
                "Solana RPC request successful",
                endpoint=endpoint,
                method=method,
                response_time=response_time
            )

            return SolanaRPCResponse(
                success=True,
                data=result,
                endpoint_used=endpoint,
                response_time=response_time
            )

        except Exception as e:
            # Update health tracking
            response_time = time.time() - start_time
            health.consecutive_failures += 1
            health.failed_requests += 1
            health.total_requests += 1

            if health.consecutive_failures >= 3:
                health.status = SolanaConnectionStatus.FAILED
            else:
                health.status = SolanaConnectionStatus.DISCONNECTED

            logger.warning(
                "Solana RPC request failed",
                endpoint=endpoint,
                method=method,
                error=str(e),
                consecutive_failures=health.consecutive_failures
            )

            return SolanaRPCResponse(
                success=False,
                error=str(e),
                endpoint_used=endpoint,
                response_time=response_time
            )

    def _simulate_rpc_request(
        self,
        method: str,
        params: List[Any],
        endpoint: str,
        start_time: float
    ) -> SolanaRPCResponse:
        """Simulate an RPC request when Solana libraries are not available."""
        import random

        # Simulate data based on method
        result = None
        if method == "getSlot":
            result = 250000000 + random.randint(0, 10000)
        elif method == "getBalance":
            result = random.randint(0, 10000000000)  # In lamports
        elif method == "getAccountInfo":
            result = {"data": [], "executable": False, "lamports": random.randint(0, 10000000000)}
        elif method == "getTokenAccountBalance":
            result = {"amount": str(random.randint(0, 1000000000000)), "decimals": 9}
        elif method == "getSignaturesForAddress":
            result = []  # Empty list of signatures
        elif method == "getTransaction":
            result = None  # Transaction not found
        elif method == "getRecentBlockhash":
            result = {"blockhash": "simulated_blockhash_" + str(random.randint(1000, 9999))}
        elif method == "getTokenSupply":
            result = {"amount": str(random.randint(1000000000, 10000000000000)), "decimals": 9}
        elif method == "getTokenLargestAccounts":
            result = []  # Empty list
        else:
            result = {"simulated": True}

        response_time = time.time() - start_time

        return SolanaRPCResponse(
            success=True,
            data=result,
            endpoint_used=endpoint,
            response_time=response_time
        )

    async def make_request(
        self,
        method: str,
        params: List[Any],
        retry_count: int = 0
    ) -> SolanaRPCResponse:
        """
        Make a Solana RPC request with automatic failover.

        Args:
            method: RPC method name
            params: Method parameters
            retry_count: Current retry attempt

        Returns:
            SolanaRPCResponse with result or error
        """
        # Check rate limit
        if not self._check_rate_limit():
            return SolanaRPCResponse(
                success=False,
                error="Rate limit exceeded"
            )

        # Try each endpoint
        errors = []
        for endpoint in self.endpoints:
            response = await self._make_rpc_request(endpoint, method, params)

            if response.success:
                return response

            errors.append(f"{endpoint}: {response.error}")

        # All endpoints failed
        if retry_count < self.max_retries:
            # Wait before retrying
            await asyncio.sleep(2 ** retry_count)
            return await self.make_request(method, params, retry_count + 1)

        return SolanaRPCResponse(
            success=False,
            error=f"All endpoints failed after {self.max_retries} retries: {'; '.join(errors)}"
        )

    async def get_slot(self) -> SolanaRPCResponse:
        """Get the current slot."""
        return await self.make_request("getSlot", [])

    async def get_balance(self, address: str) -> SolanaRPCResponse:
        """Get the balance of an address in lamports."""
        return await self.make_request("getBalance", [address])

    async def get_account_info(self, address: str) -> SolanaRPCResponse:
        """Get account information."""
        return await self.make_request("getAccountInfo", [address])

    async def get_token_account_balance(self, token_account: str) -> SolanaRPCResponse:
        """Get token account balance."""
        return await self.make_request("getTokenAccountBalance", [token_account])

    async def get_signatures_for_address(self, address: str, limit: int = 10) -> SolanaRPCResponse:
        """Get recent signatures for an address."""
        return await self.make_request("getSignaturesForAddress", [address, limit])

    async def get_transaction(self, signature: str) -> SolanaRPCResponse:
        """Get transaction details."""
        return await self.make_request("getTransaction", [signature])

    async def get_recent_blockhash(self) -> SolanaRPCResponse:
        """Get the most recent blockhash."""
        return await self.make_request("getRecentBlockhash", [])

    async def send_transaction(self, transaction) -> SolanaRPCResponse:
        """Send a transaction."""
        return await self.make_request("sendTransaction", [transaction])

    async def get_token_supply(self, mint_address: str) -> SolanaRPCResponse:
        """Get token supply information."""
        return await self.make_request("getTokenSupply", [mint_address])

    async def get_token_largest_accounts(self, mint_address: str) -> SolanaRPCResponse:
        """Get largest token accounts for a mint."""
        return await self.make_request("getTokenLargestAccounts", [mint_address])

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all endpoints.

        Returns:
            Dictionary mapping endpoint URLs to health information
        """
        status = {}
        for endpoint, health in self.endpoint_health.items():
            status[endpoint] = {
                "status": health.status.value,
                "consecutive_failures": health.consecutive_failures,
                "response_time_avg": health.response_time_avg,
                "last_successful_request": health.last_successful_request,
                "total_requests": health.total_requests,
                "failed_requests": health.failed_requests
            }
        return status


# Global Solana RPC connector instance
_solana_rpc_connector: Optional[SolanaRPCConnector] = None


async def get_solana_rpc_connector() -> SolanaRPCConnector:
    """
    Get or create the global Solana RPC connector instance.

    Returns:
        SolanaRPCConnector instance
    """
    global _solana_rpc_connector

    if _solana_rpc_connector is None:
        # Get endpoints from environment
        primary_endpoint = os.getenv("SOLANARPCPRIMARY", "https://api.mainnet-beta.solana.com")
        secondary_endpoint = os.getenv("SOLANARPCFALLBACK", "https://solana-api.projectserum.com")

        _solana_rpc_connector = SolanaRPCConnector(
            primary_endpoint=primary_endpoint,
            secondary_endpoint=secondary_endpoint
        )

        await _solana_rpc_connector.start()
        logger.info("Global Solana RPC connector created")

    return _solana_rpc_connector
