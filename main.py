#!/usr/bin/env python3
"""
Main entry point for the meme-coin trading bot.

This module provides the bootstrap flow for first-run setup and bot initialization.
It handles encrypted key generation, environment validation, and secure startup.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Optional

import structlog
from dotenv import load_dotenv

from src.config import SAFETY_CONFIG, TRADING_CONFIG
from src.security import generate_and_encrypt_key, decrypt_key
from src.utils.logger import setup_logging

# Configure logging
logger = structlog.get_logger(__name__)


def validate_environment() -> bool:
    """
    Validate that the environment is properly configured.
    
    Returns:
        True if environment is valid, False otherwise
    """
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = [
        'RPCENDPOINT1',
        'RPCENDPOINT2',
        'WSMEMPOOLPRIMARY',
        'COLDSTORAGEADDRESS',
        'NOTIFIERTOKEN',
        'MODELSTOREURL',
        'INDEXERURL',
        'BACKUPSTORAGEURL',
        'GUIAPISOCKET',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("Missing required environment variables", missing=missing_vars)
        return False
    
    # Validate file permissions
    if not validate_file_permissions():
        return False
    
    logger.info("Environment validation passed")
    return True


def validate_file_permissions() -> bool:
    """
    Validate that the filesystem is secure for storing encrypted keys.
    
    Returns:
        True if filesystem is secure, False otherwise
    """
    try:
        # Check if we can create files in the current directory
        test_file = Path('.test_permissions')
        test_file.write_text('test')
        
        # Check file permissions
        stat_info = test_file.stat()
        if stat_info.st_mode & 0o077:  # Check if readable by others
            logger.error("Filesystem permissions are insecure - files are readable by others")
            test_file.unlink()
            return False
        
        # Clean up test file
        test_file.unlink()
        
        logger.info("Filesystem permissions are secure")
        return True
        
    except Exception as e:
        logger.error("Failed to validate filesystem permissions", error=str(e))
        return False


def setup_encrypted_key() -> bool:
    """
    Set up encrypted private key for the bot.
    
    Returns:
        True if setup successful, False otherwise
    """
    encrypted_key_file = Path('.encrypted_key')
    
    if encrypted_key_file.exists():
        logger.info("Encrypted key file already exists")
        return True
    
    try:
        # Prompt for passphrase
        print("\n" + "="*60)
        print("MEME-COIN TRADING BOT - FIRST RUN SETUP")
        print("="*60)
        print("\nThis is your first run. You need to create an encrypted wallet.")
        print("The wallet will be used for trading operations.")
        print("\nIMPORTANT SECURITY NOTES:")
        print("- Choose a strong passphrase (at least 12 characters)")
        print("- Store your passphrase securely - it cannot be recovered")
        print("- The encrypted key will be stored locally with secure permissions")
        print("- Never share your passphrase or encrypted key file")
        print("\n" + "-"*60)
        
        # Get passphrase with confirmation
        while True:
            passphrase = getpass.getpass("Enter passphrase for wallet encryption: ")
            if len(passphrase) < 8:
                print("Error: Passphrase must be at least 8 characters long")
                continue
            
            confirm_passphrase = getpass.getpass("Confirm passphrase: ")
            if passphrase != confirm_passphrase:
                print("Error: Passphrases do not match")
                continue
            
            break
        
        # Generate and encrypt the key
        print("\nGenerating encrypted wallet...")
        encrypted_key = generate_and_encrypt_key(passphrase)
        
        # Write encrypted key to file with secure permissions
        encrypted_key_file.write_bytes(encrypted_key)
        encrypted_key_file.chmod(0o600)  # Read/write for owner only
        
        print(f"\nOK Encrypted wallet created successfully!")
        print(f"OK Key file: {encrypted_key_file.absolute()}")
        print(f"OK Permissions: {oct(encrypted_key_file.stat().st_mode)[-3:]}")
        
        # Show next steps
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("1. Configure your .env file with API keys and endpoints")
        print("2. Test the bot in paper mode: python main.py --paper-mode")
        print("3. Review the deployment checklist in DEPLOYMENT.md")
        print("4. Enable live trading only after thorough testing")
        print("\nSECURITY REMINDERS:")
        print("- Never commit the .encrypted_key file to version control")
        print("- Store your passphrase securely")
        print("- Test thoroughly in paper mode before live trading")
        print("- Enable kill-switch before live trading")
        print("="*60)
        
        logger.info("Encrypted key setup completed successfully")
        return True
        
    except Exception as e:
        logger.error("Failed to setup encrypted key", error=str(e))
        print(f"\nError: Failed to setup encrypted key: {e}")
        return False


def load_encrypted_key() -> Optional[bytes]:
    """
    Load the encrypted key from file.
    
    Returns:
        Encrypted key bytes if successful, None otherwise
    """
    encrypted_key_file = Path('.encrypted_key')
    
    if not encrypted_key_file.exists():
        logger.error("Encrypted key file not found")
        return None
    
    try:
        encrypted_key = encrypted_key_file.read_bytes()
        logger.info("Encrypted key loaded successfully")
        return encrypted_key
        
    except Exception as e:
        logger.error("Failed to load encrypted key", error=str(e))
        return None


def decrypt_wallet_key(encrypted_key: bytes) -> Optional[str]:
    """
    Decrypt the wallet key using user-provided passphrase.
    
    Args:
        encrypted_key: Encrypted key bytes
        
    Returns:
        Decrypted private key if successful, None otherwise
    """
    try:
        passphrase = getpass.getpass("Enter passphrase to decrypt wallet: ")
        private_key = decrypt_key(encrypted_key, passphrase)
        
        logger.info("Wallet key decrypted successfully")
        return private_key
        
    except Exception as e:
        logger.error("Failed to decrypt wallet key", error=str(e))
        print(f"Error: Failed to decrypt wallet key: {e}")
        return None


def initialize_bot(paper_mode: bool = False) -> bool:
    """
    Initialize the trading bot.
    
    Args:
        paper_mode: Whether to run in paper mode
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Load encrypted key
        encrypted_key = load_encrypted_key()
        if not encrypted_key:
            return False
        
        # Decrypt wallet key
        private_key = decrypt_wallet_key(encrypted_key)
        if not private_key:
            return False
        
        # Initialize bot components
        logger.info("Initializing trading bot", paper_mode=paper_mode)
        
        # Initialize database
        from src.utils.database import initialize_database
        if not initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize trading components
        from src.trading.strategy import get_strategy
        from src.trading.exchange import get_exchange_interface
        from src.trading.risk_manager import get_risk_manager
        
        # Initialize components
        strategy = get_strategy()
        exchange = get_exchange_interface(paper_mode=paper_mode)
        risk_manager = get_risk_manager()
        
        # Set portfolio value for risk manager
        if paper_mode:
            risk_manager.portfolio_value = 10000.0  # Paper mode starting balance
        else:
            # TODO: Get real portfolio value
            risk_manager.portfolio_value = 10000.0
        
        print(f"\nOK Bot initialized successfully!")
        print(f"OK Mode: {'Paper Mode' if paper_mode else 'Live Trading'}")
        print(f"OK Private key: {private_key[:8]}...{private_key[-8:]}")
        
        if paper_mode:
            print("\nPAPER MODE ACTIVE:")
            print("- No real trades will be executed")
            print("- All operations are simulated")
            print("- Safe for testing and development")
        else:
            print("\nLIVE TRADING MODE:")
            print("- Real trades will be executed")
            print("- Use with extreme caution")
            print("- Ensure kill-switch is enabled")
        
        return True
        
    except Exception as e:
        logger.error("Failed to initialize bot", error=str(e))
        print(f"Error: Failed to initialize bot: {e}")
        return False


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Autonomous Hardened Meme-Coin Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --paper-mode          # Run in paper mode
  python main.py --live                # Run in live mode (dangerous!)
  python main.py --setup               # Setup encrypted wallet
  python main.py --validate            # Validate environment
        """
    )
    
    parser.add_argument(
        '--paper-mode',
        action='store_true',
        help='Run in paper mode (no real trades)'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in live mode (real trades - dangerous!)'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Setup encrypted wallet (first run)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate environment configuration'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle setup mode
    if args.setup:
        if not validate_file_permissions():
            print("Error: Filesystem permissions are insecure")
            sys.exit(1)
        
        if not setup_encrypted_key():
            print("Error: Failed to setup encrypted key")
            sys.exit(1)
        
        print("\nSetup completed successfully!")
        sys.exit(0)
    
    # Handle validation mode
    if args.validate:
        if validate_environment():
            print("OK Environment validation passed")
            sys.exit(0)
        else:
            print("X Environment validation failed")
            sys.exit(1)
    
    # Validate environment
    if not validate_environment():
        print("Error: Environment validation failed")
        print("Run 'python main.py --validate' for details")
        sys.exit(1)
    
    # Determine mode
    paper_mode = args.paper_mode or not args.live
    
    # Safety check for live mode
    if args.live:
        print("\n" + "!"*60)
        print("WARNING: LIVE TRADING MODE")
        print("!"*60)
        print("You are about to enable live trading with real money.")
        print("This is extremely dangerous and can result in significant losses.")
        print("\nBefore proceeding, ensure:")
        print("1. You have thoroughly tested in paper mode")
        print("2. You understand the risks")
        print("3. You have enabled the kill-switch")
        print("4. You have set appropriate position limits")
        print("5. You have a backup plan")
        
        confirm = input("\nType 'I UNDERSTAND THE RISKS' to continue: ")
        if confirm != 'I UNDERSTAND THE RISKS':
            print("Live trading cancelled")
            sys.exit(0)
    
    # Initialize and run bot
    if not initialize_bot(paper_mode):
        print("Error: Failed to initialize bot")
        sys.exit(1)
    
    # Start bot main loop
    print("\nBot is running... Press Ctrl+C to stop")
    try:
        import asyncio
        from src.utils.scheduler import start_trading_bot, stop_trading_bot
        
        # Start the trading bot
        async def run_bot():
            scheduler = await start_trading_bot()
            return scheduler
        
        # Run the bot
        scheduler = asyncio.run(run_bot())
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        logger.info("Bot stopped by user")
        
        # Stop the trading bot
        try:
            asyncio.run(stop_trading_bot())
        except Exception as e:
            logger.error("Failed to stop trading bot", error=str(e))


if __name__ == '__main__':
    main()
