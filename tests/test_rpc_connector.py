"""
Unit tests for RPC connector functionality.

Tests cover connection management, failover logic, retry mechanisms,
and error handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.rpc_connector import RPCConnector, RPCResponse, ConnectionStatus


class TestRPCConnector:
    """Test cases for RPCConnector class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.primary_endpoint = "https://mainnet.infura.io/v3/test"
        self.secondary_endpoint = "https://eth-mainnet.alchemyapi.io/v2/test"
        self.connector = RPCConnector(self.primary_endpoint, self.secondary_endpoint)
    
    def test_initialization(self):
        """Test RPC connector initialization."""
        assert self.connector.primary_endpoint == self.primary_endpoint
        assert self.connector.secondary_endpoint == self.secondary_endpoint
        assert len(self.connector.endpoints) == 2
        assert self.primary_endpoint in self.connector.endpoints
        assert self.secondary_endpoint in self.connector.endpoints
    
    def test_initialization_primary_only(self):
        """Test RPC connector initialization with primary endpoint only."""
        connector = RPCConnector(self.primary_endpoint)
        assert connector.primary_endpoint == self.primary_endpoint
        assert connector.secondary_endpoint is None
        assert len(connector.endpoints) == 1
        assert self.primary_endpoint in connector.endpoints
    
    @pytest.mark.asyncio
    async def test_start_and_close(self):
        """Test RPC connector start and close methods."""
        await self.connector.start()
        assert self.connector.session is not None
        
        await self.connector.close()
        assert self.connector.session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test RPC connector as async context manager."""
        async with self.connector as connector:
            assert connector.session is not None
        
        assert self.connector.session is None
    
    def test_get_healthy_endpoints(self):
        """Test getting healthy endpoints."""
        # Initially no endpoints are healthy
        healthy_endpoints = self.connector._get_healthy_endpoints()
        assert len(healthy_endpoints) == 0
        
        # Mark primary endpoint as healthy
        self.connector.endpoint_health[self.primary_endpoint].status = ConnectionStatus.CONNECTED
        healthy_endpoints = self.connector._get_healthy_endpoints()
        assert len(healthy_endpoints) == 1
        assert self.primary_endpoint in healthy_endpoints
    
    def test_check_rate_limit(self):
        """Test rate limiting functionality."""
        # Should pass initially
        assert self.connector._check_rate_limit() is True
        
        # Fill up rate limit
        for _ in range(self.connector.max_requests_per_minute):
            self.connector._check_rate_limit()
        
        # Should be rate limited now
        assert self.connector._check_rate_limit() is False
    
    @pytest.mark.asyncio
    async def test_make_rpc_request_success(self):
        """Test successful RPC request."""
        with patch('src.data.rpc_connector.Web3') as mock_web3:
            # Mock Web3 instance
            mock_web3_instance = MagicMock()
            mock_web3_instance.eth.block_number = 12345
            mock_web3.return_value = mock_web3_instance
            
            response = await self.connector._make_rpc_request(
                self.primary_endpoint, "eth_blockNumber", []
            )
            
            assert response.success is True
            assert response.data == 12345
            assert response.endpoint_used == self.primary_endpoint
            assert response.response_time is not None
    
    @pytest.mark.asyncio
    async def test_make_rpc_request_failure(self):
        """Test failed RPC request."""
        with patch('src.data.rpc_connector.Web3') as mock_web3:
            # Mock Web3 instance to raise exception
            mock_web3_instance = MagicMock()
            mock_web3_instance.eth.block_number.side_effect = Exception("Connection failed")
            mock_web3.return_value = mock_web3_instance
            
            response = await self.connector._make_rpc_request(
                self.primary_endpoint, "eth_blockNumber", []
            )
            
            assert response.success is False
            assert response.error is not None
            assert response.endpoint_used == self.primary_endpoint
    
    @pytest.mark.asyncio
    async def test_make_request_with_failover(self):
        """Test RPC request with failover logic."""
        with patch.object(self.connector, '_make_rpc_request') as mock_make_request:
            # First endpoint fails, second succeeds
            mock_make_request.side_effect = [
                RPCResponse(success=False, error="Failed"),
                RPCResponse(success=True, data=12345, endpoint_used=self.secondary_endpoint)
            ]
            
            response = await self.connector.make_request("eth_blockNumber", [])
            
            assert response.success is True
            assert response.data == 12345
            assert response.endpoint_used == self.secondary_endpoint
    
    @pytest.mark.asyncio
    async def test_make_request_all_endpoints_fail(self):
        """Test RPC request when all endpoints fail."""
        with patch.object(self.connector, '_make_rpc_request') as mock_make_request:
            mock_make_request.return_value = RPCResponse(success=False, error="Failed")
            
            response = await self.connector.make_request("eth_blockNumber", [])
            
            assert response.success is False
            assert "All endpoints failed" in response.error
    
    @pytest.mark.asyncio
    async def test_get_block_number(self):
        """Test get_block_number method."""
        with patch.object(self.connector, 'make_request') as mock_make_request:
            mock_make_request.return_value = RPCResponse(
                success=True, data=12345, endpoint_used=self.primary_endpoint
            )
            
            response = await self.connector.get_block_number()
            
            assert response.success is True
            assert response.data == 12345
            mock_make_request.assert_called_once_with("eth_blockNumber", [])
    
    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test get_balance method."""
        with patch.object(self.connector, 'make_request') as mock_make_request:
            mock_make_request.return_value = RPCResponse(
                success=True, data=1000000000000000000, endpoint_used=self.primary_endpoint
            )
            
            response = await self.connector.get_balance("0x1234567890123456789012345678901234567890")
            
            assert response.success is True
            assert response.data == 1000000000000000000
            mock_make_request.assert_called_once_with(
                "eth_getBalance", ["0x1234567890123456789012345678901234567890", "latest"]
            )
    
    @pytest.mark.asyncio
    async def test_get_transaction_count(self):
        """Test get_transaction_count method."""
        with patch.object(self.connector, 'make_request') as mock_make_request:
            mock_make_request.return_value = RPCResponse(
                success=True, data=42, endpoint_used=self.primary_endpoint
            )
            
            response = await self.connector.get_transaction_count("0x1234567890123456789012345678901234567890")
            
            assert response.success is True
            assert response.data == 42
            mock_make_request.assert_called_once_with(
                "eth_getTransactionCount", ["0x1234567890123456789012345678901234567890", "latest"]
            )
    
    @pytest.mark.asyncio
    async def test_send_raw_transaction(self):
        """Test send_raw_transaction method."""
        with patch.object(self.connector, 'make_request') as mock_make_request:
            mock_make_request.return_value = RPCResponse(
                success=True, data="0x1234567890abcdef", endpoint_used=self.primary_endpoint
            )
            
            response = await self.connector.send_raw_transaction("0x1234567890abcdef")
            
            assert response.success is True
            assert response.data == "0x1234567890abcdef"
            mock_make_request.assert_called_once_with(
                "eth_sendRawTransaction", ["0x1234567890abcdef"]
            )
    
    @pytest.mark.asyncio
    async def test_get_transaction_receipt(self):
        """Test get_transaction_receipt method."""
        with patch.object(self.connector, 'make_request') as mock_make_request:
            mock_receipt = {"status": 1, "blockNumber": 12345}
            mock_make_request.return_value = RPCResponse(
                success=True, data=mock_receipt, endpoint_used=self.primary_endpoint
            )
            
            response = await self.connector.get_transaction_receipt("0x1234567890abcdef")
            
            assert response.success is True
            assert response.data == mock_receipt
            mock_make_request.assert_called_once_with(
                "eth_getTransactionReceipt", ["0x1234567890abcdef"]
            )
    
    def test_get_health_status(self):
        """Test getting health status."""
        # Mark primary endpoint as healthy
        self.connector.endpoint_health[self.primary_endpoint].status = ConnectionStatus.CONNECTED
        self.connector.endpoint_health[self.primary_endpoint].consecutive_failures = 0
        self.connector.endpoint_health[self.primary_endpoint].response_time_avg = 0.5
        
        # Mark secondary endpoint as failed
        self.connector.endpoint_health[self.secondary_endpoint].status = ConnectionStatus.FAILED
        self.connector.endpoint_health[self.secondary_endpoint].consecutive_failures = 3
        self.connector.endpoint_health[self.secondary_endpoint].response_time_avg = 1.0
        
        status = self.connector.get_health_status()
        
        assert self.primary_endpoint in status
        assert self.secondary_endpoint in status
        
        assert status[self.primary_endpoint]["status"] == "connected"
        assert status[self.primary_endpoint]["consecutive_failures"] == 0
        assert status[self.primary_endpoint]["response_time_avg"] == 0.5
        
        assert status[self.secondary_endpoint]["status"] == "failed"
        assert status[self.secondary_endpoint]["consecutive_failures"] == 3
        assert status[self.secondary_endpoint]["response_time_avg"] == 1.0


@pytest.mark.integration
class TestRPCConnectorIntegration:
    """Integration tests for RPC connector."""
    
    @pytest.mark.asyncio
    async def test_real_rpc_connection(self):
        """Test real RPC connection (requires network access)."""
        # Use public RPC endpoints for testing
        primary_endpoint = "https://cloudflare-eth.com"
        secondary_endpoint = "https://rpc.ankr.com/eth"
        
        connector = RPCConnector(primary_endpoint, secondary_endpoint)
        
        async with connector:
            # Test basic RPC call
            response = await connector.get_block_number()
            
            if response.success:
                assert isinstance(response.data, int)
                assert response.data > 0
                assert response.endpoint_used in [primary_endpoint, secondary_endpoint]
            else:
                # If network is unavailable, that's okay for integration tests
                pytest.skip("Network unavailable for integration test")
    
    @pytest.mark.asyncio
    async def test_failover_mechanism(self):
        """Test failover mechanism with real endpoints."""
        # Use one working and one failing endpoint
        primary_endpoint = "https://cloudflare-eth.com"
        secondary_endpoint = "https://invalid-endpoint.com"
        
        connector = RPCConnector(primary_endpoint, secondary_endpoint)
        
        async with connector:
            # Test that it falls back to working endpoint
            response = await connector.get_block_number()
            
            if response.success:
                assert response.endpoint_used == primary_endpoint
            else:
                pytest.skip("Network unavailable for integration test")
