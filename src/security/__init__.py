"""
Security module for the meme-coin trading bot.

This module provides secure wallet management, encryption, and authentication
functionality with industry-standard cryptographic practices.
"""

from .wallet_manager import WalletManager, generate_and_encrypt_key, decrypt_key

__all__ = [
    'WalletManager',
    'generate_and_encrypt_key',
    'decrypt_key',
]
