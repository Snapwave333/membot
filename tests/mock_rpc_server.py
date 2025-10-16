#!/usr/bin/env python3
"""
Mock RPC server for integration testing.

This server simulates Ethereum RPC endpoints and websocket connections
to provide realistic test data for the bot.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class MockToken:
    """Mock token data."""
    address: str
    symbol: str
    name: str
    decimals: int
    total_supply: int
    price_usd: float
    liquidity: float
    market_cap: float
    volume_24h: float
    created_at: float

class MockRPCServer:
    """Mock RPC server for testing."""
    
    def __init__(self, port: int = 8545):
        self.port = port
        self.tokens: Dict[str, MockToken] = {}
        self.pending_transactions: List[Dict[str, Any]] = []
        self.block_number = 18000000
        self.websocket_clients = set()
        
        # Initialize with some test tokens
        self._init_test_tokens()
        
    def _init_test_tokens(self):
        """Initialize with test tokens."""
        current_time = time.time()
        
        # Test token 1: Safe token
        self.tokens["0x1234567890123456789012345678901234567890"] = MockToken(
            address="0x1234567890123456789012345678901234567890",
            symbol="SAFE",
            name="Safe Token",
            decimals=18,
            total_supply=1000000000 * 10**18,
            price_usd=0.001,
            liquidity=50000.0,
            market_cap=1000000.0,
            volume_24h=10000.0,
            created_at=current_time - 3600  # 1 hour ago
        )
        
        # Test token 2: Risky token
        self.tokens["0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"] = MockToken(
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            symbol="RISK",
            name="Risky Token",
            decimals=18,
            total_supply=1000000 * 10**18,
            price_usd=0.0001,
            liquidity=1000.0,
            market_cap=100000.0,
            volume_24h=500.0,
            created_at=current_time - 1800  # 30 minutes ago
        )
    
    async def handle_eth_call(self, method: str, params: List[Any]) -> Dict[str, Any]:
        """Handle eth_call requests."""
        if method == "eth_getBalance":
            return {"result": "0x1bc16d674ec80000"}  # 2 ETH in wei
        
        elif method == "eth_blockNumber":
            self.block_number += 1
            return {"result": hex(self.block_number)}
        
        elif method == "eth_getCode":
            address = params[0]
            if address in self.tokens:
                # Return mock contract code
                return {"result": "0x608060405234801561001057600080fd5b50"}
            return {"result": "0x"}
        
        elif method == "eth_call":
            # Mock contract calls
            data = params[0].get("data", "")
            if data.startswith("0x70a08231"):  # balanceOf
                return {"result": "0x0000000000000000000000000000000000000000000000000000000000000000"}
            elif data.startswith("0x18160ddd"):  # totalSupply
                token_addr = params[0]["to"]
                if token_addr in self.tokens:
                    supply = self.tokens[token_addr].total_supply
                    return {"result": hex(supply)}
            return {"result": "0x0000000000000000000000000000000000000000000000000000000000000000"}
        
        return {"error": {"code": -32601, "message": "Method not found"}}
    
    async def handle_websocket_message(self, websocket, message: str):
        """Handle websocket messages."""
        try:
            data = json.loads(message)
            method = data.get("method")
            
            if method == "eth_subscribe":
                # Subscribe to new blocks
                subscription_id = f"0x{hash(str(time.time())):x}"
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": subscription_id
                }))
                
                # Start sending mock events
                asyncio.create_task(self._send_mock_events(websocket, subscription_id))
            
        except Exception as e:
            logger.error("Websocket error", error=str(e))
    
    async def _send_mock_events(self, websocket, subscription_id: str):
        """Send mock events to websocket clients."""
        try:
            while True:
                await asyncio.sleep(5)  # Send event every 5 seconds
                
                # Simulate new token listing
                if len(self.tokens) < 5:
                    new_token = self._create_mock_token()
                    self.tokens[new_token.address] = new_token
                    
                    # Send new token event
                    event = {
                        "jsonrpc": "2.0",
                        "method": "eth_subscription",
                        "params": {
                            "subscription": subscription_id,
                            "result": {
                                "address": new_token.address,
                                "topics": ["0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"],  # Transfer event
                                "data": "0x0000000000000000000000000000000000000000000000000000000000000000",
                                "blockNumber": hex(self.block_number),
                                "transactionHash": f"0x{hash(str(time.time())):x}",
                                "transactionIndex": "0x0",
                                "blockHash": f"0x{hash(str(self.block_number)):x}",
                                "logIndex": "0x0",
                                "removed": False
                            }
                        }
                    }
                    
                    await websocket.send(json.dumps(event))
                
                # Simulate price updates
                for token in self.tokens.values():
                    # Random price movement
                    price_change = (hash(str(time.time())) % 100 - 50) / 10000
                    token.price_usd = max(0.0001, token.price_usd + price_change)
                    token.market_cap = token.price_usd * (token.total_supply / 10**18)
                
        except Exception as e:
            logger.error("Error sending mock events", error=str(e))
    
    def _create_mock_token(self) -> MockToken:
        """Create a new mock token."""
        current_time = time.time()
        token_id = len(self.tokens) + 1
        
        return MockToken(
            address=f"0x{hash(str(current_time + token_id)):040x}",
            symbol=f"TEST{token_id}",
            name=f"Test Token {token_id}",
            decimals=18,
            total_supply=1000000 * 10**18,
            price_usd=0.001 + (hash(str(token_id)) % 100) / 100000,
            liquidity=10000.0 + (hash(str(token_id)) % 50000),
            market_cap=100000.0 + (hash(str(token_id)) % 900000),
            volume_24h=1000.0 + (hash(str(token_id)) % 10000),
            created_at=current_time
        )
    
    async def start_server(self):
        """Start the mock RPC server."""
        logger.info("Starting mock RPC server", port=self.port)
        
        # Start HTTP server
        async def handle_request(reader, writer):
            try:
                data = await reader.read(1024)
                request = json.loads(data.decode())
                
                method = request.get("method")
                params = request.get("params", [])
                
                response = await self.handle_eth_call(method, params)
                
                writer.write(json.dumps(response).encode())
                await writer.drain()
                
            except Exception as e:
                logger.error("Request error", error=str(e))
            finally:
                writer.close()
        
        # Start WebSocket server
        async def handle_websocket(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info("WebSocket client connected", client_count=len(self.websocket_clients))
            
            try:
                async for message in websocket:
                    await self.handle_websocket_message(websocket, message)
            except Exception as e:
                logger.error("WebSocket error", error=str(e))
            finally:
                self.websocket_clients.remove(websocket)
                logger.info("WebSocket client disconnected", client_count=len(self.websocket_clients))
        
        # Start servers
        http_server = await asyncio.start_server(handle_request, "localhost", self.port)
        ws_server = await asyncio.start_server(handle_websocket, "localhost", self.port + 1)
        
        logger.info("Mock RPC server started", http_port=self.port, ws_port=self.port + 1)
        
        # Keep running
        await asyncio.gather(http_server.serve_forever(), ws_server.serve_forever())

async def main():
    """Main function."""
    server = MockRPCServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())
