"""
Database utilities for the meme-coin trading bot.

This module provides database connection management, schema creation,
and common database operations with proper error handling and logging.
"""

import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import structlog

from src.config import DATABASE_CONFIG
from src.utils.logger import log_security_event

logger = structlog.get_logger(__name__)

# Database base class
Base = declarative_base()


class TradeRecord(Base):
    """Trade record model."""
    __tablename__ = 'trade_records'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    tx_hash = Column(String(66), nullable=True)
    status = Column(String(20), nullable=False)  # 'pending', 'completed', 'failed'
    paper_mode = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class PositionRecord(Base):
    """Position record model."""
    __tablename__ = 'position_records'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    amount = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # 'open', 'closed', 'liquidated'
    paper_mode = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SecurityEventRecord(Base):
    """Security event record model."""
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON string
    timestamp = Column(DateTime, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)


class PerformanceMetricRecord(Base):
    """Performance metric record model."""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    metric_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False)


class DatabaseManager:
    """
    Database manager with connection pooling and error handling.
    
    Features:
    - Connection pooling
    - Automatic retry logic
    - Transaction management
    - Performance monitoring
    - Security event logging
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv("DATABASE_URL_SQLITE", "sqlite:///data/memebot.db")
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine with proper configuration."""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                pool_size=DATABASE_CONFIG.DB_POOL_SIZE,
                max_overflow=DATABASE_CONFIG.DB_MAX_OVERFLOW,
                pool_timeout=DATABASE_CONFIG.DB_POOL_TIMEOUT,
                pool_recycle=3600,  # Recycle connections every hour
                echo=False,  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized", url=self.database_url)
            
        except Exception as e:
            logger.error("Failed to initialize database engine", error=str(e))
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
            
        except SQLAlchemyError as e:
            logger.error("Failed to drop database tables", error=str(e))
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get database session with automatic cleanup.
        
        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()
    
    def get_session_sync(self):
        """
        Get synchronous database session.
        
        Returns:
            Database session
        """
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("Database connection test successful")
            return True
            
        except SQLAlchemyError as e:
            logger.error("Database connection test failed", error=str(e))
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dictionary with database information
        """
        try:
            with self.engine.connect() as connection:
                # Get table counts
                trade_count = connection.execute(text("SELECT COUNT(*) FROM trade_records")).scalar()
                position_count = connection.execute(text("SELECT COUNT(*) FROM position_records")).scalar()
                security_count = connection.execute(text("SELECT COUNT(*) FROM security_events")).scalar()
                performance_count = connection.execute(text("SELECT COUNT(*) FROM performance_metrics")).scalar()
                
                # Get database size (for SQLite)
                if "sqlite" in self.database_url:
                    size_result = connection.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
                    db_size = size_result.scalar()
                else:
                    db_size = None
                
                return {
                    "database_url": self.database_url,
                    "trade_records": trade_count,
                    "position_records": position_count,
                    "security_events": security_count,
                    "performance_metrics": performance_count,
                    "database_size_bytes": db_size,
                    "connection_pool_size": DATABASE_CONFIG.DB_POOL_SIZE,
                    "max_overflow": DATABASE_CONFIG.DB_MAX_OVERFLOW,
                }
                
        except SQLAlchemyError as e:
            logger.error("Failed to get database info", error=str(e))
            return {"error": str(e)}
    
    def cleanup_old_records(self):
        """Clean up old records based on retention policies."""
        try:
            with self.engine.connect() as connection:
                # Clean up old performance metrics
                connection.execute(text(f"""
                    DELETE FROM performance_metrics 
                    WHERE created_at < datetime('now', '-{DATABASE_CONFIG.LOG_RETENTION_DAYS} days')
                """))
                
                # Clean up old security events (keep longer)
                connection.execute(text(f"""
                    DELETE FROM security_events 
                    WHERE created_at < datetime('now', '-{DATABASE_CONFIG.LOG_RETENTION_DAYS * 2} days')
                """))
                
                connection.commit()
                
            logger.info("Old records cleaned up successfully")
            
        except SQLAlchemyError as e:
            logger.error("Failed to cleanup old records", error=str(e))
            raise


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        Database manager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
    
    return _db_manager


def initialize_database() -> bool:
    """
    Initialize the database with tables and initial setup.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        db_manager = get_database_manager()
        
        # Test connection
        if not db_manager.test_connection():
            return False
        
        # Create tables
        db_manager.create_tables()
        
        # Log successful initialization
        log_security_event(
            "database_initialized",
            {"database_url": db_manager.database_url},
            "INFO"
        )
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        log_security_event(
            "database_init_failed",
            {"error": str(e)},
            "ERROR"
        )
        return False


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        db_manager = get_database_manager()
        return db_manager.test_connection()
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


def get_database_info() -> Dict[str, Any]:
    """
    Get database information and statistics.
    
    Returns:
        Dictionary with database information
    """
    try:
        db_manager = get_database_manager()
        return db_manager.get_database_info()
    except Exception as e:
        logger.error("Failed to get database info", error=str(e))
        return {"error": str(e)}
