"""
Utility modules for the meme-coin trading bot.

This module provides common utilities for logging, database operations,
scheduling, and other shared functionality.
"""

from .logger import (
    setup_logging,
    get_logger,
    log_security_event,
    log_trading_event,
    log_performance_metric,
    log_audit_trail,
)
from .database import (
    DatabaseManager,
    TradeRecord,
    PositionRecord,
    SecurityEventRecord,
    PerformanceMetricRecord,
    get_database_manager,
    initialize_database,
    test_connection,
    get_database_info,
)
# Scheduler imports removed to avoid circular dependencies

__all__ = [
    'setup_logging',
    'get_logger',
    'log_security_event',
    'log_trading_event',
    'log_performance_metric',
    'log_audit_trail',
    'DatabaseManager',
    'TradeRecord',
    'PositionRecord',
    'SecurityEventRecord',
    'PerformanceMetricRecord',
    'get_database_manager',
    'initialize_database',
    'test_connection',
    'get_database_info',
]
