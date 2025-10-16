#!/usr/bin/env python3
"""
Integration test for the meme-coin trading bot.

This script runs a comprehensive end-to-end test in PAPER_MODE
to verify all components work together correctly.
"""

import asyncio
import json
import os
import sys
import time
import signal
from pathlib import Path
from typing import Dict, Any, List
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import TRADING_CONFIG, SAFETY_CONFIG
from src.utils.database import init_database, get_session
from src.utils.logger import get_logger, log_trading_event, log_performance_metric
from src.data.rpc_connector import RPCConnector
from src.data.market_watcher import MarketWatcher
from src.security.contract_checker import KrakenAuditLayer
from src.brain.rules_engine import RulesEngine
from src.brain.ml_engine import MLEngine
from src.trading.exchange import ExchangeInterface
from src.trading.strategy import TradingStrategy
from src.utils.scheduler import TradingScheduler

logger = get_logger(__name__)

class IntegrationTest:
    """Integration test runner."""
    
    def __init__(self, duration_minutes: int = 10):
        self.duration_minutes = duration_minutes
        self.start_time = time.time()
        self.end_time = self.start_time + (duration_minutes * 60)
        self.results = {
            "tokens_detected": 0,
            "tokens_analyzed": 0,
            "tokens_passed_checks": 0,
            "signals_generated": 0,
            "trades_executed": 0,
            "trades_successful": 0,
            "total_pnl_usd": 0.0,
            "total_gas_cost_eth": 0.0,
            "errors": []
        }
        
        # Initialize components
        self.rpc_connector = None
        self.market_watcher = None
        self.contract_checker = None
        self.rules_engine = None
        self.ml_engine = None
        self.exchange = None
        self.strategy = None
        self.scheduler = None
        
        # Test data
        self.detected_tokens = []
        self.analyzed_tokens = []
        self.generated_signals = []
        self.executed_trades = []
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up integration test environment")
        
        # Verify PAPER_MODE is enabled
        if not SAFETY_CONFIG.PAPER_MODE:
            raise RuntimeError("PAPER_MODE must be enabled for integration test")
        
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize RPC connector
        self.rpc_connector = RPCConnector()
        await self.rpc_connector.connect()
        logger.info("RPC connector initialized")
        
        # Initialize market watcher
        self.market_watcher = MarketWatcher(self.rpc_connector)
        await self.market_watcher.start()
        logger.info("Market watcher started")
        
        # Initialize contract checker
        self.contract_checker = KrakenAuditLayer(self.rpc_connector)
        logger.info("Contract checker initialized")
        
        # Initialize rules engine
        self.rules_engine = RulesEngine()
        logger.info("Rules engine initialized")
        
        # Initialize ML engine
        self.ml_engine = MLEngine()
        logger.info("ML engine initialized")
        
        # Initialize exchange
        self.exchange = ExchangeInterface()
        logger.info("Exchange interface initialized")
        
        # Initialize strategy
        self.strategy = TradingStrategy(
            self.exchange,
            self.rules_engine,
            self.ml_engine,
            self.contract_checker
        )
        logger.info("Trading strategy initialized")
        
        # Initialize scheduler
        self.scheduler = TradingScheduler(self.strategy)
        logger.info("Trading scheduler initialized")
        
        logger.info("Integration test environment setup complete")
    
    async def run_test(self):
        """Run the integration test."""
        logger.info("Starting integration test", duration_minutes=self.duration_minutes)
        
        try:
            # Start scheduler
            await self.scheduler.start()
            
            # Run test loop
            while time.time() < self.end_time:
                await self._test_cycle()
                await asyncio.sleep(10)  # 10 second cycles
            
            # Stop scheduler
            await self.scheduler.stop()
            
            # Generate final report
            await self._generate_report()
            
        except Exception as e:
            logger.error("Integration test failed", error=str(e))
            self.results["errors"].append(str(e))
            raise
    
    async def _test_cycle(self):
        """Run a single test cycle."""
        try:
            # Check for new tokens
            new_tokens = await self.market_watcher.get_new_tokens()
            if new_tokens:
                self.results["tokens_detected"] += len(new_tokens)
                self.detected_tokens.extend(new_tokens)
                logger.info("New tokens detected", count=len(new_tokens))
            
            # Analyze tokens
            for token_address in new_tokens:
                try:
                    analysis = await self.contract_checker.analyze_token(token_address)
                    self.results["tokens_analyzed"] += 1
                    self.analyzed_tokens.append(analysis)
                    
                    if analysis.overall_score >= 70.0:  # Kraken compliance threshold
                        self.results["tokens_passed_checks"] += 1
                        logger.info("Token passed compliance check", 
                                  token=token_address, score=analysis.overall_score)
                    else:
                        logger.info("Token failed compliance check", 
                                  token=token_address, score=analysis.overall_score)
                
                except Exception as e:
                    logger.error("Token analysis failed", token=token_address, error=str(e))
                    self.results["errors"].append(f"Analysis failed for {token_address}: {e}")
            
            # Generate signals
            for analysis in self.analyzed_tokens:
                if analysis.overall_score >= 70.0:
                    try:
                        signal = await self.strategy.generate_signal(analysis)
                        if signal:
                            self.results["signals_generated"] += 1
                            self.generated_signals.append(signal)
                            logger.info("Signal generated", token=analysis.token_address)
                    except Exception as e:
                        logger.error("Signal generation failed", token=analysis.token_address, error=str(e))
                        self.results["errors"].append(f"Signal generation failed for {analysis.token_address}: {e}")
            
            # Execute trades
            for signal in self.generated_signals:
                try:
                    trade = await self.strategy.execute_trade(signal)
                    if trade:
                        self.results["trades_executed"] += 1
                        self.executed_trades.append(trade)
                        
                        if trade.status == "FILLED":
                            self.results["trades_successful"] += 1
                            self.results["total_pnl_usd"] += trade.pnl_usd
                            self.results["total_gas_cost_eth"] += trade.gas_cost_eth
                            logger.info("Trade executed successfully", 
                                      token=signal.token_address, pnl=trade.pnl_usd)
                        else:
                            logger.info("Trade failed", token=signal.token_address, status=trade.status)
                
                except Exception as e:
                    logger.error("Trade execution failed", token=signal.token_address, error=str(e))
                    self.results["errors"].append(f"Trade execution failed for {signal.token_address}: {e}")
            
            # Log performance metrics
            await log_performance_metric("integration_test_cycle", time.time() - self.start_time, "seconds")
            
        except Exception as e:
            logger.error("Test cycle failed", error=str(e))
            self.results["errors"].append(f"Test cycle failed: {e}")
    
    async def _generate_report(self):
        """Generate final test report."""
        logger.info("Generating integration test report")
        
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
            "detected_tokens": [token for token in self.detected_tokens],
            "analyzed_tokens": [analysis.token_address for analysis in self.analyzed_tokens],
            "generated_signals": [signal.token_address for signal in self.generated_signals],
            "executed_trades": [trade.token_address for trade in self.executed_trades],
            "errors": self.results["errors"]
        }
        
        # Save report
        report_path = Path("dumps") / "integration_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Integration test report saved", path=str(report_path))
        
        # Print summary
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Duration: {self.duration_minutes} minutes")
        print(f"Tokens detected: {self.results['tokens_detected']}")
        print(f"Tokens analyzed: {self.results['tokens_analyzed']}")
        print(f"Tokens passed checks: {self.results['tokens_passed_checks']}")
        print(f"Signals generated: {self.results['signals_generated']}")
        print(f"Trades executed: {self.results['trades_executed']}")
        print(f"Trades successful: {self.results['trades_successful']}")
        print(f"Total PnL (USD): ${self.results['total_pnl_usd']:.2f}")
        print(f"Total gas cost (ETH): {self.results['total_gas_cost_eth']:.6f}")
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
        logger.info("Cleaning up integration test environment")
        
        if self.scheduler:
            await self.scheduler.stop()
        
        if self.market_watcher:
            await self.market_watcher.stop()
        
        if self.rpc_connector:
            await self.rpc_connector.disconnect()
        
        logger.info("Integration test cleanup complete")

async def main():
    """Main function."""
    duration_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    test = IntegrationTest(duration_minutes)
    
    try:
        await test.setup()
        await test.run_test()
    finally:
        await test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
