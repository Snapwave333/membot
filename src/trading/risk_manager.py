"""
Risk management system for the meme-coin trading bot.

This module provides comprehensive risk management with:
- Position sizing and limits
- Stop-loss and take-profit management
- Portfolio risk monitoring
- Emergency controls and kill-switch
- Real-time risk assessment
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config import TRADING_CONFIG, SAFETY_CONFIG
from src.utils.logger import log_security_event, log_trading_event

logger = structlog.get_logger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PositionStatus(Enum):
    """Position status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"
    PENDING = "pending"


@dataclass
class Position:
    """Position data structure."""
    symbol: str
    side: str  # 'long' or 'short'
    amount: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    status: PositionStatus = PositionStatus.OPEN
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()


@dataclass
class RiskMetrics:
    """Risk metrics data structure."""
    portfolio_value: float
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    position_count: int
    risk_level: RiskLevel
    kill_switch_active: bool
    last_updated: float


class RiskManager:
    """
    Comprehensive risk management system.
    
    Features:
    - Position sizing and limits
    - Stop-loss and take-profit management
    - Portfolio risk monitoring
    - Emergency controls and kill-switch
    - Real-time risk assessment
    """
    
    def __init__(self):
        """Initialize risk manager."""
        self.positions: Dict[str, Position] = {}
        self.portfolio_value: float = 0.0
        self.daily_pnl: float = 0.0
        self.max_drawdown: float = 0.0
        self.kill_switch_active: bool = False
        self.last_risk_check: float = 0.0
        
        # Risk limits from configuration
        self.daily_max_loss_percent = TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT
        self.profit_sweep_threshold = TRADING_CONFIG.PROFIT_SWEEP_THRESHOLD
        self.per_trade_pct = TRADING_CONFIG.PER_TRADE_PCT
        self.max_concurrent_positions = TRADING_CONFIG.MAX_CONCURRENT_POSITIONS
        self.profit_target_pct = TRADING_CONFIG.PROFIT_TARGET_PCT
        self.hard_stop_pct = TRADING_CONFIG.HARD_STOP_PCT
        
        # Safety limits
        self.emergency_stop_loss_pct = SAFETY_CONFIG.EMERGENCY_STOP_LOSS_PCT
        self.max_drawdown_pct = SAFETY_CONFIG.MAX_DRAWDOWN_PCT
        self.emergency_liquidation_threshold = SAFETY_CONFIG.EMERGENCY_LIQUIDATION_THRESHOLD
        
        logger.info("Risk manager initialized")
    
    def check_kill_switch(self) -> bool:
        """
        Check if kill switch is active.
        
        Returns:
            True if kill switch is active, False otherwise
        """
        try:
            kill_switch_file = SAFETY_CONFIG.KILL_SWITCH_FILE_PATH
            if os.path.exists(kill_switch_file):
                self.kill_switch_active = True
                log_security_event(
                    "kill_switch_activated",
                    {"file_path": kill_switch_file},
                    "CRITICAL"
                )
                return True
            else:
                self.kill_switch_active = False
                return False
                
        except Exception as e:
            logger.error("Failed to check kill switch", error=str(e))
            # Fail-closed: assume kill switch is active if we can't check
            self.kill_switch_active = True
            return True
    
    def calculate_position_size(self, symbol: str, price: float, risk_pct: Optional[float] = None) -> float:
        """
        Calculate appropriate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            price: Entry price
            risk_pct: Risk percentage (overrides default)
            
        Returns:
            Position size in base currency
        """
        try:
            if risk_pct is None:
                risk_pct = self.per_trade_pct
            
            # Calculate position size based on portfolio value and risk percentage
            position_value = self.portfolio_value * (risk_pct / 100.0)
            position_size = position_value / price
            
            # Apply position size limits
            min_size = TRADING_CONFIG.MIN_POSITION_SIZE_USD / price
            max_size = TRADING_CONFIG.MAX_POSITION_SIZE_USD / price
            
            position_size = max(min_size, min(position_size, max_size))
            
            log_trading_event(
                "position_size_calculated",
                {
                    "symbol": symbol,
                    "price": price,
                    "risk_pct": risk_pct,
                    "position_size": position_size,
                    "position_value": position_size * price
                },
                "INFO"
            )
            
            return position_size
            
        except Exception as e:
            logger.error("Failed to calculate position size", error=str(e))
            # Fail-closed: return zero position size
            return 0.0
    
    def can_open_position(self, symbol: str, side: str, amount: float, price: float) -> Tuple[bool, str]:
        """
        Check if a position can be opened based on risk limits.
        
        Args:
            symbol: Trading symbol
            side: Position side ('long' or 'short')
            amount: Position amount
            price: Entry price
            
        Returns:
            Tuple of (can_open, reason)
        """
        try:
            # Check kill switch
            if self.check_kill_switch():
                return False, "Kill switch is active"
            
            # Check maximum concurrent positions
            if len(self.positions) >= self.max_concurrent_positions:
                return False, f"Maximum concurrent positions ({self.max_concurrent_positions}) reached"
            
            # Check if position already exists
            if symbol in self.positions:
                return False, f"Position for {symbol} already exists"
            
            # Check position size limits
            position_value = amount * price
            if position_value < TRADING_CONFIG.MIN_POSITION_SIZE_USD:
                return False, f"Position size too small (${position_value:.2f} < ${TRADING_CONFIG.MIN_POSITION_SIZE_USD})"
            
            if position_value > TRADING_CONFIG.MAX_POSITION_SIZE_USD:
                return False, f"Position size too large (${position_value:.2f} > ${TRADING_CONFIG.MAX_POSITION_SIZE_USD})"
            
            # Check daily loss limit
            if self.daily_pnl < -(self.portfolio_value * self.daily_max_loss_percent / 100.0):
                return False, f"Daily loss limit exceeded (${self.daily_pnl:.2f})"
            
            # Check portfolio drawdown
            if self.max_drawdown > self.max_drawdown_pct:
                return False, f"Maximum drawdown exceeded ({self.max_drawdown:.2f}% > {self.max_drawdown_pct}%)"
            
            return True, "Position can be opened"
            
        except Exception as e:
            logger.error("Failed to check if position can be opened", error=str(e))
            # Fail-closed: refuse to open position
            return False, f"Risk check failed: {e}"
    
    def open_position(self, symbol: str, side: str, amount: float, price: float) -> bool:
        """
        Open a new position.
        
        Args:
            symbol: Trading symbol
            side: Position side ('long' or 'short')
            amount: Position amount
            price: Entry price
            
        Returns:
            True if position opened successfully, False otherwise
        """
        try:
            # Check if position can be opened
            can_open, reason = self.can_open_position(symbol, side, amount, price)
            if not can_open:
                log_trading_event(
                    "position_open_rejected",
                    {
                        "symbol": symbol,
                        "side": side,
                        "amount": amount,
                        "price": price,
                        "reason": reason
                    },
                    "WARNING"
                )
                return False
            
            # Create position
            position = Position(
                symbol=symbol,
                side=side,
                amount=amount,
                entry_price=price,
                current_price=price,
                status=PositionStatus.OPEN
            )
            
            self.positions[symbol] = position
            
            log_trading_event(
                "position_opened",
                {
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "position_value": amount * price
                },
                "INFO"
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to open position", error=str(e))
            log_security_event(
                "position_open_failed",
                {
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "error": str(e)
                },
                "ERROR"
            )
            return False
    
    def close_position(self, symbol: str, price: float, reason: str = "manual") -> bool:
        """
        Close an existing position.
        
        Args:
            symbol: Trading symbol
            price: Exit price
            reason: Reason for closing
            
        Returns:
            True if position closed successfully, False otherwise
        """
        try:
            if symbol not in self.positions:
                logger.warning("Attempted to close non-existent position", symbol=symbol)
                return False
            
            position = self.positions[symbol]
            
            # Calculate realized P&L
            if position.side == "long":
                realized_pnl = (price - position.entry_price) * position.amount
            else:  # short
                realized_pnl = (position.entry_price - price) * position.amount
            
            # Update position
            position.current_price = price
            position.realized_pnl = realized_pnl
            position.status = PositionStatus.CLOSED
            position.updated_at = time.time()
            
            # Update portfolio metrics
            self.daily_pnl += realized_pnl
            
            log_trading_event(
                "position_closed",
                {
                    "symbol": symbol,
                    "side": position.side,
                    "amount": position.amount,
                    "entry_price": position.entry_price,
                    "exit_price": price,
                    "realized_pnl": realized_pnl,
                    "reason": reason
                },
                "INFO"
            )
            
            # Remove position from active positions
            del self.positions[symbol]
            
            return True
            
        except Exception as e:
            logger.error("Failed to close position", error=str(e))
            log_security_event(
                "position_close_failed",
                {
                    "symbol": symbol,
                    "price": price,
                    "reason": reason,
                    "error": str(e)
                },
                "ERROR"
            )
            return False
    
    def update_position_prices(self, price_updates: Dict[str, float]) -> None:
        """
        Update current prices for positions.
        
        Args:
            price_updates: Dictionary of symbol -> price
        """
        try:
            for symbol, price in price_updates.items():
                if symbol in self.positions:
                    position = self.positions[symbol]
                    position.current_price = price
                    position.updated_at = time.time()
                    
                    # Calculate unrealized P&L
                    if position.side == "long":
                        position.unrealized_pnl = (price - position.entry_price) * position.amount
                    else:  # short
                        position.unrealized_pnl = (position.entry_price - price) * position.amount
            
        except Exception as e:
            logger.error("Failed to update position prices", error=str(e))
    
    def check_stop_loss_take_profit(self) -> List[Tuple[str, str, float]]:
        """
        Check for stop-loss and take-profit triggers.
        
        Returns:
            List of (symbol, action, price) tuples
        """
        triggers = []
        
        try:
            for symbol, position in self.positions.items():
                if position.current_price is None:
                    continue
                
                # Calculate P&L percentage
                if position.side == "long":
                    pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
                else:  # short
                    pnl_pct = ((position.entry_price - position.current_price) / position.entry_price) * 100
                
                # Check stop-loss
                if pnl_pct <= -self.hard_stop_pct:
                    triggers.append((symbol, "stop_loss", position.current_price))
                    log_trading_event(
                        "stop_loss_triggered",
                        {
                            "symbol": symbol,
                            "side": position.side,
                            "entry_price": position.entry_price,
                            "current_price": position.current_price,
                            "pnl_pct": pnl_pct,
                            "stop_loss_pct": self.hard_stop_pct
                        },
                        "WARNING"
                    )
                
                # Check take-profit
                elif pnl_pct >= self.profit_target_pct:
                    triggers.append((symbol, "take_profit", position.current_price))
                    log_trading_event(
                        "take_profit_triggered",
                        {
                            "symbol": symbol,
                            "side": position.side,
                            "entry_price": position.entry_price,
                            "current_price": position.current_price,
                            "pnl_pct": pnl_pct,
                            "profit_target_pct": self.profit_target_pct
                        },
                        "INFO"
                    )
            
        except Exception as e:
            logger.error("Failed to check stop-loss/take-profit", error=str(e))
        
        return triggers
    
    def check_emergency_conditions(self) -> List[str]:
        """
        Check for emergency conditions that require immediate action.
        
        Returns:
            List of emergency conditions
        """
        emergencies = []
        
        try:
            # Check kill switch
            if self.check_kill_switch():
                emergencies.append("Kill switch is active")
            
            # Check daily loss limit
            if self.daily_pnl < -(self.portfolio_value * self.daily_max_loss_percent / 100.0):
                emergencies.append(f"Daily loss limit exceeded: ${self.daily_pnl:.2f}")
            
            # Check maximum drawdown
            if self.max_drawdown > self.max_drawdown_pct:
                emergencies.append(f"Maximum drawdown exceeded: {self.max_drawdown:.2f}%")
            
            # Check emergency liquidation threshold
            if self.max_drawdown > self.emergency_liquidation_threshold:
                emergencies.append(f"Emergency liquidation threshold exceeded: {self.max_drawdown:.2f}%")
            
            # Check for positions exceeding maximum hold time
            current_time = time.time()
            for symbol, position in self.positions.items():
                if current_time - position.created_at > TRADING_CONFIG.MAX_TRADE_DURATION_HOURS * 3600:
                    emergencies.append(f"Position {symbol} exceeded maximum hold time")
            
        except Exception as e:
            logger.error("Failed to check emergency conditions", error=str(e))
            emergencies.append(f"Risk check failed: {e}")
        
        return emergencies
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Get current risk metrics.
        
        Returns:
            Risk metrics object
        """
        try:
            # Calculate total P&L
            total_pnl = self.daily_pnl
            for position in self.positions.values():
                if position.unrealized_pnl is not None:
                    total_pnl += position.unrealized_pnl
            
            # Determine risk level
            risk_level = RiskLevel.LOW
            if self.kill_switch_active:
                risk_level = RiskLevel.CRITICAL
            elif self.max_drawdown > self.max_drawdown_pct * 0.8:
                risk_level = RiskLevel.HIGH
            elif self.max_drawdown > self.max_drawdown_pct * 0.5:
                risk_level = RiskLevel.MEDIUM
            
            return RiskMetrics(
                portfolio_value=self.portfolio_value,
                total_pnl=total_pnl,
                daily_pnl=self.daily_pnl,
                max_drawdown=self.max_drawdown,
                position_count=len(self.positions),
                risk_level=risk_level,
                kill_switch_active=self.kill_switch_active,
                last_updated=time.time()
            )
            
        except Exception as e:
            logger.error("Failed to get risk metrics", error=str(e))
            # Return safe defaults
            return RiskMetrics(
                portfolio_value=0.0,
                total_pnl=0.0,
                daily_pnl=0.0,
                max_drawdown=0.0,
                position_count=0,
                risk_level=RiskLevel.CRITICAL,
                kill_switch_active=True,
                last_updated=time.time()
            )
    
    def should_sweep_profits(self) -> bool:
        """
        Check if profits should be swept to cold storage.
        
        Returns:
            True if profits should be swept, False otherwise
        """
        try:
            risk_metrics = self.get_risk_metrics()
            return risk_metrics.total_pnl >= self.profit_sweep_threshold
            
        except Exception as e:
            logger.error("Failed to check profit sweep condition", error=str(e))
            # Fail-closed: don't sweep profits if we can't determine
            return False
    
    def reset_daily_metrics(self) -> None:
        """Reset daily metrics (call at start of new trading day)."""
        try:
            self.daily_pnl = 0.0
            self.last_risk_check = time.time()
            
            log_trading_event(
                "daily_metrics_reset",
                {"timestamp": time.time()},
                "INFO"
            )
            
        except Exception as e:
            logger.error("Failed to reset daily metrics", error=str(e))


# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """
    Get the global risk manager instance.
    
    Returns:
        Risk manager instance
    """
    global _risk_manager
    
    if _risk_manager is None:
        _risk_manager = RiskManager()
    
    return _risk_manager
