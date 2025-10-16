"""
Exchange interface for the meme-coin trading bot.

This module provides a unified interface for interacting with various
cryptocurrency exchanges and DEXs with proper error handling and security.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

from src.utils.logger import log_trading_event, log_security_event

logger = structlog.get_logger(__name__)


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Order:
    """Order data structure."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    filled_price: Optional[float] = None
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()


@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    price: float
    volume_24h: float
    market_cap: float
    liquidity: float
    timestamp: float


class ExchangeInterface:
    """
    Unified exchange interface for trading operations.
    
    Features:
    - Order management
    - Market data retrieval
    - Balance management
    - Paper mode support
    - Security controls
    """
    
    def __init__(self, paper_mode: bool = True):
        """
        Initialize exchange interface.
        
        Args:
            paper_mode: Whether to run in paper mode
        """
        self.paper_mode = paper_mode
        self.orders: Dict[str, Order] = {}
        self.balances: Dict[str, float] = {}
        self.market_data: Dict[str, MarketData] = {}
        
        # Initialize paper mode balances
        if self.paper_mode:
            self.balances = {
                "USD": 10000.0,  # Starting balance
                "ETH": 5.0,      # Starting ETH balance
            }
        
        logger.info("Exchange interface initialized", paper_mode=paper_mode)
    
    def get_balance(self, symbol: str) -> float:
        """
        Get balance for a specific symbol.
        
        Args:
            symbol: Symbol to get balance for
            
        Returns:
            Balance amount
        """
        try:
            if self.paper_mode:
                return self.balances.get(symbol, 0.0)
            else:
                # TODO: Implement real exchange balance retrieval
                logger.warning("Real exchange balance retrieval not implemented")
                return 0.0
                
        except Exception as e:
            logger.error("Failed to get balance", symbol=symbol, error=str(e))
            return 0.0
    
    def get_all_balances(self) -> Dict[str, float]:
        """
        Get all balances.
        
        Returns:
            Dictionary of symbol -> balance
        """
        try:
            if self.paper_mode:
                return self.balances.copy()
            else:
                # TODO: Implement real exchange balance retrieval
                logger.warning("Real exchange balance retrieval not implemented")
                return {}
                
        except Exception as e:
            logger.error("Failed to get all balances", error=str(e))
            return {}
    
    def place_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                   amount: float, price: Optional[float] = None) -> Optional[Order]:
        """
        Place a new order.
        
        Args:
            symbol: Trading symbol
            side: Order side
            order_type: Order type
            amount: Order amount
            price: Order price (for limit orders)
            
        Returns:
            Order object if successful, None otherwise
        """
        try:
            # Generate order ID
            order_id = f"order_{int(time.time() * 1000)}"
            
            # Create order
            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price
            )
            
            if self.paper_mode:
                # Simulate order execution
                self._simulate_order_execution(order)
            else:
                # TODO: Implement real exchange order placement
                logger.warning("Real exchange order placement not implemented")
                order.status = OrderStatus.FAILED
                return None
            
            # Store order
            self.orders[order_id] = order
            
            log_trading_event(
                "order_placed",
                {
                    "order_id": order_id,
                    "symbol": symbol,
                    "side": side.value,
                    "order_type": order_type.value,
                    "amount": amount,
                    "price": price,
                    "paper_mode": self.paper_mode
                },
                "INFO"
            )
            
            return order
            
        except Exception as e:
            logger.error("Failed to place order", symbol=symbol, side=side.value, error=str(e))
            log_security_event(
                "order_placement_failed",
                {
                    "symbol": symbol,
                    "side": side.value,
                    "order_type": order_type.value,
                    "amount": amount,
                    "price": price,
                    "error": str(e)
                },
                "ERROR"
            )
            return None
    
    def _simulate_order_execution(self, order: Order):
        """Simulate order execution in paper mode."""
        try:
            # Get current market price (simplified)
            current_price = self._get_simulated_price(order.symbol)
            
            if order.order_type == OrderType.MARKET:
                # Market order executes immediately
                order.filled_amount = order.amount
                order.filled_price = current_price
                order.status = OrderStatus.FILLED
                
                # Update balances
                if order.side == OrderSide.BUY:
                    cost = order.amount * current_price
                    if self.balances.get("USD", 0) >= cost:
                        self.balances["USD"] -= cost
                        self.balances[order.symbol] = self.balances.get(order.symbol, 0) + order.amount
                    else:
                        order.status = OrderStatus.FAILED
                else:  # SELL
                    if self.balances.get(order.symbol, 0) >= order.amount:
                        self.balances[order.symbol] -= order.amount
                        self.balances["USD"] += order.amount * current_price
                    else:
                        order.status = OrderStatus.FAILED
            
            elif order.order_type == OrderType.LIMIT:
                # Limit order - check if price is met
                if order.side == OrderSide.BUY and current_price <= order.price:
                    order.filled_amount = order.amount
                    order.filled_price = order.price
                    order.status = OrderStatus.FILLED
                    
                    # Update balances
                    cost = order.amount * order.price
                    if self.balances.get("USD", 0) >= cost:
                        self.balances["USD"] -= cost
                        self.balances[order.symbol] = self.balances.get(order.symbol, 0) + order.amount
                    else:
                        order.status = OrderStatus.FAILED
                elif order.side == OrderSide.SELL and current_price >= order.price:
                    order.filled_amount = order.amount
                    order.filled_price = order.price
                    order.status = OrderStatus.FILLED
                    
                    # Update balances
                    if self.balances.get(order.symbol, 0) >= order.amount:
                        self.balances[order.symbol] -= order.amount
                        self.balances["USD"] += order.amount * order.price
                    else:
                        order.status = OrderStatus.FAILED
                else:
                    # Price not met, keep as pending
                    order.status = OrderStatus.PENDING
            
            order.updated_at = time.time()
            
        except Exception as e:
            logger.error("Failed to simulate order execution", order_id=order.order_id, error=str(e))
            order.status = OrderStatus.FAILED
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for a symbol."""
        # Simple price simulation (in production, use real market data)
        base_prices = {
            "ETH": 2000.0,
            "BTC": 30000.0,
            "DOGE": 0.08,
            "SHIB": 0.00001,
        }
        
        base_price = base_prices.get(symbol, 1.0)
        
        # Add some random variation
        import random
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        
        return base_price * (1 + variation)
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if order cancelled successfully, False otherwise
        """
        try:
            if order_id not in self.orders:
                logger.warning("Order not found", order_id=order_id)
                return False
            
            order = self.orders[order_id]
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED]:
                logger.warning("Cannot cancel order", order_id=order_id, status=order.status.value)
                return False
            
            order.status = OrderStatus.CANCELLED
            order.updated_at = time.time()
            
            log_trading_event(
                "order_cancelled",
                {
                    "order_id": order_id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "amount": order.amount,
                    "paper_mode": self.paper_mode
                },
                "INFO"
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to cancel order", order_id=order_id, error=str(e))
            return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object if found, None otherwise
        """
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """
        Get all open orders.
        
        Returns:
            List of open orders
        """
        return [order for order in self.orders.values() 
                if order.status == OrderStatus.PENDING]
    
    def get_order_history(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get order history.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of orders
        """
        orders = list(self.orders.values())
        
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        # Sort by creation time (newest first)
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: Symbol to get market data for
            
        Returns:
            Market data object if available, None otherwise
        """
        try:
            if self.paper_mode:
                # Return simulated market data
                return MarketData(
                    symbol=symbol,
                    price=self._get_simulated_price(symbol),
                    volume_24h=1000000.0,  # Simulated volume
                    market_cap=10000000.0,  # Simulated market cap
                    liquidity=500000.0,  # Simulated liquidity
                    timestamp=time.time()
                )
            else:
                # TODO: Implement real market data retrieval
                logger.warning("Real market data retrieval not implemented")
                return None
                
        except Exception as e:
            logger.error("Failed to get market data", symbol=symbol, error=str(e))
            return None
    
    def update_market_data(self, symbol: str, market_data: MarketData):
        """
        Update market data for a symbol.
        
        Args:
            symbol: Symbol to update
            market_data: New market data
        """
        try:
            self.market_data[symbol] = market_data
            
        except Exception as e:
            logger.error("Failed to update market data", symbol=symbol, error=str(e))
    
    def get_trading_fees(self, symbol: str, amount: float) -> float:
        """
        Get trading fees for a transaction.
        
        Args:
            symbol: Trading symbol
            amount: Transaction amount
            
        Returns:
            Trading fee amount
        """
        try:
            # Simple fee calculation (0.3% of transaction value)
            fee_rate = 0.003
            return amount * fee_rate
            
        except Exception as e:
            logger.error("Failed to calculate trading fees", symbol=symbol, amount=amount, error=str(e))
            return 0.0
    
    def is_market_open(self) -> bool:
        """
        Check if the market is open.
        
        Returns:
            True if market is open, False otherwise
        """
        try:
            # Crypto markets are always open
            return True
            
        except Exception as e:
            logger.error("Failed to check market status", error=str(e))
            return False
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information.
        
        Returns:
            Dictionary with exchange information
        """
        try:
            return {
                "exchange_name": "Paper Exchange" if self.paper_mode else "Real Exchange",
                "paper_mode": self.paper_mode,
                "supported_symbols": ["ETH", "BTC", "DOGE", "SHIB"],
                "trading_fees": 0.003,  # 0.3%
                "min_order_size": 10.0,  # $10 minimum
                "max_order_size": 100000.0,  # $100k maximum
                "order_count": len(self.orders),
                "balance_count": len(self.balances),
                "market_data_count": len(self.market_data)
            }
            
        except Exception as e:
            logger.error("Failed to get exchange info", error=str(e))
            return {"error": str(e)}


# Global exchange interface instance
_exchange_interface: Optional[ExchangeInterface] = None


def get_exchange_interface(paper_mode: bool = True) -> ExchangeInterface:
    """
    Get the global exchange interface instance.
    
    Args:
        paper_mode: Whether to run in paper mode
        
    Returns:
        Exchange interface instance
    """
    global _exchange_interface
    
    if _exchange_interface is None:
        _exchange_interface = ExchangeInterface(paper_mode)
    
    return _exchange_interface
