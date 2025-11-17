"""
Data layer for the meme-coin trading bot.

This module provides RPC connectivity, market data fetching,
and data aggregation for both EVM and Solana chains.
"""

from .rpc_connector import RPCConnector, RPCResponse, ConnectionStatus, get_rpc_connector
from .solana_rpc_connector import SolanaRPCConnector, get_solana_rpc_connector
from .market_watcher import EVMMarketWatcher, get_evm_market_watcher
from .solana_market_watcher import SolanaMarketWatcher, get_solana_market_watcher
from .live_market_fetcher import fetch_market_data_sync, LiveMarketFetcher

__all__ = [
    "RPCConnector",
    "RPCResponse",
    "ConnectionStatus",
    "get_rpc_connector",
    "SolanaRPCConnector",
    "get_solana_rpc_connector",
    "EVMMarketWatcher",
    "get_evm_market_watcher",
    "SolanaMarketWatcher",
    "get_solana_market_watcher",
    "fetch_market_data_sync",
    "LiveMarketFetcher",
]
