"""
Logging utilities for the meme-coin trading bot.

This module provides structured logging with security considerations,
audit trails, and performance monitoring.
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                logs_dir / "memebot.log",
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=5
            )
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_security_event(event_type: str, details: dict, severity: str = "INFO") -> None:
    """
    Log security-related events with special handling.
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity
    """
    logger = get_logger("security")
    
    # Add security context
    security_details = {
        "event_type": event_type,
        "severity": severity,
        "timestamp": time.time(),
        **details
    }
    
    # Log to security-specific file
    security_logger = logging.getLogger("security")
    security_handler = logging.FileHandler("logs/security.log")
    security_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    security_logger.addHandler(security_handler)
    
    # Log the event
    if severity.upper() == "CRITICAL":
        logger.critical("Security event", **security_details)
    elif severity.upper() == "ERROR":
        logger.error("Security event", **security_details)
    elif severity.upper() == "WARNING":
        logger.warning("Security event", **security_details)
    else:
        logger.info("Security event", **security_details)


def log_trading_event(event_type: str, details: dict, severity: str = "INFO") -> None:
    """
    Log trading-related events with special handling.
    
    Args:
        event_type: Type of trading event
        details: Event details
        severity: Event severity
    """
    logger = get_logger("trading")
    
    # Add trading context
    trading_details = {
        "event_type": event_type,
        "severity": severity,
        "timestamp": time.time(),
        **details
    }
    
    # Log to trading-specific file
    trading_logger = logging.getLogger("trading")
    trading_handler = logging.FileHandler("logs/trading.log")
    trading_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    trading_logger.addHandler(trading_handler)
    
    # Log the event
    if severity.upper() == "CRITICAL":
        logger.critical("Trading event", **trading_details)
    elif severity.upper() == "ERROR":
        logger.error("Trading event", **trading_details)
    elif severity.upper() == "WARNING":
        logger.warning("Trading event", **trading_details)
    else:
        logger.info("Trading event", **trading_details)


def log_performance_metric(metric_name: str, value: float, unit: str = "") -> None:
    """
    Log performance metrics for monitoring.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
    """
    logger = get_logger("performance")
    
    logger.info(
        "Performance metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        timestamp=structlog.processors.TimeStamper(fmt="iso")()
    )


def log_audit_trail(action: str, user: str, details: dict) -> None:
    """
    Log audit trail events for compliance and security.
    
    Args:
        action: Action performed
        user: User who performed the action
        details: Action details
    """
    logger = get_logger("audit")
    
    audit_details = {
        "action": action,
        "user": user,
        "timestamp": time.time(),
        **details
    }
    
    # Log to audit-specific file
    audit_logger = logging.getLogger("audit")
    audit_handler = logging.FileHandler("logs/audit.log")
    audit_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    audit_logger.addHandler(audit_handler)
    
    logger.info("Audit trail", **audit_details)
