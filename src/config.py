"""
Configuration parameters for the meme-coin trading bot.

This module contains all numeric and behavioral parameters.
No secrets are stored here - they come from environment variables.
"""

from typing import Final
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Trading behavior configuration parameters."""
    
    # Risk Management Parameters
    DAILY_MAX_LOSS_PERCENT: Final[float] = 5.0  # Maximum daily loss percentage
    PROFIT_SWEEP_THRESHOLD: Final[float] = 1000.0  # USD threshold for profit sweeping
    PER_TRADE_PCT: Final[float] = 2.0  # Percentage of portfolio per trade
    MAX_CONCURRENT_POSITIONS: Final[int] = 5  # Maximum simultaneous positions
    PROFIT_TARGET_PCT: Final[float] = 15.0  # Target profit percentage
    HARD_STOP_PCT: Final[float] = 8.0  # Hard stop loss percentage
    
    # Multi-Chain Parameters
    SOLANA_MODE: Final[bool] = True  # Enable Solana trading
    TELEGRAM_MODE: Final[bool] = True  # Enable Telegram signal ingestion
    MAX_POSITION_SIZE_SOL: Final[float] = 100.0  # Maximum position size in SOL
    SOLANA_COMPUTE_BUDGET: Final[int] = 200000  # Default compute budget units
    SOLANA_PRIORITY_FEE: Final[float] = 0.001  # Priority fee in SOL
    
    # Trading Timing Parameters
    WATCH_CADENCE_SECONDS: Final[int] = 30  # How often to check for opportunities
    MIN_TRADE_INTERVAL_SECONDS: Final[int] = 300  # Minimum time between trades
    MAX_TRADE_DURATION_HOURS: Final[int] = 24  # Maximum position hold time
    
    # Position Sizing Parameters
    MIN_POSITION_SIZE_USD: Final[float] = 50.0  # Minimum position size
    MAX_POSITION_SIZE_USD: Final[float] = 5000.0  # Maximum position size
    POSITION_SIZE_MULTIPLIER: Final[float] = 1.0  # Risk multiplier for position sizing
    
    # Slippage and Fees
    MAX_SLIPPAGE_PCT: Final[float] = 2.0  # Maximum acceptable slippage
    ESTIMATED_FEE_PCT: Final[float] = 0.3  # Estimated trading fees
    
    # Liquidity Requirements
    MIN_LIQUIDITY_USD: Final[float] = 10000.0  # Minimum liquidity for trading
    MIN_VOLUME_24H_USD: Final[float] = 50000.0  # Minimum 24h volume


@dataclass
class SafetyConfig:
    """Safety and security configuration parameters."""
    
    # Paper Mode Configuration
    PAPER_MODE: Final[bool] = True  # Default to paper mode for safety
    
    # Kill Switch Parameters
    KILL_SWITCH_ENABLED: Final[bool] = True  # Enable kill switch
    KILL_SWITCH_FILE_PATH: Final[str] = "/tmp/meme_bot_kill_switch"
    KILL_SWITCH_CHECK_INTERVAL: Final[int] = 10  # Check every 10 seconds
    
    # Emergency Parameters
    EMERGENCY_STOP_LOSS_PCT: Final[float] = 20.0  # Emergency stop loss
    MAX_DRAWDOWN_PCT: Final[float] = 15.0  # Maximum portfolio drawdown
    EMERGENCY_LIQUIDATION_THRESHOLD: Final[float] = 25.0  # Emergency liquidation threshold
    
    # Security Parameters
    MAX_FAILED_AUTH_ATTEMPTS: Final[int] = 3  # Maximum failed authentication attempts
    SESSION_TIMEOUT_MINUTES: Final[int] = 30  # Session timeout
    ENCRYPTION_KEY_ROTATION_DAYS: Final[int] = 30  # Key rotation interval


@dataclass
class NetworkConfig:
    """Network and connection configuration parameters."""
    
    # RPC Connection Parameters
    RPC_TIMEOUT_SECONDS: Final[int] = 30  # RPC request timeout
    RPC_RETRY_ATTEMPTS: Final[int] = 3  # Number of retry attempts
    RPC_RETRY_DELAY_SECONDS: Final[int] = 5  # Delay between retries
    
    # WebSocket Parameters
    WS_RECONNECT_DELAY_SECONDS: Final[int] = 10  # WebSocket reconnect delay
    WS_PING_INTERVAL_SECONDS: Final[int] = 30  # WebSocket ping interval
    WS_PING_TIMEOUT_SECONDS: Final[int] = 10  # WebSocket ping timeout
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: Final[int] = 100  # Maximum API requests per minute
    RATE_LIMIT_BURST_SIZE: Final[int] = 20  # Burst size for rate limiting


@dataclass
class DatabaseConfig:
    """Database configuration parameters."""
    
    # Connection Parameters
    DB_POOL_SIZE: Final[int] = 10  # Database connection pool size
    DB_MAX_OVERFLOW: Final[int] = 20  # Maximum overflow connections
    DB_POOL_TIMEOUT: Final[int] = 30  # Pool timeout in seconds
    
    # Query Parameters
    DB_QUERY_TIMEOUT: Final[int] = 30  # Query timeout in seconds
    DB_BATCH_SIZE: Final[int] = 1000  # Batch size for bulk operations
    
    # Retention Parameters
    LOG_RETENTION_DAYS: Final[int] = 90  # Log retention period
    TRADE_HISTORY_RETENTION_DAYS: Final[int] = 365  # Trade history retention


@dataclass
class LoggingConfig:
    """Logging configuration parameters."""
    
    # Log Levels
    DEFAULT_LOG_LEVEL: Final[str] = "INFO"  # Default logging level
    TRADING_LOG_LEVEL: Final[str] = "DEBUG"  # Trading-specific log level
    SECURITY_LOG_LEVEL: Final[str] = "WARNING"  # Security log level
    
    # Log Rotation
    MAX_LOG_FILE_SIZE_MB: Final[int] = 100  # Maximum log file size
    LOG_BACKUP_COUNT: Final[int] = 5  # Number of backup log files
    
    # Log Formatting
    LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


@dataclass
class MLConfig:
    """Machine learning configuration parameters."""
    
    # Model Parameters
    MODEL_UPDATE_INTERVAL_HOURS: Final[int] = 24  # Model update frequency
    MODEL_RETRAIN_THRESHOLD: Final[int] = 1000  # Minimum samples for retraining
    MODEL_CONFIDENCE_THRESHOLD: Final[float] = 0.7  # Minimum confidence for predictions
    
    # Feature Engineering
    LOOKBACK_PERIODS: Final[list[int]] = None  # Technical indicator periods - will be set in __post_init__
    FEATURE_WINDOW_SIZE: Final[int] = 100  # Feature window size
    
    # Training Parameters
    TRAINING_SPLIT_RATIO: Final[float] = 0.8  # Train/test split ratio
    VALIDATION_SPLIT_RATIO: Final[float] = 0.2  # Validation split ratio
    MIN_TRAINING_SAMPLES: Final[int] = 100  # Minimum samples for training
    
    # Kraken Weighting
    ML_UNLISTED_WEIGHT: Final[float] = 0.3  # ML weight for unlisted tokens
    UNLISTED_SIZE_MULTIPLIER: Final[float] = 0.5  # Position size multiplier for unlisted tokens
    KRAKEN_COMPLIANCE_THRESHOLD: Final[float] = 70.0  # Minimum compliance score
    HARD_VETO_THRESHOLD: Final[float] = 60.0  # Hard veto threshold
    
    # Cache Configuration
    AUDIT_CACHE_TTL: Final[int] = 3600  # Cache TTL in seconds (1 hour)
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.LOOKBACK_PERIODS is None:
            object.__setattr__(self, 'LOOKBACK_PERIODS', [5, 10, 20, 50, 100])


# Global configuration instances
TRADING_CONFIG = TradingConfig()
SAFETY_CONFIG = SafetyConfig()
NETWORK_CONFIG = NetworkConfig()
DATABASE_CONFIG = DatabaseConfig()
LOGGING_CONFIG = LoggingConfig()
ML_CONFIG = MLConfig()


def get_config_summary() -> dict:
    """Get a summary of all configuration parameters."""
    return {
        "trading": {
            "daily_max_loss_percent": TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT,
            "profit_sweep_threshold": TRADING_CONFIG.PROFIT_SWEEP_THRESHOLD,
            "per_trade_pct": TRADING_CONFIG.PER_TRADE_PCT,
            "max_concurrent_positions": TRADING_CONFIG.MAX_CONCURRENT_POSITIONS,
            "profit_target_pct": TRADING_CONFIG.PROFIT_TARGET_PCT,
            "hard_stop_pct": TRADING_CONFIG.HARD_STOP_PCT,
        },
        "safety": {
            "paper_mode": SAFETY_CONFIG.PAPER_MODE,
            "kill_switch_enabled": SAFETY_CONFIG.KILL_SWITCH_ENABLED,
            "emergency_stop_loss_pct": SAFETY_CONFIG.EMERGENCY_STOP_LOSS_PCT,
            "max_drawdown_pct": SAFETY_CONFIG.MAX_DRAWDOWN_PCT,
        },
        "network": {
            "rpc_timeout_seconds": NETWORK_CONFIG.RPC_TIMEOUT_SECONDS,
            "rpc_retry_attempts": NETWORK_CONFIG.RPC_RETRY_ATTEMPTS,
            "max_requests_per_minute": NETWORK_CONFIG.MAX_REQUESTS_PER_MINUTE,
        },
        "database": {
            "pool_size": DATABASE_CONFIG.DB_POOL_SIZE,
            "log_retention_days": DATABASE_CONFIG.LOG_RETENTION_DAYS,
            "trade_history_retention_days": DATABASE_CONFIG.TRADE_HISTORY_RETENTION_DAYS,
        },
        "logging": {
            "default_log_level": LOGGING_CONFIG.DEFAULT_LOG_LEVEL,
            "max_log_file_size_mb": LOGGING_CONFIG.MAX_LOG_FILE_SIZE_MB,
        },
        "ml": {
            "model_update_interval_hours": ML_CONFIG.MODEL_UPDATE_INTERVAL_HOURS,
            "model_confidence_threshold": ML_CONFIG.MODEL_CONFIDENCE_THRESHOLD,
            "min_training_samples": ML_CONFIG.MIN_TRAINING_SAMPLES,
        },
    }
