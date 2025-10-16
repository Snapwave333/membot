"""
Trading strategy for the meme-coin trading bot.

This module provides the main trading strategy that combines
rules-based logic with ML predictions for intelligent trading decisions.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config import TRADING_CONFIG
from src.trading.risk_manager import get_risk_manager
from src.trading.exchange import get_exchange_interface, OrderSide, OrderType
from src.brain.rules_engine import get_rules_engine, RuleType
from src.brain.ml_engine import get_ml_engine
from src.utils.logger import log_trading_event, log_performance_metric

logger = structlog.get_logger(__name__)


class StrategyStatus(Enum):
    """Strategy status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TradingSignal:
    """Trading signal data structure."""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reason: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class StrategyMetrics:
    """Strategy performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    last_updated: float


class TradingStrategy:
    """
    Main trading strategy combining rules and ML.
    
    Features:
    - Rules-based decision making
    - ML prediction integration
    - Risk management integration
    - Performance monitoring
    - Signal generation
    """
    
    def __init__(self):
        """Initialize the trading strategy."""
        self.status = StrategyStatus.ACTIVE
        self.risk_manager = get_risk_manager()
        self.exchange = get_exchange_interface(paper_mode=True)
        self.rules_engine = get_rules_engine()
        self.ml_engine = get_ml_engine()
        
        # Strategy metrics
        self.metrics = StrategyMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_pnl=0.0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            last_updated=time.time()
        )
        
        # Trading signals
        self.signals: List[TradingSignal] = []
        
        # Strategy parameters
        self.symbols_to_trade = ["ETH", "BTC", "DOGE", "SHIB"]
        self.min_confidence_threshold = 0.6
        self.max_signals_per_hour = 10
        
        logger.info("Trading strategy initialized")
    
    def analyze_market(self, symbol: str) -> Optional[TradingSignal]:
        """
        Analyze market conditions and generate trading signal.
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Trading signal if generated, None otherwise
        """
        try:
            start_time = time.time()
            
            # Get market data
            market_data = self.exchange.get_market_data(symbol)
            if not market_data:
                logger.warning("No market data available", symbol=symbol)
                return None
            
            # Prepare context for rules and ML
            context = self._prepare_context(symbol, market_data)
            
            # Get rules-based decision
            rules_decision, rules_reason, rules_confidence = self.rules_engine.get_decision(
                RuleType.ENTRY, context
            )
            
            # Get ML-based decision
            ml_decision, ml_reason, ml_confidence = self.ml_engine.get_ml_decision(context)
            
            # Combine decisions
            combined_decision, combined_reason, combined_confidence = self._combine_decisions(
                rules_decision, rules_reason, rules_confidence,
                ml_decision, ml_reason, ml_confidence
            )
            
            # Generate signal
            if combined_confidence >= self.min_confidence_threshold:
                action = "buy" if combined_decision else "hold"
                signal = TradingSignal(
                    symbol=symbol,
                    action=action,
                    confidence=combined_confidence,
                    reason=combined_reason,
                    timestamp=time.time(),
                    metadata={
                        "rules_decision": rules_decision,
                        "rules_confidence": rules_confidence,
                        "ml_decision": ml_decision,
                        "ml_confidence": ml_confidence,
                        "analysis_time": time.time() - start_time
                    }
                )
                
                self.signals.append(signal)
                
                log_trading_event(
                    "trading_signal_generated",
                    {
                        "symbol": symbol,
                        "action": action,
                        "confidence": combined_confidence,
                        "reason": combined_reason,
                        "analysis_time": time.time() - start_time
                    },
                    "INFO"
                )
                
                return signal
            
            execution_time = time.time() - start_time
            log_performance_metric("market_analysis_time", execution_time, "seconds")
            
            return None
            
        except Exception as e:
            logger.error("Failed to analyze market", symbol=symbol, error=str(e))
            return None
    
    def _prepare_context(self, symbol: str, market_data: Any) -> Dict[str, Any]:
        """
        Prepare context data for rules and ML engines.
        
        Args:
            symbol: Trading symbol
            market_data: Market data object
            
        Returns:
            Context dictionary
        """
        try:
            # Get current positions
            positions = self.risk_manager.positions
            position_count = len(positions)
            
            # Get portfolio metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # Get recent signals for this symbol
            recent_signals = [s for s in self.signals 
                            if s.symbol == symbol and time.time() - s.timestamp < 3600]
            
            context = {
                # Market data
                "symbol": symbol,
                "price": market_data.price,
                "volume_24h": market_data.volume_24h,
                "market_cap": market_data.market_cap,
                "liquidity": market_data.liquidity,
                
                # Risk metrics
                "portfolio_value": risk_metrics.portfolio_value,
                "total_pnl": risk_metrics.total_pnl,
                "daily_pnl": risk_metrics.daily_pnl,
                "max_drawdown": risk_metrics.max_drawdown,
                "position_count": position_count,
                "risk_level": risk_metrics.risk_level.value,
                
                # Trading limits
                "daily_max_loss_pct": TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT,
                "per_trade_pct": TRADING_CONFIG.PER_TRADE_PCT,
                "max_concurrent_positions": TRADING_CONFIG.MAX_CONCURRENT_POSITIONS,
                "profit_target_pct": TRADING_CONFIG.PROFIT_TARGET_PCT,
                "hard_stop_pct": TRADING_CONFIG.HARD_STOP_PCT,
                
                # Position sizing
                "min_position_size_usd": TRADING_CONFIG.MIN_POSITION_SIZE_USD,
                "max_position_size_usd": TRADING_CONFIG.MAX_POSITION_SIZE_USD,
                
                # Timing
                "min_trade_interval": TRADING_CONFIG.MIN_TRADE_INTERVAL_SECONDS,
                "max_hold_time": TRADING_CONFIG.MAX_TRADE_DURATION_HOURS,
                
                # Market conditions
                "market_open": True,  # Crypto markets are always open
                "time_since_last_trade": self._get_time_since_last_trade(),
                
                # Signal history
                "recent_signals_count": len(recent_signals),
                "signals_per_hour": len(recent_signals),
            }
            
            return context
            
        except Exception as e:
            logger.error("Failed to prepare context", symbol=symbol, error=str(e))
            return {}
    
    def _combine_decisions(self, rules_decision: bool, rules_reason: str, rules_confidence: float,
                          ml_decision: bool, ml_reason: str, ml_confidence: float) -> Tuple[bool, str, float]:
        """
        Combine rules-based and ML-based decisions.
        
        Args:
            rules_decision: Rules-based decision
            rules_reason: Rules-based reason
            rules_confidence: Rules-based confidence
            ml_decision: ML-based decision
            ml_reason: ML-based reason
            ml_confidence: ML-based confidence
            
        Returns:
            Tuple of (combined_decision, combined_reason, combined_confidence)
        """
        try:
            # Weight the decisions (rules: 60%, ML: 40%)
            rules_weight = 0.6
            ml_weight = 0.4
            
            # Calculate combined confidence
            combined_confidence = (rules_confidence * rules_weight + ml_confidence * ml_weight)
            
            # Calculate combined decision score
            rules_score = 1.0 if rules_decision else 0.0
            ml_score = 1.0 if ml_decision else 0.0
            
            combined_score = (rules_score * rules_weight + ml_score * ml_weight)
            
            # Make decision based on score threshold
            decision_threshold = 0.5
            combined_decision = combined_score >= decision_threshold
            
            # Create combined reason
            combined_reason = f"Rules: {rules_reason} (conf: {rules_confidence:.2f}) | ML: {ml_reason} (conf: {ml_confidence:.2f})"
            
            return combined_decision, combined_reason, combined_confidence
            
        except Exception as e:
            logger.error("Failed to combine decisions", error=str(e))
            return False, f"Decision combination error: {e}", 0.0
    
    def _get_time_since_last_trade(self) -> float:
        """Get time since last trade."""
        try:
            # Get recent orders
            recent_orders = self.exchange.get_order_history()
            if recent_orders:
                last_order = recent_orders[0]  # Most recent order
                return time.time() - last_order.created_at
            
            return float('inf')  # No recent trades
            
        except Exception as e:
            logger.error("Failed to get time since last trade", error=str(e))
            return float('inf')
    
    def execute_signal(self, signal: TradingSignal) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            True if signal executed successfully, False otherwise
        """
        try:
            if signal.action == "hold":
                return True  # No action needed
            
            # Check if we can open a position
            can_open, reason = self.risk_manager.can_open_position(
                signal.symbol, "long", 1.0, 1.0  # Placeholder values
            )
            
            if not can_open:
                log_trading_event(
                    "signal_execution_rejected",
                    {
                        "symbol": signal.symbol,
                        "action": signal.action,
                        "reason": reason,
                        "signal_confidence": signal.confidence
                    },
                    "WARNING"
                )
                return False
            
            # Calculate position size
            market_data = self.exchange.get_market_data(signal.symbol)
            if not market_data:
                logger.warning("No market data for position sizing", symbol=signal.symbol)
                return False
            
            position_size = self.risk_manager.calculate_position_size(
                signal.symbol, market_data.price
            )
            
            if position_size <= 0:
                logger.warning("Invalid position size", symbol=signal.symbol, size=position_size)
                return False
            
            # Place order
            order_side = OrderSide.BUY if signal.action == "buy" else OrderSide.SELL
            order = self.exchange.place_order(
                symbol=signal.symbol,
                side=order_side,
                order_type=OrderType.MARKET,
                amount=position_size
            )
            
            if order and order.status.value == "filled":
                # Open position in risk manager
                success = self.risk_manager.open_position(
                    signal.symbol, "long", position_size, market_data.price
                )
                
                if success:
                    self.metrics.total_trades += 1
                    self.metrics.last_updated = time.time()
                    
                    log_trading_event(
                        "signal_executed",
                        {
                            "symbol": signal.symbol,
                            "action": signal.action,
                            "position_size": position_size,
                            "price": market_data.price,
                            "signal_confidence": signal.confidence,
                            "order_id": order.order_id
                        },
                        "INFO"
                    )
                    
                    return True
                else:
                    logger.error("Failed to open position in risk manager", symbol=signal.symbol)
                    return False
            else:
                logger.error("Failed to place order", symbol=signal.symbol, order=order)
                return False
                
        except Exception as e:
            logger.error("Failed to execute signal", symbol=signal.symbol, error=str(e))
            return False
    
    def update_positions(self):
        """Update all open positions."""
        try:
            # Get current market data for all symbols
            price_updates = {}
            for symbol in self.symbols_to_trade:
                market_data = self.exchange.get_market_data(symbol)
                if market_data:
                    price_updates[symbol] = market_data.price
            
            # Update position prices
            self.risk_manager.update_position_prices(price_updates)
            
            # Check for stop-loss and take-profit triggers
            triggers = self.risk_manager.check_stop_loss_take_profit()
            
            for symbol, action, price in triggers:
                if action == "stop_loss":
                    self.risk_manager.close_position(symbol, price, "stop_loss")
                    log_trading_event(
                        "position_closed_stop_loss",
                        {"symbol": symbol, "price": price},
                        "WARNING"
                    )
                elif action == "take_profit":
                    self.risk_manager.close_position(symbol, price, "take_profit")
                    log_trading_event(
                        "position_closed_take_profit",
                        {"symbol": symbol, "price": price},
                        "INFO"
                    )
            
        except Exception as e:
            logger.error("Failed to update positions", error=str(e))
    
    def run_strategy_cycle(self):
        """Run one cycle of the trading strategy."""
        try:
            if self.status != StrategyStatus.ACTIVE:
                return
            
            # Update positions
            self.update_positions()
            
            # Analyze each symbol
            for symbol in self.symbols_to_trade:
                signal = self.analyze_market(symbol)
                if signal and signal.confidence >= self.min_confidence_threshold:
                    self.execute_signal(signal)
            
            # Update metrics
            self._update_metrics()
            
        except Exception as e:
            logger.error("Failed to run strategy cycle", error=str(e))
            self.status = StrategyStatus.ERROR
    
    def _update_metrics(self):
        """Update strategy performance metrics."""
        try:
            # Get recent trades
            recent_orders = self.exchange.get_order_history()
            
            # Calculate basic metrics
            total_trades = len(recent_orders)
            winning_trades = 0
            losing_trades = 0
            total_pnl = 0.0
            
            for order in recent_orders:
                if order.status.value == "filled":
                    # Simple P&L calculation (in production, use actual P&L)
                    pnl = 0.0  # Placeholder
                    total_pnl += pnl
                    
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1
            
            # Update metrics
            self.metrics.total_trades = total_trades
            self.metrics.winning_trades = winning_trades
            self.metrics.losing_trades = losing_trades
            self.metrics.total_pnl = total_pnl
            self.metrics.win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            self.metrics.avg_win = total_pnl / winning_trades if winning_trades > 0 else 0.0
            self.metrics.avg_loss = total_pnl / losing_trades if losing_trades > 0 else 0.0
            self.metrics.last_updated = time.time()
            
        except Exception as e:
            logger.error("Failed to update metrics", error=str(e))
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """
        Get current strategy status.
        
        Returns:
            Dictionary with strategy status
        """
        try:
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            return {
                "status": self.status.value,
                "symbols_traded": self.symbols_to_trade,
                "min_confidence_threshold": self.min_confidence_threshold,
                "max_signals_per_hour": self.max_signals_per_hour,
                "metrics": {
                    "total_trades": self.metrics.total_trades,
                    "winning_trades": self.metrics.winning_trades,
                    "losing_trades": self.metrics.losing_trades,
                    "total_pnl": self.metrics.total_pnl,
                    "win_rate": self.metrics.win_rate,
                    "avg_win": self.metrics.avg_win,
                    "avg_loss": self.metrics.avg_loss,
                    "max_drawdown": self.metrics.max_drawdown,
                    "sharpe_ratio": self.metrics.sharpe_ratio,
                    "last_updated": self.metrics.last_updated
                },
                "risk_metrics": {
                    "portfolio_value": risk_metrics.portfolio_value,
                    "total_pnl": risk_metrics.total_pnl,
                    "daily_pnl": risk_metrics.daily_pnl,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "position_count": risk_metrics.position_count,
                    "risk_level": risk_metrics.risk_level.value,
                    "kill_switch_active": risk_metrics.kill_switch_active
                },
                "signal_count": len(self.signals),
                "recent_signals": len([s for s in self.signals if time.time() - s.timestamp < 3600])
            }
            
        except Exception as e:
            logger.error("Failed to get strategy status", error=str(e))
            return {"error": str(e)}
    
    def pause_strategy(self):
        """Pause the trading strategy."""
        self.status = StrategyStatus.PAUSED
        log_trading_event("strategy_paused", {}, "INFO")
    
    def resume_strategy(self):
        """Resume the trading strategy."""
        self.status = StrategyStatus.ACTIVE
        log_trading_event("strategy_resumed", {}, "INFO")
    
    def stop_strategy(self):
        """Stop the trading strategy."""
        self.status = StrategyStatus.STOPPED
        log_trading_event("strategy_stopped", {}, "INFO")


# Global strategy instance
_strategy: Optional[TradingStrategy] = None


def get_strategy() -> TradingStrategy:
    """
    Get the global strategy instance.
    
    Returns:
        Strategy instance
    """
    global _strategy
    
    if _strategy is None:
        _strategy = TradingStrategy()
    
    return _strategy
