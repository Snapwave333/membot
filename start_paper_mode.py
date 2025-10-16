#!/usr/bin/env python3
"""
Quick start script for paper mode testing.

This script provides a simple way to start the bot in paper mode
for testing and development purposes.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Check if all requirements are met."""
    print("Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11+ required")
        return False
    
    # Check if virtual environment exists
    if not Path("venv").exists():
        print("Error: Virtual environment not found")
        print("Run: python -m venv venv")
        return False
    
    # Check if requirements are installed
    try:
        import web3
        import sqlalchemy
        import cryptography
        print("✓ Dependencies installed")
    except ImportError as e:
        print(f"Error: Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True


def setup_environment():
    """Setup environment for paper mode."""
    print("Setting up environment...")
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Check if .env exists
    if not Path(".env").exists():
        if Path("env.example").exists():
            print("Creating .env from template...")
            import shutil
            shutil.copy("env.example", ".env")
            print("✓ .env file created")
            print("⚠️  Please edit .env with your configuration")
        else:
            print("Error: env.example not found")
            return False
    
    return True


def start_paper_mode():
    """Start the bot in paper mode."""
    print("Starting bot in paper mode...")
    
    try:
        # Run the bot in paper mode
        result = subprocess.run([
            sys.executable, "main.py", "--paper-mode"
        ], check=True)
        
        print("✓ Bot started successfully in paper mode")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to start bot: {e}")
        return False
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("MEME-COIN TRADING BOT - PAPER MODE STARTUP")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\nRequirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\nEnvironment setup failed. Please fix the issues above.")
        sys.exit(1)
    
    # Start paper mode
    if not start_paper_mode():
        print("\nFailed to start bot in paper mode.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("PAPER MODE STARTUP COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
