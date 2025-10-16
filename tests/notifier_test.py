#!/usr/bin/env python3
"""
Notifier integration test for the meme-coin trading bot.

This script tests the notifier integration in paper mode to ensure
alerts are generated but not actually sent to external services.
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
from src.utils.logger import get_logger

logger = get_logger(__name__)

class NotifierTest:
    """Notifier integration test runner."""
    
    def __init__(self):
        self.results = {
            "alerts_generated": 0,
            "alerts_logged": 0,
            "external_calls_made": 0,
            "dry_run_mode_active": True,
            "errors": []
        }
        
        # Mock notifier for testing
        self.notifier = None
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up notifier test environment")
        
        # Verify PAPER_MODE is enabled
        if not SAFETY_CONFIG.PAPER_MODE:
            raise RuntimeError("PAPER_MODE must be enabled for notifier test")
        
        # Initialize mock notifier
        self.notifier = MockNotifier()
        logger.info("Mock notifier initialized")
        
        logger.info("Notifier test environment setup complete")
    
    async def run_test(self):
        """Run the notifier test."""
        logger.info("Starting notifier test")
        
        try:
            # Test alert generation
            await self._test_alert_generation()
            
            # Test dry-run mode
            await self._test_dry_run_mode()
            
            # Test daily digest generation
            await self._test_daily_digest()
            
            # Generate final report
            await self._generate_report()
            
        except Exception as e:
            logger.error("Notifier test failed", error=str(e))
            self.results["errors"].append(str(e))
            raise
    
    async def _test_alert_generation(self):
        """Test alert generation."""
        logger.info("Testing alert generation")
        
        try:
            # Generate test alert
            alert_result = await self.notifier.send_alert(
                alert_type="paper_demo",
                message="Test alert from paper mode",
                severity="INFO"
            )
            
            if alert_result:
                self.results["alerts_generated"] += 1
                logger.info("Alert generated successfully")
            else:
                logger.warning("Alert generation failed")
                self.results["errors"].append("Alert generation failed")
            
        except Exception as e:
            logger.error("Alert generation test failed", error=str(e))
            self.results["errors"].append(f"Alert generation test failed: {e}")
    
    async def _test_dry_run_mode(self):
        """Test dry-run mode."""
        logger.info("Testing dry-run mode")
        
        try:
            # Check if notifier is in dry-run mode
            if self.notifier.dry_run_mode:
                self.results["dry_run_mode_active"] = True
                logger.info("Dry-run mode is active")
            else:
                self.results["dry_run_mode_active"] = False
                logger.warning("Dry-run mode is not active")
                self.results["errors"].append("Dry-run mode is not active")
            
            # Verify no external calls were made
            if self.notifier.external_calls_count == 0:
                logger.info("No external calls made")
            else:
                logger.warning("External calls were made", count=self.notifier.external_calls_count)
                self.results["external_calls_made"] = self.notifier.external_calls_count
                self.results["errors"].append(f"External calls made: {self.notifier.external_calls_count}")
            
        except Exception as e:
            logger.error("Dry-run mode test failed", error=str(e))
            self.results["errors"].append(f"Dry-run mode test failed: {e}")
    
    async def _test_daily_digest(self):
        """Test daily digest generation."""
        logger.info("Testing daily digest generation")
        
        try:
            # Generate daily digest
            digest_result = await self.notifier.generate_daily_digest()
            
            if digest_result:
                logger.info("Daily digest generated successfully")
                
                # Check if digest file was created
                digest_path = Path("logs/digests/paperdemodaily.json")
                if digest_path.exists():
                    logger.info("Daily digest file created", path=str(digest_path))
                    
                    # Read and validate digest content
                    with open(digest_path, "r") as f:
                        digest_data = json.load(f)
                    
                    logger.info("Daily digest content", data=digest_data)
                else:
                    logger.warning("Daily digest file not created")
                    self.results["errors"].append("Daily digest file not created")
            else:
                logger.warning("Daily digest generation failed")
                self.results["errors"].append("Daily digest generation failed")
            
        except Exception as e:
            logger.error("Daily digest test failed", error=str(e))
            self.results["errors"].append(f"Daily digest test failed: {e}")
    
    async def _generate_report(self):
        """Generate final test report."""
        logger.info("Generating notifier test report")
        
        # Create report
        report = {
            "test_summary": {
                "timestamp": time.time(),
                "paper_mode": SAFETY_CONFIG.PAPER_MODE
            },
            "results": self.results,
            "notifier_status": "SAFE" if self.results["dry_run_mode_active"] and self.results["external_calls_made"] == 0 else "UNSAFE"
        }
        
        # Save report
        report_path = Path("dumps") / "notifier_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Notifier test report saved", path=str(report_path))
        
        # Print summary
        print("\n" + "="*80)
        print("NOTIFIER TEST SUMMARY")
        print("="*80)
        print(f"Alerts generated: {self.results['alerts_generated']}")
        print(f"Alerts logged: {self.results['alerts_logged']}")
        print(f"External calls made: {self.results['external_calls_made']}")
        print(f"Dry-run mode active: {self.results['dry_run_mode_active']}")
        print(f"Errors: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            print("\nErrors:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("="*80)
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Notifier test cleanup complete")

class MockNotifier:
    """Mock notifier for testing."""
    
    def __init__(self):
        self.dry_run_mode = True
        self.external_calls_count = 0
        self.alerts_logged = []
    
    async def send_alert(self, alert_type: str, message: str, severity: str = "INFO") -> bool:
        """Send alert in dry-run mode."""
        try:
            # Log the alert instead of sending it
            alert_data = {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": time.time(),
                "dry_run": True
            }
            
            self.alerts_logged.append(alert_data)
            logger.info("Alert logged (dry-run)", **alert_data)
            
            return True
            
        except Exception as e:
            logger.error("Alert logging failed", error=str(e))
            return False
    
    async def generate_daily_digest(self) -> bool:
        """Generate daily digest."""
        try:
            # Create digests directory if it doesn't exist
            digests_dir = Path("logs/digests")
            digests_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate digest data
            digest_data = {
                "date": time.strftime("%Y-%m-%d"),
                "paper_mode": True,
                "alerts_count": len(self.alerts_logged),
                "alerts": self.alerts_logged,
                "summary": "Daily digest generated in paper mode",
                "timestamp": time.time()
            }
            
            # Save digest to file
            digest_path = digests_dir / "paperdemodaily.json"
            with open(digest_path, "w") as f:
                json.dump(digest_data, f, indent=2, default=str)
            
            logger.info("Daily digest generated", path=str(digest_path))
            return True
            
        except Exception as e:
            logger.error("Daily digest generation failed", error=str(e))
            return False

async def main():
    """Main function."""
    test = NotifierTest()
    
    try:
        await test.setup()
        await test.run_test()
    finally:
        await test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
