"""
Unit tests for wallet manager functionality.

Tests cover key generation, encryption, decryption, and address generation
with proper security validation.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.security.wallet_manager import WalletManager, generate_and_encrypt_key, decrypt_key


class TestWalletManager:
    """Test cases for WalletManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.wallet_manager = WalletManager()
        self.test_passphrase = "test_passphrase_123"
    
    def test_generate_and_encrypt_key_success(self):
        """Test successful key generation and encryption."""
        encrypted_key = self.wallet_manager.generate_and_encrypt_key(self.test_passphrase)
        
        assert isinstance(encrypted_key, bytes)
        assert len(encrypted_key) > 0
        
        # Verify the encrypted blob structure: salt + nonce + ciphertext + auth_tag
        assert len(encrypted_key) >= 44  # Minimum size check
    
    def test_generate_and_encrypt_key_invalid_passphrase(self):
        """Test key generation with invalid passphrase."""
        with pytest.raises(ValueError, match="Passphrase must be at least 8 characters long"):
            self.wallet_manager.generate_and_encrypt_key("short")
        
        with pytest.raises(ValueError, match="Passphrase must be at least 8 characters long"):
            self.wallet_manager.generate_and_encrypt_key("")
    
    def test_decrypt_key_success(self):
        """Test successful key decryption."""
        # Generate and encrypt a key
        encrypted_key = self.wallet_manager.generate_and_encrypt_key(self.test_passphrase)
        
        # Decrypt the key
        decrypted_key = self.wallet_manager.decrypt_key(encrypted_key, self.test_passphrase)
        
        assert isinstance(decrypted_key, str)
        assert len(decrypted_key) == 64  # 32 bytes = 64 hex characters
        assert all(c in '0123456789abcdefABCDEF' for c in decrypted_key)
    
    def test_decrypt_key_wrong_passphrase(self):
        """Test key decryption with wrong passphrase."""
        encrypted_key = self.wallet_manager.generate_and_encrypt_key(self.test_passphrase)
        
        with pytest.raises(RuntimeError, match="Key decryption failed"):
            self.wallet_manager.decrypt_key(encrypted_key, "wrong_passphrase")
    
    def test_decrypt_key_invalid_format(self):
        """Test key decryption with invalid encrypted key format."""
        with pytest.raises(ValueError, match="Invalid encrypted key format"):
            self.wallet_manager.decrypt_key(b"invalid", self.test_passphrase)
        
        with pytest.raises(ValueError, match="Invalid encrypted key format"):
            self.wallet_manager.decrypt_key(b"", self.test_passphrase)
    
    def test_generate_wallet_address_success(self):
        """Test successful wallet address generation."""
        encrypted_key = self.wallet_manager.generate_and_encrypt_key(self.test_passphrase)
        private_key = self.wallet_manager.decrypt_key(encrypted_key, self.test_passphrase)
        
        address = self.wallet_manager.generate_wallet_address(private_key)
        
        assert isinstance(address, str)
        assert address.startswith("0x")
        assert len(address) == 42  # 20 bytes = 40 hex characters + "0x"
        assert all(c in '0123456789abcdefABCDEF' for c in address[2:])
    
    def test_generate_wallet_address_invalid_key(self):
        """Test wallet address generation with invalid private key."""
        with pytest.raises(RuntimeError, match="Address generation failed"):
            self.wallet_manager.generate_wallet_address("invalid_key")
    
    def test_validate_private_key(self):
        """Test private key validation."""
        # Valid private key
        valid_key = "a" * 64
        assert self.wallet_manager.validate_private_key(valid_key) is True
        
        # Invalid length
        assert self.wallet_manager.validate_private_key("a" * 32) is False
        
        # Invalid characters
        assert self.wallet_manager.validate_private_key("g" * 64) is False
        
        # Zero key
        assert self.wallet_manager.validate_private_key("0" * 64) is False
    
    def test_validate_address(self):
        """Test address validation."""
        # Valid address
        valid_address = "0x" + "a" * 40
        assert self.wallet_manager.validate_address(valid_address) is True
        
        # Invalid prefix
        assert self.wallet_manager.validate_address("1x" + "a" * 40) is False
        
        # Invalid length
        assert self.wallet_manager.validate_address("0x" + "a" * 20) is False
        
        # Invalid characters
        assert self.wallet_manager.validate_address("0x" + "g" * 40) is False
    
    def test_to_checksum_address(self):
        """Test checksum address conversion."""
        address = "0x" + "a" * 40
        checksummed = self.wallet_manager._to_checksum_address(address)
        
        assert isinstance(checksummed, str)
        assert checksummed.startswith("0x")
        assert len(checksummed) == 42


class TestWalletManagerFunctions:
    """Test cases for module-level functions."""
    
    def test_generate_and_encrypt_key_function(self):
        """Test module-level generate_and_encrypt_key function."""
        passphrase = "test_passphrase_123"
        encrypted_key = generate_and_encrypt_key(passphrase)
        
        assert isinstance(encrypted_key, bytes)
        assert len(encrypted_key) > 0
    
    def test_decrypt_key_function(self):
        """Test module-level decrypt_key function."""
        passphrase = "test_passphrase_123"
        encrypted_key = generate_and_encrypt_key(passphrase)
        decrypted_key = decrypt_key(encrypted_key, passphrase)
        
        assert isinstance(decrypted_key, str)
        assert len(decrypted_key) == 64


@pytest.mark.integration
class TestWalletManagerIntegration:
    """Integration tests for wallet manager."""
    
    def test_full_wallet_lifecycle(self):
        """Test complete wallet lifecycle: generate -> encrypt -> decrypt -> address."""
        wallet_manager = WalletManager()
        passphrase = "integration_test_passphrase_123"
        
        # Generate and encrypt key
        encrypted_key = wallet_manager.generate_and_encrypt_key(passphrase)
        assert isinstance(encrypted_key, bytes)
        
        # Decrypt key
        private_key = wallet_manager.decrypt_key(encrypted_key, passphrase)
        assert isinstance(private_key, str)
        assert len(private_key) == 64
        
        # Generate address
        address = wallet_manager.generate_wallet_address(private_key)
        assert isinstance(address, str)
        assert address.startswith("0x")
        assert len(address) == 42
        
        # Validate components
        assert wallet_manager.validate_private_key(private_key) is True
        assert wallet_manager.validate_address(address) is True
    
    def test_multiple_key_generation(self):
        """Test generating multiple unique keys."""
        wallet_manager = WalletManager()
        passphrase = "test_passphrase_123"
        
        keys = []
        for _ in range(5):
            encrypted_key = wallet_manager.generate_and_encrypt_key(passphrase)
            private_key = wallet_manager.decrypt_key(encrypted_key, passphrase)
            keys.append(private_key)
        
        # All keys should be unique
        assert len(set(keys)) == 5
        
        # All keys should be valid
        for key in keys:
            assert wallet_manager.validate_private_key(key) is True
