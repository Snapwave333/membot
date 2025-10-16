#!/usr/bin/env python3
"""
Test script for the meme-coin trading bot.

This script provides a simple way to test the bot functionality
without running the full application.
"""

import sys
import time
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logging
from src.trading.strategy import get_strategy
from src.trading.exchange import get_exchange_interface
from src.trading.risk_manager import get_risk_manager
from src.brain.rules_engine import get_rules_engine
from src.brain.ml_engine import get_ml_engine
from src.utils.database import initialize_database


def test_components():
    """Test all bot components."""
    print("Testing bot components...")
    
    try:
        # Test database initialization
        print("1. Testing database initialization...")
        if initialize_database():
            print("   OK Database initialized successfully")
        else:
            print("   X Database initialization failed")
            return False
        
        # Test risk manager
        print("2. Testing risk manager...")
        risk_manager = get_risk_manager()
        risk_metrics = risk_manager.get_risk_metrics()
        print(f"   OK Risk manager initialized: {risk_metrics.risk_level.value}")
        
        # Test exchange interface
        print("3. Testing exchange interface...")
        exchange = get_exchange_interface(paper_mode=True)
        balances = exchange.get_all_balances()
        print(f"   OK Exchange interface initialized: {len(balances)} balances")
        
        # Test rules engine
        print("4. Testing rules engine...")
        rules_engine = get_rules_engine()
        rule_stats = rules_engine.get_rule_statistics()
        print(f"   OK Rules engine initialized: {rule_stats['total_evaluations']} evaluations")
        
        # Test ML engine
        print("5. Testing ML engine...")
        ml_engine = get_ml_engine()
        ml_stats = ml_engine.get_prediction_statistics()
        print(f"   OK ML engine initialized: {ml_stats['total_predictions']} predictions")
        
        # Test strategy
        print("6. Testing trading strategy...")
        strategy = get_strategy()
        strategy_status = strategy.get_strategy_status()
        print(f"   OK Strategy initialized: {strategy_status['status']}")
        
        return True
        
    except Exception as e:
        print(f"   X Component test failed: {e}")
        return False


def test_trading_simulation():
    """Test a simple trading simulation."""
    print("\nTesting trading simulation...")
    
    try:
        # Get components
        strategy = get_strategy()
        exchange = get_exchange_interface(paper_mode=True)
        risk_manager = get_risk_manager()
        
        # Set initial portfolio value
        risk_manager.portfolio_value = 10000.0
        
        print(f"Initial portfolio value: ${risk_manager.portfolio_value:,.2f}")
        print(f"Initial balances: {exchange.get_all_balances()}")
        
        # Run a few strategy cycles
        for i in range(3):
            print(f"\nCycle {i+1}:")
            
            # Analyze market for each symbol
            for symbol in ["ETH", "BTC", "DOGE"]:
                signal = strategy.analyze_market(symbol)
                if signal:
                    print(f"   {symbol}: {signal.action} (confidence: {signal.confidence:.2f})")
                    
                    # Execute signal if confidence is high enough
                    if signal.confidence >= 0.7:
                        success = strategy.execute_signal(signal)
                        if success:
                            print(f"   OK Signal executed for {symbol}")
                        else:
                            print(f"   X Signal execution failed for {symbol}")
            
            # Update positions
            strategy.update_positions()
            
            # Get updated metrics
            risk_metrics = risk_manager.get_risk_metrics()
            print(f"   Portfolio P&L: ${risk_metrics.total_pnl:,.2f}")
            print(f"   Active positions: {risk_metrics.position_count}")
            
            time.sleep(1)  # Brief pause between cycles
        
        print(f"\nFinal balances: {exchange.get_all_balances()}")
        print(f"Final portfolio value: ${risk_manager.portfolio_value:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"Trading simulation failed: {e}")
        return False


async def test_scheduler():
    """Test the scheduler."""
    print("\nTesting scheduler...")
    
    try:
        from src.utils.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        # Start scheduler
        print("Starting scheduler...")
        await scheduler.start()
        
        # Let it run for a few seconds
        print("Running scheduler for 5 seconds...")
        await asyncio.sleep(5)
        
        # Get status
        status = scheduler.get_status()
        print(f"Scheduler status: {status['status']}")
        print(f"Total cycles: {status['metrics']['total_cycles']}")
        print(f"Success rate: {status['metrics']['success_rate']:.2%}")
        
        # Stop scheduler
        print("Stopping scheduler...")
        await scheduler.stop()
        
        print("OK Scheduler test completed")
        return True
        
    except Exception as e:
        print(f"Scheduler test failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("MEME-COIN TRADING BOT - COMPONENT TESTS")
    print("=" * 60)
    
    # Setup logging
    setup_logging("INFO")
    
    # Test components
    if not test_components():
        print("\nX Component tests failed")
        return False
    
    # Test trading simulation
    if not test_trading_simulation():
        print("\nX Trading simulation failed")
        return False
    
    # Test scheduler
    try:
        asyncio.run(test_scheduler())
    except Exception as e:
        print(f"\nX Scheduler test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("OK ALL TESTS PASSED")
    print("=" * 60)
    print("\nThe bot is ready for use!")
    print("Run 'python main.py --paper-mode' to start the bot.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
