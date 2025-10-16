#!/usr/bin/env python3
"""
Comprehensive PAPER_MODE demo script for the meme-coin trading bot.

This script provides a complete demonstration of the bot's functionality
in paper mode, including:
- Component initialization and testing
- Market monitoring simulation
- Token discovery and analysis
- Kraken compliance checking
- Signal processing and aggregation
- Trading simulation
- Performance monitoring
"""

import os
import sys
import time
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logging, get_logger
from src.config import TRADING_CONFIG, MLConfig
from src.security.wallet_manager import generate_and_encrypt_key, decrypt_key
from src.security.solana_wallet_manager import generate_and_encrypt_keypair, decrypt_keypair
from src.data.rpc_connector import get_rpc_connector
from src.data.solana_rpc_connector import get_solana_rpc_connector
from src.data.market_watcher import get_evm_market_watcher
from src.data.solana_market_watcher import get_solana_market_watcher
from src.security.contract_checker import get_kraken_audit_layer
from src.integrations.telegram_listener import get_telegram_listener
from src.trading.strategy import get_strategy
from src.trading.exchange import get_exchange_interface
from src.trading.risk_manager import get_risk_manager
from src.brain.rules_engine import get_rules_engine
from src.brain.ml_engine import get_ml_engine
from src.utils.database import initialize_database
from src.utils.scheduler import get_scheduler

logger = get_logger(__name__)


class PaperModeDemo:
    """
    Comprehensive PAPER_MODE demonstration system.
    
    Features:
    - Component initialization and testing
    - Market monitoring simulation
    - Token discovery and analysis
    - Kraken compliance checking
    - Signal processing and aggregation
    - Trading simulation
    - Performance monitoring
    """
    
    def __init__(self, duration_minutes: int = 5):
        """
        Initialize the paper mode demo.
        
        Args:
            duration_minutes: Demo duration in minutes
        """
        self.duration_minutes = duration_minutes
        self.start_time = time.time()
        self.end_time = self.start_time + (duration_minutes * 60)
        
        # Demo state
        self.is_running = False
        self.demo_data = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": duration_minutes,
            "components": {},
            "events": [],
            "trades": [],
            "signals": [],
            "compliance_checks": [],
            "performance_metrics": {}
        }
        
        # Components
        self.components = {}
        
        logger.info("Paper mode demo initialized", duration_minutes=duration_minutes)
    
    async def run_demo(self):
        """Run the complete paper mode demonstration."""
        try:
            logger.info("Starting paper mode demonstration")
            self.is_running = True
            
            # Phase 1: Initialize components
            await self._initialize_components()
            
            # Phase 2: Start monitoring
            await self._start_monitoring()
            
            # Phase 3: Simulate market activity
            await self._simulate_market_activity()
            
            # Phase 4: Process signals and trades
            await self._process_signals_and_trades()
            
            # Phase 5: Generate final report
            await self._generate_final_report()
            
            logger.info("Paper mode demonstration completed successfully")
            
        except Exception as e:
            logger.error("Paper mode demonstration failed", error=str(e))
            raise
        finally:
            self.is_running = False
    
    async def _initialize_components(self):
        """Initialize all bot components."""
        logger.info("Phase 1: Initializing components")
        
        try:
            # Initialize database
            logger.info("Initializing database...")
            if initialize_database():
                self.demo_data["components"]["database"] = "initialized"
                logger.info("✓ Database initialized")
            else:
                logger.error("✗ Database initialization failed")
                return
            
            # Initialize RPC connectors
            logger.info("Initializing RPC connectors...")
            try:
                rpc_connector = get_rpc_connector()
                self.components["rpc_connector"] = rpc_connector
                self.demo_data["components"]["rpc_connector"] = "initialized"
                logger.info("✓ EVM RPC connector initialized")
            except Exception as e:
                logger.warning("EVM RPC connector not available", error=str(e))
                self.demo_data["components"]["rpc_connector"] = "unavailable"
            
            try:
                solana_rpc_connector = await get_solana_rpc_connector()
                self.components["solana_rpc_connector"] = solana_rpc_connector
                self.demo_data["components"]["solana_rpc_connector"] = "initialized"
                logger.info("✓ Solana RPC connector initialized")
            except Exception as e:
                logger.warning("Solana RPC connector not available", error=str(e))
                self.demo_data["components"]["solana_rpc_connector"] = "unavailable"
            
            # Initialize market watchers
            logger.info("Initializing market watchers...")
            try:
                evm_market_watcher = get_evm_market_watcher(self.components.get("rpc_connector"))
                self.components["evm_market_watcher"] = evm_market_watcher
                self.demo_data["components"]["evm_market_watcher"] = "initialized"
                logger.info("✓ EVM market watcher initialized")
            except Exception as e:
                logger.warning("EVM market watcher not available", error=str(e))
                self.demo_data["components"]["evm_market_watcher"] = "unavailable"
            
            try:
                solana_market_watcher = get_solana_market_watcher(self.components.get("solana_rpc_connector"))
                self.components["solana_market_watcher"] = solana_market_watcher
                self.demo_data["components"]["solana_market_watcher"] = "initialized"
                logger.info("✓ Solana market watcher initialized")
            except Exception as e:
                logger.warning("Solana market watcher not available", error=str(e))
                self.demo_data["components"]["solana_market_watcher"] = "unavailable"
            
            # Initialize Kraken audit layer
            logger.info("Initializing Kraken audit layer...")
            try:
                kraken_audit_layer = get_kraken_audit_layer(
                    self.components.get("rpc_connector"),
                    self.components.get("solana_rpc_connector")
                )
                self.components["kraken_audit_layer"] = kraken_audit_layer
                self.demo_data["components"]["kraken_audit_layer"] = "initialized"
                logger.info("✓ Kraken audit layer initialized")
            except Exception as e:
                logger.warning("Kraken audit layer not available", error=str(e))
                self.demo_data["components"]["kraken_audit_layer"] = "unavailable"
            
            # Initialize Telegram listener
            logger.info("Initializing Telegram listener...")
            try:
                telegram_listener = get_telegram_listener()
                self.components["telegram_listener"] = telegram_listener
                self.demo_data["components"]["telegram_listener"] = "initialized"
                logger.info("✓ Telegram listener initialized")
            except Exception as e:
                logger.warning("Telegram listener not available", error=str(e))
                self.demo_data["components"]["telegram_listener"] = "unavailable"
            
            # Initialize trading components
            logger.info("Initializing trading components...")
            try:
                strategy = get_strategy()
                self.components["strategy"] = strategy
                self.demo_data["components"]["strategy"] = "initialized"
                logger.info("✓ Trading strategy initialized")
            except Exception as e:
                logger.warning("Trading strategy not available", error=str(e))
                self.demo_data["components"]["strategy"] = "unavailable"
            
            try:
                exchange = get_exchange_interface(paper_mode=True)
                self.components["exchange"] = exchange
                self.demo_data["components"]["exchange"] = "initialized"
                logger.info("✓ Exchange interface initialized")
            except Exception as e:
                logger.warning("Exchange interface not available", error=str(e))
                self.demo_data["components"]["exchange"] = "unavailable"
            
            try:
                risk_manager = get_risk_manager()
                self.components["risk_manager"] = risk_manager
                self.demo_data["components"]["risk_manager"] = "initialized"
                logger.info("✓ Risk manager initialized")
            except Exception as e:
                logger.warning("Risk manager not available", error=str(e))
                self.demo_data["components"]["risk_manager"] = "unavailable"
            
            # Initialize brain components
            logger.info("Initializing brain components...")
            try:
                rules_engine = get_rules_engine()
                self.components["rules_engine"] = rules_engine
                self.demo_data["components"]["rules_engine"] = "initialized"
                logger.info("✓ Rules engine initialized")
            except Exception as e:
                logger.warning("Rules engine not available", error=str(e))
                self.demo_data["components"]["rules_engine"] = "unavailable"
            
            try:
                ml_engine = get_ml_engine()
                self.components["ml_engine"] = ml_engine
                self.demo_data["components"]["ml_engine"] = "initialized"
                logger.info("✓ ML engine initialized")
            except Exception as e:
                logger.warning("ML engine not available", error=str(e))
                self.demo_data["components"]["ml_engine"] = "unavailable"
            
            # Initialize scheduler
            logger.info("Initializing scheduler...")
            try:
                scheduler = get_scheduler()
                self.components["scheduler"] = scheduler
                self.demo_data["components"]["scheduler"] = "initialized"
                logger.info("✓ Scheduler initialized")
            except Exception as e:
                logger.warning("Scheduler not available", error=str(e))
                self.demo_data["components"]["scheduler"] = "unavailable"
            
            logger.info("Phase 1 completed: All components initialized")
            
        except Exception as e:
            logger.error("Component initialization failed", error=str(e))
            raise
    
    async def _start_monitoring(self):
        """Start market monitoring."""
        logger.info("Phase 2: Starting market monitoring")
        
        try:
            # Start EVM market watcher
            if "evm_market_watcher" in self.components:
                await self.components["evm_market_watcher"].start_monitoring()
                logger.info("✓ EVM market watcher started")
            
            # Start Solana market watcher
            if "solana_market_watcher" in self.components:
                await self.components["solana_market_watcher"].start_monitoring()
                logger.info("✓ Solana market watcher started")
            
            # Start Telegram listener
            if "telegram_listener" in self.components:
                await self.components["telegram_listener"].start_monitoring()
                logger.info("✓ Telegram listener started")
            
            # Start scheduler
            if "scheduler" in self.components:
                await self.components["scheduler"].start()
                logger.info("✓ Scheduler started")
            
            logger.info("Phase 2 completed: Market monitoring started")
            
        except Exception as e:
            logger.error("Market monitoring startup failed", error=str(e))
            raise
    
    async def _simulate_market_activity(self):
        """Simulate market activity and token discovery."""
        logger.info("Phase 3: Simulating market activity")
        
        try:
            # Simulate token discoveries
            await self._simulate_token_discoveries()
            
            # Simulate Telegram signals
            await self._simulate_telegram_signals()
            
            # Simulate compliance checks
            await self._simulate_compliance_checks()
            
            logger.info("Phase 3 completed: Market activity simulated")
            
        except Exception as e:
            logger.error("Market activity simulation failed", error=str(e))
            raise
    
    async def _simulate_token_discoveries(self):
        """Simulate token discoveries."""
        logger.info("Simulating token discoveries...")
        
        # Mock token addresses for testing
        mock_tokens = [
            "0x1234567890123456789012345678901234567890",  # Ethereum
            "0x0987654321098765432109876543210987654321",  # Ethereum
            "So11111111111111111111111111111111111111112",  # Solana (WSOL)
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # Solana (USDC)
        ]
        
        for token in mock_tokens:
            # Simulate token discovery event
            discovery_event = {
                "timestamp": time.time(),
                "token_address": token,
                "chain": "ethereum" if token.startswith("0x") else "solana",
                "event_type": "token_discovered",
                "source": "market_watcher"
            }
            
            self.demo_data["events"].append(discovery_event)
            logger.info("Simulated token discovery", token=token)
            
            # Wait a bit between discoveries
            await asyncio.sleep(1)
    
    async def _simulate_telegram_signals(self):
        """Simulate Telegram signals."""
        logger.info("Simulating Telegram signals...")
        
        # Mock Telegram messages
        mock_messages = [
            {
                "text": "🚀 $PEPE to the moon! Diamond hands! 💎🙌",
                "tokens": ["PEPE"],
                "user_id": "user_001",
                "username": "crypto_trader_1"
            },
            {
                "text": "Just bought 0x1234567890123456789012345678901234567890 - this is going to pump!",
                "tokens": ["0x1234567890123456789012345678901234567890"],
                "user_id": "user_002",
                "username": "moon_boy_99"
            },
            {
                "text": "Solana token So11111111111111111111111111111111111111112 is the next big thing!",
                "tokens": ["So11111111111111111111111111111111111111112"],
                "user_id": "user_003",
                "username": "solana_whale"
            }
        ]
        
        for message in mock_messages:
            # Simulate Telegram signal
            signal_event = {
                "timestamp": time.time(),
                "message_id": f"msg_{int(time.time())}",
                "chat_id": "demo_chat",
                "user_id": message["user_id"],
                "username": message["username"],
                "text": message["text"],
                "tokens_mentioned": message["tokens"],
                "signal_strength": "moderate",
                "astroturf_score": 0.2,
                "event_type": "telegram_signal"
            }
            
            self.demo_data["signals"].append(signal_event)
            logger.info("Simulated Telegram signal", tokens=message["tokens"])
            
            # Wait a bit between signals
            await asyncio.sleep(2)
    
    async def _simulate_compliance_checks(self):
        """Simulate compliance checks."""
        logger.info("Simulating compliance checks...")
        
        if "kraken_audit_layer" not in self.components:
            logger.warning("Kraken audit layer not available, skipping compliance checks")
            return
        
        # Mock token addresses for compliance checking
        mock_tokens = [
            "0x1234567890123456789012345678901234567890",
            "0x0987654321098765432109876543210987654321",
            "So11111111111111111111111111111111111111112",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        ]
        
        for token in mock_tokens:
            try:
                chain = "ethereum" if token.startswith("0x") else "solana"
                
                # Perform compliance analysis
                analysis = await self.components["kraken_audit_layer"].analyze_token(token, chain)
                
                # Store compliance check result
                compliance_event = {
                    "timestamp": time.time(),
                    "token_address": token,
                    "chain": chain,
                    "compliance_score": analysis.compliance_score.overall_score,
                    "veto_reasons": [r.value for r in analysis.compliance_score.veto_reasons],
                    "warnings": analysis.compliance_score.warnings,
                    "is_compliant": self.components["kraken_audit_layer"].is_token_compliant(analysis),
                    "event_type": "compliance_check"
                }
                
                self.demo_data["compliance_checks"].append(compliance_event)
                logger.info("Simulated compliance check", token=token, score=analysis.compliance_score.overall_score)
                
                # Wait a bit between checks
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Compliance check failed", token=token, error=str(e))
    
    async def _process_signals_and_trades(self):
        """Process signals and simulate trades."""
        logger.info("Phase 4: Processing signals and simulating trades")
        
        try:
            # Process compliance-checked tokens
            compliant_tokens = [
                check for check in self.demo_data["compliance_checks"]
                if check["is_compliant"]
            ]
            
            logger.info("Processing compliant tokens", count=len(compliant_tokens))
            
            for compliance_check in compliant_tokens:
                token = compliance_check["token_address"]
                chain = compliance_check["chain"]
                
                # Simulate trading decision
                await self._simulate_trading_decision(token, chain, compliance_check)
                
                # Wait between trades
                await asyncio.sleep(3)
            
            logger.info("Phase 4 completed: Signals processed and trades simulated")
            
        except Exception as e:
            logger.error("Signal processing and trading simulation failed", error=str(e))
            raise
    
    async def _simulate_trading_decision(self, token: str, chain: str, compliance_check: Dict[str, Any]):
        """Simulate a trading decision."""
        try:
            # Check if we have signals for this token
            token_signals = [
                signal for signal in self.demo_data["signals"]
                if token in signal["tokens_mentioned"]
            ]
            
            if not token_signals:
                logger.info("No signals for token, skipping trade", token=token)
                return
            
            # Simulate trading decision based on signals and compliance
            signal_strength = sum(1 for signal in token_signals) / len(token_signals)
            compliance_score = compliance_check["compliance_score"]
            
            # Simple trading logic
            if signal_strength > 0.5 and compliance_score > 70:
                # Simulate buy order
                trade_event = {
                    "timestamp": time.time(),
                    "token_address": token,
                    "chain": chain,
                    "action": "buy",
                    "amount": 1000.0,  # Mock amount
                    "price": 0.001,  # Mock price
                    "signal_strength": signal_strength,
                    "compliance_score": compliance_score,
                    "event_type": "trade"
                }
                
                self.demo_data["trades"].append(trade_event)
                logger.info("Simulated buy trade", token=token, amount=1000.0)
                
                # Simulate position monitoring
                await self._simulate_position_monitoring(token, chain)
            
        except Exception as e:
            logger.error("Trading decision simulation failed", token=token, error=str(e))
    
    async def _simulate_position_monitoring(self, token: str, chain: str):
        """Simulate position monitoring."""
        try:
            # Simulate position updates
            for i in range(3):  # 3 updates
                await asyncio.sleep(2)
                
                # Simulate price movement
                price_change = (i + 1) * 0.001  # Mock price change
                
                position_event = {
                    "timestamp": time.time(),
                    "token_address": token,
                    "chain": chain,
                    "price_change": price_change,
                    "event_type": "position_update"
                }
                
                self.demo_data["events"].append(position_event)
                logger.info("Simulated position update", token=token, price_change=price_change)
            
        except Exception as e:
            logger.error("Position monitoring simulation failed", token=token, error=str(e))
    
    async def _generate_final_report(self):
        """Generate final demonstration report."""
        logger.info("Phase 5: Generating final report")
        
        try:
            # Calculate performance metrics
            self.demo_data["performance_metrics"] = {
                "total_events": len(self.demo_data["events"]),
                "total_signals": len(self.demo_data["signals"]),
                "total_compliance_checks": len(self.demo_data["compliance_checks"]),
                "total_trades": len(self.demo_data["trades"]),
                "compliant_tokens": len([c for c in self.demo_data["compliance_checks"] if c["is_compliant"]]),
                "non_compliant_tokens": len([c for c in self.demo_data["compliance_checks"] if not c["is_compliant"]]),
                "demo_duration": time.time() - self.start_time
            }
            
            # Save demo data
            await self._save_demo_data()
            
            # Print summary
            self._print_demo_summary()
            
            logger.info("Phase 5 completed: Final report generated")
            
        except Exception as e:
            logger.error("Final report generation failed", error=str(e))
            raise
    
    async def _save_demo_data(self):
        """Save demo data to files."""
        try:
            # Create dumps directory
            dumps_dir = Path("dumps")
            dumps_dir.mkdir(exist_ok=True)
            
            # Save demo summary
            summary_file = dumps_dir / "paperdemo_summary.json"
            with open(summary_file, "w") as f:
                json.dump(self.demo_data, f, indent=2, default=str)
            
            # Save detailed events
            events_file = dumps_dir / "paperdemo_events.json"
            with open(events_file, "w") as f:
                json.dump(self.demo_data["events"], f, indent=2, default=str)
            
            # Save trades
            trades_file = dumps_dir / "paperdemo_trades.json"
            with open(trades_file, "w") as f:
                json.dump(self.demo_data["trades"], f, indent=2, default=str)
            
            # Save signals
            signals_file = dumps_dir / "paperdemo_signals.json"
            with open(signals_file, "w") as f:
                json.dump(self.demo_data["signals"], f, indent=2, default=str)
            
            # Save compliance checks
            compliance_file = dumps_dir / "paperdemo_compliance.json"
            with open(compliance_file, "w") as f:
                json.dump(self.demo_data["compliance_checks"], f, indent=2, default=str)
            
            logger.info("Demo data saved to dumps/ directory")
            
        except Exception as e:
            logger.error("Failed to save demo data", error=str(e))
    
    def _print_demo_summary(self):
        """Print demo summary to console."""
        print("\n" + "="*80)
        print("PAPER MODE DEMONSTRATION SUMMARY")
        print("="*80)
        
        metrics = self.demo_data["performance_metrics"]
        
        print(f"Demo Duration: {metrics['demo_duration']:.2f} seconds")
        print(f"Total Events: {metrics['total_events']}")
        print(f"Total Signals: {metrics['total_signals']}")
        print(f"Total Compliance Checks: {metrics['total_compliance_checks']}")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Compliant Tokens: {metrics['compliant_tokens']}")
        print(f"Non-Compliant Tokens: {metrics['non_compliant_tokens']}")
        
        print("\nComponent Status:")
        for component, status in self.demo_data["components"].items():
            status_icon = "✓" if status == "initialized" else "✗"
            print(f"  {status_icon} {component}: {status}")
        
        print("\nFiles Generated:")
        print("  - dumps/paperdemo_summary.json")
        print("  - dumps/paperdemo_events.json")
        print("  - dumps/paperdemo_trades.json")
        print("  - dumps/paperdemo_signals.json")
        print("  - dumps/paperdemo_compliance.json")
        
        print("\n" + "="*80)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*80)
    
    async def stop_demo(self):
        """Stop the demonstration."""
        try:
            self.is_running = False
            
            # Stop all components
            if "scheduler" in self.components:
                await self.components["scheduler"].stop()
            
            if "evm_market_watcher" in self.components:
                await self.components["evm_market_watcher"].stop_monitoring()
            
            if "solana_market_watcher" in self.components:
                await self.components["solana_market_watcher"].stop_monitoring()
            
            if "telegram_listener" in self.components:
                await self.components["telegram_listener"].stop_monitoring()
            
            logger.info("Demo stopped")
            
        except Exception as e:
            logger.error("Failed to stop demo", error=str(e))


async def main():
    """Main function to run the paper mode demo."""
    try:
        # Setup logging
        setup_logging("INFO")
        
        # Get demo duration from command line
        duration_minutes = 5
        if len(sys.argv) > 1:
            try:
                duration_minutes = int(sys.argv[1])
            except ValueError:
                print("Invalid duration. Using default 5 minutes.")
        
        print(f"Starting PAPER_MODE demonstration for {duration_minutes} minutes...")
        print("This will simulate the complete bot functionality without real trading.")
        print("Press Ctrl+C to stop early.\n")
        
        # Create and run demo
        demo = PaperModeDemo(duration_minutes)
        
        try:
            await demo.run_demo()
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            await demo.stop_demo()
        
        print("\nDemo completed. Check the dumps/ directory for detailed results.")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
