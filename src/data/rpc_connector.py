"""
Ethereum RPC connector with failover and health monitoring.

Provides reliable connection to Ethereum nodes with automatic failover,
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
from web3 import Web3
from web3.providers import HTTPProvider

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionStatus(Enum):
    """Connection status for RPC endpoints."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class EndpointHealth:
    """Health tracking for an RPC endpoint."""
    status: ConnectionStatus = ConnectionStatus.UNKNOWN
    consecutive_failures: int = 0
    response_time_avg: float = 0.0
    last_successful_request: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class RPCResponse:
    """Response from an RPC request."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    endpoint_used: Optional[str] = None
    response_time: Optional[float] = None


class RPCConnector:
    """
    Ethereum RPC connector with failover and health monitoring.

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
        max_retries: int = 3
    ):
        """
        Initialize the RPC connector.

        Args:
            primary_endpoint: Primary RPC endpoint URL
            secondary_endpoint: Optional secondary endpoint for failover
            max_requests_per_minute: Rate limit for requests
            request_timeout: Timeout for individual requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.primary_endpoint = primary_endpoint
        self.secondary_endpoint = secondary_endpoint
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        # Build endpoint list
        self.endpoints: List[str] = [primary_endpoint]
        if secondary_endpoint:
            self.endpoints.append(secondary_endpoint)

        # Health tracking
        self.endpoint_health: Dict[str, EndpointHealth] = {
            endpoint: EndpointHealth() for endpoint in self.endpoints
        }

        # Rate limiting
        self.request_timestamps: deque = deque(maxlen=max_requests_per_minute)

        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self._web3_instances: Dict[str, Web3] = {}

        logger.info(
            "RPC connector initialized",
            primary_endpoint=primary_endpoint,
            secondary_endpoint=secondary_endpoint,
            endpoints_count=len(self.endpoints)
        )

    async def start(self):
        """Start the RPC connector and initialize session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            )

        # Initialize Web3 instances for each endpoint
        for endpoint in self.endpoints:
            try:
                self._web3_instances[endpoint] = Web3(HTTPProvider(endpoint))
                logger.debug("Web3 instance created", endpoint=endpoint)
            except Exception as e:
                logger.error("Failed to create Web3 instance", endpoint=endpoint, error=str(e))

        logger.info("RPC connector started")

    async def close(self):
        """Close the RPC connector and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None

        self._web3_instances.clear()
        logger.info("RPC connector closed")

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
            if health.status == ConnectionStatus.CONNECTED:
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
    ) -> RPCResponse:
        """
        Make an RPC request to a specific endpoint.

        Args:
            endpoint: RPC endpoint URL
            method: RPC method name
            params: Method parameters

        Returns:
            RPCResponse with success/failure and data
        """
        start_time = time.time()
        health = self.endpoint_health[endpoint]

        try:
            web3 = self._web3_instances.get(endpoint)
            if not web3:
                web3 = Web3(HTTPProvider(endpoint))
                self._web3_instances[endpoint] = web3

            # Execute the RPC call
            result = None
            if method == "eth_blockNumber":
                result = web3.eth.block_number
            elif method == "eth_getBalance":
                result = web3.eth.get_balance(params[0], params[1] if len(params) > 1 else "latest")
            elif method == "eth_getTransactionCount":
                result = web3.eth.get_transaction_count(params[0], params[1] if len(params) > 1 else "latest")
            elif method == "eth_sendRawTransaction":
                result = web3.eth.send_raw_transaction(params[0]).hex()
            elif method == "eth_getTransactionReceipt":
                result = dict(web3.eth.get_transaction_receipt(params[0]))
            elif method == "eth_call":
                result = web3.eth.call(params[0], params[1] if len(params) > 1 else "latest")
            elif method == "eth_getCode":
                result = web3.eth.get_code(params[0], params[1] if len(params) > 1 else "latest").hex()
            elif method == "eth_gasPrice":
                result = web3.eth.gas_price
            else:
                # Generic RPC call
                result = web3.provider.make_request(method, params)

            # Update health tracking
            response_time = time.time() - start_time
            health.status = ConnectionStatus.CONNECTED
            health.consecutive_failures = 0
            health.last_successful_request = time.time()
            health.total_requests += 1
            health.response_times.append(response_time)
            health.response_time_avg = sum(health.response_times) / len(health.response_times)

            logger.debug(
                "RPC request successful",
                endpoint=endpoint,
                method=method,
                response_time=response_time
            )

            return RPCResponse(
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
                health.status = ConnectionStatus.FAILED
            else:
                health.status = ConnectionStatus.DISCONNECTED

            logger.warning(
                "RPC request failed",
                endpoint=endpoint,
                method=method,
                error=str(e),
                consecutive_failures=health.consecutive_failures
            )

            return RPCResponse(
                success=False,
                error=str(e),
                endpoint_used=endpoint,
                response_time=response_time
            )

    async def make_request(
        self,
        method: str,
        params: List[Any],
        retry_count: int = 0
    ) -> RPCResponse:
        """
        Make an RPC request with automatic failover.

        Args:
            method: RPC method name
            params: Method parameters
            retry_count: Current retry attempt

        Returns:
            RPCResponse with result or error
        """
        # Check rate limit
        if not self._check_rate_limit():
            return RPCResponse(
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

        return RPCResponse(
            success=False,
            error=f"All endpoints failed after {self.max_retries} retries: {'; '.join(errors)}"
        )

    async def get_block_number(self) -> RPCResponse:
        """Get the current block number."""
        return await self.make_request("eth_blockNumber", [])

    async def get_balance(self, address: str, block: str = "latest") -> RPCResponse:
        """Get the balance of an address."""
        return await self.make_request("eth_getBalance", [address, block])

    async def get_transaction_count(self, address: str, block: str = "latest") -> RPCResponse:
        """Get the transaction count (nonce) for an address."""
        return await self.make_request("eth_getTransactionCount", [address, block])

    async def send_raw_transaction(self, signed_tx: str) -> RPCResponse:
        """Send a signed transaction."""
        return await self.make_request("eth_sendRawTransaction", [signed_tx])

    async def get_transaction_receipt(self, tx_hash: str) -> RPCResponse:
        """Get the receipt of a transaction."""
        return await self.make_request("eth_getTransactionReceipt", [tx_hash])

    async def get_code(self, address: str, block: str = "latest") -> RPCResponse:
        """Get the code at an address."""
        return await self.make_request("eth_getCode", [address, block])

    async def call(self, transaction: Dict[str, Any], block: str = "latest") -> RPCResponse:
        """Execute a call without creating a transaction."""
        return await self.make_request("eth_call", [transaction, block])

    async def get_gas_price(self) -> RPCResponse:
        """Get the current gas price."""
        return await self.make_request("eth_gasPrice", [])

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


# Global RPC connector instance
_rpc_connector: Optional[RPCConnector] = None


def get_rpc_connector() -> RPCConnector:
    """
    Get or create the global RPC connector instance.

    Returns:
        RPCConnector instance
    """
    global _rpc_connector

    if _rpc_connector is None:
        # Get endpoints from environment
        primary_endpoint = os.getenv("ETHRPCPRIMARY", "https://cloudflare-eth.com")
        secondary_endpoint = os.getenv("ETHRPCFALLBACK", "https://rpc.ankr.com/eth")

        _rpc_connector = RPCConnector(
            primary_endpoint=primary_endpoint,
            secondary_endpoint=secondary_endpoint
        )

        logger.info("Global RPC connector created")

    return _rpc_connector
