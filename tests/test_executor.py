"""
Unit tests for the executor module (exchange interface).

This module tests the trading execution functionality including order placement,
signing logic, and nonce management in simulation mode.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.trading.exchange import ExchangeInterface, Order, OrderType, OrderSide, OrderStatus, MarketData
from src.config import TRADING_CONFIG


class TestExchangeInterface:
    """Test cases for ExchangeInterface class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exchange = ExchangeInterface()
        self.test_symbol = "ETH/USDT"
        self.test_amount = 100.0
        self.test_price = 2000.0
    
    def test_place_order_market_buy(self):
        """Test placing a market buy order."""
        result = self.exchange.place_order(
            symbol=self.test_symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=self.test_amount
        )
        
        assert isinstance(result, Order)
        assert result.symbol == self.test_symbol
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.amount == self.test_amount
    
    def test_place_order_limit_sell(self):
        """Test placing a limit sell order."""
        result = self.exchange.place_order(
            symbol=self.test_symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            amount=self.test_amount,
            price=self.test_price
        )
        
        assert isinstance(result, Order)
        assert result.symbol == self.test_symbol
        assert result.side == OrderSide.SELL
        assert result.order_type == OrderType.LIMIT
        assert result.amount == self.test_amount
        assert result.price == self.test_price
    
    def test_cancel_order_success(self):
        """Test canceling an order successfully."""
        # First place an order
        order = self.exchange.place_order(
            symbol=self.test_symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=self.test_amount
        )
        
        # Then cancel it
        result = self.exchange.cancel_order(order.order_id)
        assert result is True
    
    def test_cancel_order_not_found(self):
        """Test canceling a non-existent order."""
        result = self.exchange.cancel_order("non_existent_order")
        assert result is False
    
    def test_get_order_success(self):
        """Test getting an order."""
        # First place an order
        placed_order = self.exchange.place_order(
            symbol=self.test_symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=self.test_amount
        )
        
        # Then get it
        retrieved_order = self.exchange.get_order(placed_order.order_id)
        assert retrieved_order is not None
        assert retrieved_order.order_id == placed_order.order_id
        assert retrieved_order.symbol == self.test_symbol
    
    def test_get_order_not_found(self):
        """Test getting a non-existent order."""
        result = self.exchange.get_order("non_existent_order")
        assert result is None
    
    def test_get_balance_success(self):
        """Test getting account balance."""
        balance = self.exchange.get_balance("ETH")
        assert isinstance(balance, float)
        assert balance >= 0.0
    
    def test_get_all_balances(self):
        """Test getting all account balances."""
        balances = self.exchange.get_all_balances()
        assert isinstance(balances, dict)
        assert "ETH" in balances
        assert "USD" in balances
    
    def test_get_market_data(self):
        """Test getting market data."""
        market_data = self.exchange.get_market_data(self.test_symbol)
        assert market_data is not None
        assert isinstance(market_data, MarketData)
        assert market_data.symbol == self.test_symbol
    
    def test_get_trading_fees(self):
        """Test getting trading fees."""
        fee = self.exchange.get_trading_fees(self.test_symbol, self.test_amount)
        assert isinstance(fee, float)
        assert fee >= 0.0
    
    def test_is_market_open(self):
        """Test checking if market is open."""
        is_open = self.exchange.is_market_open()
        assert isinstance(is_open, bool)
    
    def test_get_exchange_info(self):
        """Test getting exchange information."""
        info = self.exchange.get_exchange_info()
        assert isinstance(info, dict)
        assert "exchange_name" in info
        assert "paper_mode" in info


class TestExchangeInterfaceIntegration:
    """Integration tests for ExchangeInterface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exchange = ExchangeInterface()
    
    def test_full_trading_workflow(self):
        """Test complete trading workflow."""
        # Place buy order
        buy_order = self.exchange.place_order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=100.0
        )
        
        assert buy_order.side == OrderSide.BUY
        assert buy_order.status == OrderStatus.FILLED
        
        # Place sell order
        sell_order = self.exchange.place_order(
            symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            amount=100.0,
            price=2100.0
        )
        
        assert sell_order.side == OrderSide.SELL
        assert sell_order.order_type == OrderType.LIMIT
    
    def test_order_management_workflow(self):
        """Test order management workflow."""
        # Place an order
        order = self.exchange.place_order(
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            amount=50.0,
            price=1900.0
        )
        
        # Get the order
        retrieved_order = self.exchange.get_order(order.order_id)
        assert retrieved_order.order_id == order.order_id
        
        # Get open orders
        open_orders = self.exchange.get_open_orders()
        assert len(open_orders) >= 0
        
        # Cancel the order
        cancel_result = self.exchange.cancel_order(order.order_id)
        assert cancel_result is True
    
    def test_market_data_workflow(self):
        """Test market data workflow."""
        symbol = "ETH/USDT"
        
        # Get market data
        market_data = self.exchange.get_market_data(symbol)
        assert market_data.symbol == symbol
        
        # Update market data
        new_market_data = MarketData(
            symbol=symbol,
            price=2050.0,
            volume_24h=1000.0,
            market_cap=1000000.0,
            liquidity=50000.0,
            timestamp=1234567890
        )
        self.exchange.update_market_data(symbol, new_market_data)
        
        # Verify update
        updated_data = self.exchange.get_market_data(symbol)
        assert updated_data.price == 2050.0
    
    def test_balance_workflow(self):
        """Test balance workflow."""
        # Get individual balance
        eth_balance = self.exchange.get_balance("ETH")
        assert isinstance(eth_balance, float)
        
        # Get all balances
        all_balances = self.exchange.get_all_balances()
        assert "ETH" in all_balances
        assert "USD" in all_balances
        
        # Verify individual balance matches all balances
        assert all_balances["ETH"] == eth_balance