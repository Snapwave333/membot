#!/usr/bin/env python3
"""
Security validation test for the meme-coin trading bot.

This script validates safety and security measures to ensure
no real transactions occur and proper security controls are in place.
"""

import asyncio
import json
import os
import sys
import stat
import time
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import SAFETY_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SecurityValidationTest:
    """Security validation test runner."""
    
    def __init__(self):
        self.results = {
            "paper_mode_enabled": False,
            "real_transactions_blocked": True,
            "key_encryption_verified": False,
            "file_permissions_secure": False,
            "no_key_logging": True,
            "security_controls_active": True,
            "errors": []
        }
        
        # Security checks
        self.security_issues = []
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up security validation test environment")
        
        logger.info("Security validation test environment setup complete")
    
    async def run_test(self):
        """Run the security validation test."""
        logger.info("Starting security validation test")
        
        try:
            # Test paper mode enforcement
            await self._test_paper_mode_enforcement()
            
            # Test real transaction blocking
            await self._test_real_transaction_blocking()
            
            # Test key encryption
            await self._test_key_encryption()
            
            # Test file permissions
            await self._test_file_permissions()
            
            # Test key logging prevention
            await self._test_key_logging_prevention()
            
            # Test security controls
            await self._test_security_controls()
            
            # Generate final report
            await self._generate_report()
            
        except Exception as e:
            logger.error("Security validation test failed", error=str(e))
            self.results["errors"].append(str(e))
            raise
    
    async def _test_paper_mode_enforcement(self):
        """Test paper mode enforcement."""
        logger.info("Testing paper mode enforcement")
        
        try:
            if SAFETY_CONFIG.PAPER_MODE:
                self.results["paper_mode_enabled"] = True
                logger.info("Paper mode is enabled")
            else:
                self.results["paper_mode_enabled"] = False
                self.results["errors"].append("Paper mode is not enabled")
                logger.error("Paper mode is not enabled")
            
        except Exception as e:
            logger.error("Paper mode enforcement test failed", error=str(e))
            self.results["errors"].append(f"Paper mode enforcement test failed: {e}")
    
    async def _test_real_transaction_blocking(self):
        """Test real transaction blocking."""
        logger.info("Testing real transaction blocking")
        
        try:
            # Check if any real transaction attempts were made
            # This would be verified by scanning logs for eth_sendRawTransaction calls
            log_files = list(Path("logs").glob("*.log"))
            
            real_transaction_attempts = 0
            for log_file in log_files:
                if log_file.exists():
                    content = log_file.read_text()
                    # Look for signs of real transaction attempts
                    if "eth_sendRawTransaction" in content.lower():
                        real_transaction_attempts += 1
                        logger.warning("Real transaction attempt found", file=str(log_file))
            
            if real_transaction_attempts == 0:
                self.results["real_transactions_blocked"] = True
                logger.info("No real transaction attempts found")
            else:
                self.results["real_transactions_blocked"] = False
                self.results["errors"].append(f"Real transaction attempts found: {real_transaction_attempts}")
                logger.error("Real transaction attempts found", count=real_transaction_attempts)
            
        except Exception as e:
            logger.error("Real transaction blocking test failed", error=str(e))
            self.results["errors"].append(f"Real transaction blocking test failed: {e}")
    
    async def _test_key_encryption(self):
        """Test key encryption."""
        logger.info("Testing key encryption")
        
        try:
            # Check if encrypted key file exists
            encrypted_key_path = Path(".encrypted_key")
            if encrypted_key_path.exists():
                # Check file permissions
                file_stat = encrypted_key_path.stat()
                file_mode = oct(file_stat.st_mode)[-3:]
                
                if file_mode == "600":
                    self.results["key_encryption_verified"] = True
                    logger.info("Encrypted key file exists with correct permissions", mode=file_mode)
                else:
                    self.results["key_encryption_verified"] = False
                    self.results["errors"].append(f"Encrypted key file has incorrect permissions: {file_mode}")
                    logger.error("Encrypted key file has incorrect permissions", mode=file_mode)
            else:
                self.results["key_encryption_verified"] = False
                self.results["errors"].append("Encrypted key file does not exist")
                logger.error("Encrypted key file does not exist")
            
        except Exception as e:
            logger.error("Key encryption test failed", error=str(e))
            self.results["errors"].append(f"Key encryption test failed: {e}")
    
    async def _test_file_permissions(self):
        """Test file permissions."""
        logger.info("Testing file permissions")
        
        try:
            # Check critical file permissions
            critical_files = [
                ".encrypted_key",
                "src/config.py",
                ".env"
            ]
            
            secure_files = 0
            total_files = 0
            
            for file_path in critical_files:
                path = Path(file_path)
                if path.exists():
                    total_files += 1
                    file_stat = path.stat()
                    file_mode = oct(file_stat.st_mode)[-3:]
                    
                    # Check if file has restrictive permissions
                    if file_mode in ["600", "700"]:
                        secure_files += 1
                        logger.info("File has secure permissions", file=file_path, mode=file_mode)
                    else:
                        logger.warning("File has insecure permissions", file=file_path, mode=file_mode)
                        self.results["errors"].append(f"File {file_path} has insecure permissions: {file_mode}")
            
            if secure_files == total_files and total_files > 0:
                self.results["file_permissions_secure"] = True
                logger.info("All critical files have secure permissions")
            else:
                self.results["file_permissions_secure"] = False
                logger.error("Some critical files have insecure permissions", secure=secure_files, total=total_files)
            
        except Exception as e:
            logger.error("File permissions test failed", error=str(e))
            self.results["errors"].append(f"File permissions test failed: {e}")
    
    async def _test_key_logging_prevention(self):
        """Test key logging prevention."""
        logger.info("Testing key logging prevention")
        
        try:
            # Check if private keys were logged to console or files
            log_files = list(Path("logs").glob("*.log"))
            
            key_logging_incidents = 0
            for log_file in log_files:
                if log_file.exists():
                    content = log_file.read_text()
                    # Look for signs of key logging
                    if "private_key" in content.lower() or "0x" in content:
                        # Check if it's a real private key (64 hex chars)
                        import re
                        hex_pattern = r'0x[a-fA-F0-9]{64}'
                        matches = re.findall(hex_pattern, content)
                        if matches:
                            key_logging_incidents += len(matches)
                            logger.warning("Potential key logging found", file=str(log_file), count=len(matches))
            
            if key_logging_incidents == 0:
                self.results["no_key_logging"] = True
                logger.info("No key logging incidents found")
            else:
                self.results["no_key_logging"] = False
                self.results["errors"].append(f"Key logging incidents found: {key_logging_incidents}")
                logger.error("Key logging incidents found", count=key_logging_incidents)
            
        except Exception as e:
            logger.error("Key logging prevention test failed", error=str(e))
            self.results["errors"].append(f"Key logging prevention test failed: {e}")
    
    async def _test_security_controls(self):
        """Test security controls."""
        logger.info("Testing security controls")
        
        try:
            # Check if security controls are active
            security_controls = [
                ("PAPER_MODE", SAFETY_CONFIG.PAPER_MODE),
                ("KILL_SWITCH_FILE_PATH", hasattr(SAFETY_CONFIG, "KILL_SWITCH_FILE_PATH")),
                ("MAX_DRAWDOWN_PCT", hasattr(SAFETY_CONFIG, "MAX_DRAWDOWN_PCT")),
                ("PROFIT_SWEEP_THRESHOLD", hasattr(SAFETY_CONFIG, "PROFIT_SWEEP_THRESHOLD"))
            ]
            
            active_controls = 0
            total_controls = len(security_controls)
            
            for control_name, is_active in security_controls:
                if is_active:
                    active_controls += 1
                    logger.info("Security control is active", control=control_name)
                else:
                    logger.warning("Security control is not active", control=control_name)
                    self.results["errors"].append(f"Security control {control_name} is not active")
            
            if active_controls == total_controls:
                self.results["security_controls_active"] = True
                logger.info("All security controls are active")
            else:
                self.results["security_controls_active"] = False
                logger.error("Some security controls are not active", active=active_controls, total=total_controls)
            
        except Exception as e:
            logger.error("Security controls test failed", error=str(e))
            self.results["errors"].append(f"Security controls test failed: {e}")
    
    async def _generate_report(self):
        """Generate final test report."""
        logger.info("Generating security validation test report")
        
        # Calculate overall security score
        security_score = 0
        total_checks = 6
        
        if self.results["paper_mode_enabled"]:
            security_score += 1
        if self.results["real_transactions_blocked"]:
            security_score += 1
        if self.results["key_encryption_verified"]:
            security_score += 1
        if self.results["file_permissions_secure"]:
            security_score += 1
        if self.results["no_key_logging"]:
            security_score += 1
        if self.results["security_controls_active"]:
            security_score += 1
        
        security_percentage = (security_score / total_checks) * 100
        
        # Create report
        report = {
            "test_summary": {
                "timestamp": time.time(),
                "paper_mode": SAFETY_CONFIG.PAPER_MODE
            },
            "results": self.results,
            "security_score": {
                "score": security_score,
                "total": total_checks,
                "percentage": security_percentage
            },
            "security_status": "SECURE" if security_percentage >= 80 else "INSECURE"
        }
        
        # Save report
        report_path = Path("dumps") / "security_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Security validation test report saved", path=str(report_path))
        
        # Print summary
        print("\n" + "="*80)
        print("SECURITY VALIDATION TEST SUMMARY")
        print("="*80)
        print(f"Paper mode enabled: {self.results['paper_mode_enabled']}")
        print(f"Real transactions blocked: {self.results['real_transactions_blocked']}")
        print(f"Key encryption verified: {self.results['key_encryption_verified']}")
        print(f"File permissions secure: {self.results['file_permissions_secure']}")
        print(f"No key logging: {self.results['no_key_logging']}")
        print(f"Security controls active: {self.results['security_controls_active']}")
        print(f"Security score: {security_score}/{total_checks} ({security_percentage:.1f}%)")
        print(f"Security status: {report['security_status']}")
        print(f"Errors: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            print("\nErrors:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("="*80)
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Security validation test cleanup complete")

async def main():
    """Main function."""
    test = SecurityValidationTest()
    
    try:
        await test.setup()
        await test.run_test()
    finally:
        await test.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
