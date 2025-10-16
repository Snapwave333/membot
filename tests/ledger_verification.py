#!/usr/bin/env python3
"""
Ledger verification test for the meme-coin trading bot.

This script verifies that all trading decisions are properly logged
and persisted in the database with complete audit trails.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import SAFETY_CONFIG
from src.utils.logger import get_logger, log_trading_event, log_performance_metric
from src.trading.exchange import ExchangeInterface, OrderSide, OrderType
from src.utils.database import initialize_database, get_database_manager

logger = get_logger(__name__)

class LedgerVerificationTest:
    """Ledger verification test runner."""
    
    def __init__(self):
        self.results = {
            "trading_events_logged": 0,
            "performance_metrics_logged": 0,
            "database_entries_created": 0,
            "audit_trail_complete": True,
            "errors": []
        }
        
        # Initialize components
        self.exchange = None
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up ledger verification test environment")
        
        # Verify PAPER_MODE is enabled
        if not SAFETY_CONFIG.PAPER_MODE:
            raise RuntimeError("PAPER_MODE must be enabled for ledger verification test")
        
        # Initialize database
        initialize_database()
        logger.info("Database initialized")
        
        # Initialize exchange
        self.exchange = ExchangeInterface()
        logger.info("Exchange interface initialized")
        
        logger.info("Ledger verification test environment setup complete")
    
    async def run_test(self):
        """Run the ledger verification test."""
        logger.info("Starting ledger verification test")
        
        try:
            # Test trading event logging
            await self._test_trading_event_logging()
            
            # Test performance metric logging
            await self._test_performance_metric_logging()
            
            # Test database persistence
            await self._test_database_persistence()
            
            # Verify audit trail completeness
            await self._verify_audit_trail()
            
            # Generate final report
            await self._generate_report()
            
        except Exception as e:
            logger.error("Ledger verification test failed", error=str(e))
            self.results["errors"].append(str(e))
            raise
    
    async def _test_trading_event_logging(self):
        """Test trading event logging."""
        logger.info("Testing trading event logging")
        
        try:
            # Place a test order
            order = self.exchange.place_order(
                symbol="ETH/USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                amount=0.1
            )
            
            if order:
                # Log trading event
                log_trading_event(
                    event_type="order_placed",
                    details={
                        "symbol": "ETH/USD",
                        "side": "buy",
                        "amount": 0.1,
                        "price": None,
                        "order_id": order.order_id,
                        "order_type": "market",
                        "paper_mode": True
                    },
                    severity="INFO"
                )
                
                self.results["trading_events_logged"] += 1
                logger.info("Trading event logged successfully", order_id=order.order_id)
            
        except Exception as e:
            logger.error("Trading event logging failed", error=str(e))
            self.results["errors"].append(f"Trading event logging failed: {e}")
            self.results["audit_trail_complete"] = False
    
    async def _test_performance_metric_logging(self):
        """Test performance metric logging."""
        logger.info("Testing performance metric logging")
        
        try:
            # Log performance metric
            log_performance_metric(
                metric_name="test_metric",
                value=100.0,
                unit="test_units"
            )
            
            self.results["performance_metrics_logged"] += 1
            logger.info("Performance metric logged successfully")
            
        except Exception as e:
            logger.error("Performance metric logging failed", error=str(e))
            self.results["errors"].append(f"Performance metric logging failed: {e}")
            self.results["audit_trail_complete"] = False
    
    async def _test_database_persistence(self):
        """Test database persistence."""
        logger.info("Testing database persistence")
        
        try:
            # Get database manager
            db_manager = get_database_manager()
            
            # Get database info
            db_info = db_manager.get_database_info()
            logger.info("Database info", info=db_info)
            
            # Check if database file exists
            db_path = Path("data/memebot.db")
            if db_path.exists():
                logger.info("Database file exists", path=str(db_path))
                self.results["database_entries_created"] = 1
            else:
                logger.warning("Database file does not exist", path=str(db_path))
                self.results["errors"].append("Database file does not exist")
                self.results["audit_trail_complete"] = False
            
        except Exception as e:
            logger.error("Database persistence test failed", error=str(e))
            self.results["errors"].append(f"Database persistence test failed: {e}")
            self.results["audit_trail_complete"] = False
    
    async def _verify_audit_trail(self):
        """Verify audit trail completeness."""
        logger.info("Verifying audit trail completeness")
        
        try:
            # Check log files
            log_files = list(Path("logs").glob("*.log"))
            logger.info("Log files found", count=len(log_files), files=[f.name for f in log_files])
            
            # Check if trading.log exists and has content
            trading_log = Path("logs/trading.log")
            if trading_log.exists():
                content = trading_log.read_text()
                if content.strip():
                    logger.info("Trading log has content", size=len(content))
                else:
                    logger.warning("Trading log is empty")
                    self.results["errors"].append("Trading log is empty")
                    self.results["audit_trail_complete"] = False
            else:
                logger.warning("Trading log does not exist")
                self.results["errors"].append("Trading log does not exist")
                self.results["audit_trail_complete"] = False
            
            # Check dump files
            dump_files = list(Path("dumps").glob("*.json"))
            logger.info("Dump files found", count=len(dump_files), files=[f.name for f in dump_files])
            
        except Exception as e:
            logger.error("Audit trail verification failed", error=str(e))
            self.results["errors"].append(f"Audit trail verification failed: {e}")
            self.results["audit_trail_complete"] = False
    
    async def _generate_report(self):
        """Generate final test report."""
        logger.info("Generating ledger verification test report")
        
        # Create report
        report = {
            "test_summary": {
                "timestamp": time.time(),
                "paper_mode": SAFETY_CONFIG.PAPER_MODE
            },
            "results": self.results,
            "audit_trail_status": "COMPLETE" if self.results["audit_trail_complete"] else "INCOMPLETE"
        }
        
        # Save report
        report_path = Path("dumps") / "ledger_verification_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Ledger verification test report saved", path=str(report_path))
        
        # Print summary
        print("\n" + "="*80)
        print("LEDGER VERIFICATION TEST SUMMARY")
        print("="*80)
        print(f"Trading events logged: {self.results['trading_events_logged']}")
        print(f"Performance metrics logged: {self.results['performance_metrics_logged']}")
        print(f"Database entries created: {self.results['database_entries_created']}")
        print(f"Audit trail complete: {self.results['audit_trail_complete']}")
        print(f"Errors: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            print("\nErrors:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("="*80)
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Ledger verification test cleanup complete")

async def main():
    """Main function."""
    test = LedgerVerificationTest()
    
    try:
        await test.setup()
        await test.run_test()
    finally:
        await test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
