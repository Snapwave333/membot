#!/usr/bin/env python3
"""
Simple integration test for the meme-coin trading bot.

This script runs a basic end-to-end test in PAPER_MODE
to verify core components work together.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import SAFETY_CONFIG
from src.utils.logger import get_logger
from src.trading.exchange import ExchangeInterface, OrderSide, OrderType

logger = get_logger(__name__)

class SimpleIntegrationTest:
    """Simple integration test runner."""
    
    def __init__(self, duration_minutes: int = 5):
        self.duration_minutes = duration_minutes
        self.start_time = time.time()
        self.end_time = self.start_time + (duration_minutes * 60)
        self.results = {
            "trades_executed": 0,
            "trades_successful": 0,
            "total_pnl_usd": 0.0,
            "errors": []
        }
        
        # Initialize components
        self.exchange = None
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up simple integration test environment")
        
        # Verify PAPER_MODE is enabled
        if not SAFETY_CONFIG.PAPER_MODE:
            raise RuntimeError("PAPER_MODE must be enabled for integration test")
        
        # Initialize exchange
        self.exchange = ExchangeInterface()
        logger.info("Exchange interface initialized")
        
        logger.info("Simple integration test environment setup complete")
    
    async def run_test(self):
        """Run the integration test."""
        logger.info("Starting simple integration test", duration_minutes=self.duration_minutes)
        
        try:
            # Run test loop
            while time.time() < self.end_time:
                await self._test_cycle()
                await asyncio.sleep(30)  # 30 second cycles
            
            # Generate final report
            await self._generate_report()
            
        except Exception as e:
            logger.error("Simple integration test failed", error=str(e))
            self.results["errors"].append(str(e))
            raise
    
    async def _test_cycle(self):
        """Run a single test cycle."""
        try:
            # Get initial balances
            initial_eth = self.exchange.get_balance("ETH")
            initial_usd = self.exchange.get_balance("USD")
            
            logger.info("Initial balances", eth=initial_eth, usd=initial_usd)
            
            # Place a test buy order
            buy_order = self.exchange.place_order(
                symbol="ETH/USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                amount=0.1  # Buy 0.1 ETH
            )
            
            if buy_order:
                self.results["trades_executed"] += 1
                if buy_order.status.value == "filled":
                    self.results["trades_successful"] += 1
                    logger.info("Buy order executed successfully", order_id=buy_order.order_id)
                else:
                    logger.info("Buy order failed", order_id=buy_order.order_id, status=buy_order.status)
            
            # Place a test sell order
            sell_order = self.exchange.place_order(
                symbol="ETH/USD",
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=0.05  # Sell 0.05 ETH
            )
            
            if sell_order:
                self.results["trades_executed"] += 1
                if sell_order.status.value == "filled":
                    self.results["trades_successful"] += 1
                    logger.info("Sell order executed successfully", order_id=sell_order.order_id)
                else:
                    logger.info("Sell order failed", order_id=sell_order.order_id, status=sell_order.status)
            
            # Get final balances
            final_eth = self.exchange.get_balance("ETH")
            final_usd = self.exchange.get_balance("USD")
            
            logger.info("Final balances", eth=final_eth, usd=final_usd)
            
            # Calculate PnL
            pnl_usd = final_usd - initial_usd
            self.results["total_pnl_usd"] += pnl_usd
            
            logger.info("Cycle completed", pnl_usd=pnl_usd)
            
        except Exception as e:
            logger.error("Test cycle failed", error=str(e))
            self.results["errors"].append(f"Test cycle failed: {e}")
    
    async def _generate_report(self):
        """Generate final test report."""
        logger.info("Generating simple integration test report")
        
        # Calculate final balances
        final_eth_balance = self.exchange.get_balance("ETH")
        final_usd_balance = self.exchange.get_balance("USD")
        
        # Create report
        report = {
            "test_summary": {
                "duration_minutes": self.duration_minutes,
                "start_time": self.start_time,
                "end_time": time.time(),
                "paper_mode": SAFETY_CONFIG.PAPER_MODE
            },
            "results": self.results,
            "final_balances": {
                "eth": final_eth_balance,
                "usd": final_usd_balance
            },
            "errors": self.results["errors"]
        }
        
        # Save report
        report_path = Path("dumps") / "simple_integration_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Simple integration test report saved", path=str(report_path))
        
        # Print summary
        print("\n" + "="*80)
        print("SIMPLE INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Duration: {self.duration_minutes} minutes")
        print(f"Trades executed: {self.results['trades_executed']}")
        print(f"Trades successful: {self.results['trades_successful']}")
        print(f"Total PnL (USD): ${self.results['total_pnl_usd']:.2f}")
        print(f"Final ETH balance: {final_eth_balance:.6f}")
        print(f"Final USD balance: ${final_usd_balance:.2f}")
        print(f"Errors: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            print("\nErrors:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("="*80)
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Simple integration test cleanup complete")

async def main():
    """Main function."""
    duration_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    test = SimpleIntegrationTest(duration_minutes)
    
    try:
        await test.setup()
        await test.run_test()
    finally:
        await test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
