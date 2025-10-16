"""
Scheduler for the meme-coin trading bot.

This module provides a scheduling system for running the trading strategy
at regular intervals with proper error handling and monitoring.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config import TRADING_CONFIG
from src.trading.strategy import get_strategy
from src.utils.logger import log_trading_event, log_performance_metric

logger = structlog.get_logger(__name__)


class SchedulerStatus(Enum):
    """Scheduler status enumeration."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SchedulerMetrics:
    """Scheduler performance metrics."""
    total_cycles: int
    successful_cycles: int
    failed_cycles: int
    avg_cycle_time: float
    last_cycle_time: float
    uptime: float
    start_time: float


class TradingScheduler:
    """
    Scheduler for running the trading strategy.
    
    Features:
    - Configurable interval scheduling
    - Error handling and recovery
    - Performance monitoring
    - Graceful shutdown
    """
    
    def __init__(self, interval_seconds: int = None):
        """
        Initialize the trading scheduler.
        
        Args:
            interval_seconds: Scheduling interval in seconds
        """
        self.interval_seconds = interval_seconds or TRADING_CONFIG.WATCH_CADENCE_SECONDS
        self.status = SchedulerStatus.STOPPED
        self.strategy = get_strategy()
        
        # Metrics
        self.metrics = SchedulerMetrics(
            total_cycles=0,
            successful_cycles=0,
            failed_cycles=0,
            avg_cycle_time=0.0,
            last_cycle_time=0.0,
            uptime=0.0,
            start_time=0.0
        )
        
        # Control flags
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info("Trading scheduler initialized", interval=self.interval_seconds)
    
    async def start(self):
        """Start the scheduler."""
        try:
            if self.status == SchedulerStatus.RUNNING:
                logger.warning("Scheduler already running")
                return
            
            self.status = SchedulerStatus.RUNNING
            self._running = True
            self.metrics.start_time = time.time()
            
            # Start the main loop
            self._task = asyncio.create_task(self._run_loop())
            
            logger.info("Trading scheduler started")
            log_trading_event("scheduler_started", {"interval": self.interval_seconds}, "INFO")
            
        except Exception as e:
            logger.error("Failed to start scheduler", error=str(e))
            self.status = SchedulerStatus.ERROR
            raise
    
    async def stop(self):
        """Stop the scheduler."""
        try:
            if self.status == SchedulerStatus.STOPPED:
                logger.warning("Scheduler already stopped")
                return
            
            self._running = False
            self.status = SchedulerStatus.STOPPED
            
            # Cancel the task
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            # Calculate uptime
            self.metrics.uptime = time.time() - self.metrics.start_time
            
            logger.info("Trading scheduler stopped")
            log_trading_event("scheduler_stopped", {"uptime": self.metrics.uptime}, "INFO")
            
        except Exception as e:
            logger.error("Failed to stop scheduler", error=str(e))
            self.status = SchedulerStatus.ERROR
            raise
    
    async def pause(self):
        """Pause the scheduler."""
        try:
            if self.status == SchedulerStatus.RUNNING:
                self.status = SchedulerStatus.PAUSED
                self.strategy.pause_strategy()
                
                logger.info("Trading scheduler paused")
                log_trading_event("scheduler_paused", {}, "INFO")
            
        except Exception as e:
            logger.error("Failed to pause scheduler", error=str(e))
            self.status = SchedulerStatus.ERROR
            raise
    
    async def resume(self):
        """Resume the scheduler."""
        try:
            if self.status == SchedulerStatus.PAUSED:
                self.status = SchedulerStatus.RUNNING
                self.strategy.resume_strategy()
                
                logger.info("Trading scheduler resumed")
                log_trading_event("scheduler_resumed", {}, "INFO")
            
        except Exception as e:
            logger.error("Failed to resume scheduler", error=str(e))
            self.status = SchedulerStatus.ERROR
            raise
    
    async def _run_loop(self):
        """Main scheduler loop."""
        try:
            while self._running:
                cycle_start_time = time.time()
                
                try:
                    # Run strategy cycle
                    await self._run_strategy_cycle()
                    
                    # Update metrics
                    cycle_time = time.time() - cycle_start_time
                    self._update_metrics(cycle_time, success=True)
                    
                except Exception as e:
                    # Update metrics
                    cycle_time = time.time() - cycle_start_time
                    self._update_metrics(cycle_time, success=False)
                    
                    logger.error("Strategy cycle failed", error=str(e))
                    log_trading_event("strategy_cycle_failed", {"error": str(e)}, "ERROR")
                
                # Wait for next cycle
                await asyncio.sleep(self.interval_seconds)
                
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error("Scheduler loop error", error=str(e))
            self.status = SchedulerStatus.ERROR
            raise
    
    async def _run_strategy_cycle(self):
        """Run one cycle of the trading strategy."""
        try:
            # Run strategy in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.strategy.run_strategy_cycle)
            
        except Exception as e:
            logger.error("Failed to run strategy cycle", error=str(e))
            raise
    
    def _update_metrics(self, cycle_time: float, success: bool):
        """Update scheduler metrics."""
        try:
            self.metrics.total_cycles += 1
            self.metrics.last_cycle_time = cycle_time
            
            if success:
                self.metrics.successful_cycles += 1
            else:
                self.metrics.failed_cycles += 1
            
            # Update average cycle time
            if self.metrics.total_cycles > 0:
                total_time = self.metrics.avg_cycle_time * (self.metrics.total_cycles - 1) + cycle_time
                self.metrics.avg_cycle_time = total_time / self.metrics.total_cycles
            
            # Log performance metric
            log_performance_metric("scheduler_cycle_time", cycle_time, "seconds")
            
        except Exception as e:
            logger.error("Failed to update metrics", error=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with scheduler status
        """
        try:
            current_time = time.time()
            uptime = current_time - self.metrics.start_time if self.metrics.start_time > 0 else 0.0
            
            return {
                "status": self.status.value,
                "interval_seconds": self.interval_seconds,
                "running": self._running,
                "metrics": {
                    "total_cycles": self.metrics.total_cycles,
                    "successful_cycles": self.metrics.successful_cycles,
                    "failed_cycles": self.metrics.failed_cycles,
                    "success_rate": self.metrics.successful_cycles / self.metrics.total_cycles if self.metrics.total_cycles > 0 else 0.0,
                    "avg_cycle_time": self.metrics.avg_cycle_time,
                    "last_cycle_time": self.metrics.last_cycle_time,
                    "uptime": uptime,
                    "start_time": self.metrics.start_time
                },
                "strategy_status": self.strategy.get_strategy_status()
            }
            
        except Exception as e:
            logger.error("Failed to get scheduler status", error=str(e))
            return {"error": str(e)}
    
    def set_interval(self, interval_seconds: int):
        """
        Set the scheduling interval.
        
        Args:
            interval_seconds: New interval in seconds
        """
        try:
            if interval_seconds <= 0:
                raise ValueError("Interval must be positive")
            
            self.interval_seconds = interval_seconds
            
            logger.info("Scheduler interval updated", new_interval=interval_seconds)
            log_trading_event("scheduler_interval_updated", {"new_interval": interval_seconds}, "INFO")
            
        except Exception as e:
            logger.error("Failed to set interval", error=str(e))
            raise


# Global scheduler instance
_scheduler: Optional[TradingScheduler] = None


def get_scheduler() -> TradingScheduler:
    """
    Get the global scheduler instance.
    
    Returns:
        Scheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = TradingScheduler()
    
    return _scheduler


async def start_trading_bot():
    """Start the trading bot with scheduler."""
    try:
        scheduler = get_scheduler()
        await scheduler.start()
        
        logger.info("Trading bot started successfully")
        return scheduler
        
    except Exception as e:
        logger.error("Failed to start trading bot", error=str(e))
        raise


async def stop_trading_bot():
    """Stop the trading bot."""
    try:
        scheduler = get_scheduler()
        await scheduler.stop()
        
        logger.info("Trading bot stopped successfully")
        
    except Exception as e:
        logger.error("Failed to stop trading bot", error=str(e))
        raise
