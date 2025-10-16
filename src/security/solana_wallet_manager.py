"""
Solana wallet manager with encrypted keypair storage.

This module provides secure generation, encryption, and decryption of Solana keypairs
using industry-standard cryptographic practices:
- Argon2 KDF for key derivation (resistant to GPU/ASIC attacks)
- AES-GCM for authenticated encryption (prevents tampering)
- Secure random number generation
- Proper authentication tag handling
"""

import secrets
from typing import Optional
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import structlog

# Solana imports
try:
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
    from solders.keypair import Keypair as SoldersKeypair
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    # Fallback for when Solana is not available
    class Keypair:
        def __init__(self):
            pass
    
    class PublicKey:
        def __init__(self, key):
            pass

logger = structlog.get_logger(__name__)


class SolanaWalletManager:
    """
    Secure Solana wallet manager with encrypted keypair storage.
    
    Security features:
    - Argon2 KDF with secure parameters (memory=65536, iterations=3, parallelism=4)
    - AES-GCM authenticated encryption
    - Secure random number generation
    - Proper key derivation and authentication tag handling
    """
    
    # Argon2 parameters - chosen for security vs performance balance
    # Memory: 64MB (65536 KB) - resistant to GPU attacks
    # Iterations: 3 - sufficient for security without excessive delay
    # Parallelism: 4 - optimal for modern CPUs
    ARGON2_MEMORY = 65536  # KB
    ARGON2_ITERATIONS = 3
    ARGON2_PARALLELISM = 4
    
    # AES-GCM parameters
    AES_KEY_SIZE = 32  # 256-bit key
    AES_NONCE_SIZE = 12  # 96-bit nonce (recommended for GCM)
    
    def __init__(self):
        """Initialize the Solana wallet manager."""
        if not SOLANA_AVAILABLE:
            logger.warning("Solana libraries not available - running in stub mode")
        
        self.password_hasher = PasswordHasher(
            memory_cost=self.ARGON2_MEMORY,
            time_cost=self.ARGON2_ITERATIONS,
            parallelism=self.ARGON2_PARALLELISM,
            hash_len=32,
            salt_len=16
        )
    
    def generate_and_encrypt_keypair(self, passphrase: str) -> bytes:
        """
        Generate a new Solana keypair and encrypt it with the given passphrase.
        
        Args:
            passphrase: User-provided passphrase for encryption
            
        Returns:
            Encrypted keypair blob containing:
            - Argon2 salt (16 bytes)
            - AES-GCM nonce (12 bytes)
            - Encrypted keypair
            - Authentication tag (16 bytes)
            
        Raises:
            ValueError: If passphrase is empty or too weak
            RuntimeError: If keypair generation or encryption fails
        """
        if not passphrase or len(passphrase) < 8:
            raise ValueError("Passphrase must be at least 8 characters long")
        
        try:
            if not SOLANA_AVAILABLE:
                # Generate a mock keypair for testing
                mock_keypair = b"mock_solana_keypair_" + secrets.token_bytes(32)
                keypair_bytes = mock_keypair
            else:
                # Generate a new Solana keypair
                keypair = Keypair()
                
                # Serialize the keypair to bytes
                # Solana keypairs are 64 bytes: 32 bytes private key + 32 bytes public key
                keypair_bytes = bytes(keypair)
            
            # Generate secure random salt for Argon2
            salt = secrets.token_bytes(16)
            
            # Derive encryption key using Argon2
            # Using argon2-cffi for key derivation
            ph = PasswordHasher(
                memory_cost=self.ARGON2_MEMORY,
                time_cost=self.ARGON2_ITERATIONS,
                parallelism=self.ARGON2_PARALLELISM,
                hash_len=self.AES_KEY_SIZE,
                salt_len=16
            )
            
            # Hash the passphrase with the salt to get a deterministic key
            hash_result = ph.hash(passphrase.encode('utf-8'), salt=salt)
            # Extract the hash part (remove the encoded parameters)
            encryption_key = hash_result.split('$')[-1].encode('utf-8')[:self.AES_KEY_SIZE]
            
            # Generate secure random nonce for AES-GCM
            nonce = secrets.token_bytes(self.AES_NONCE_SIZE)
            
            # Encrypt the keypair using AES-GCM
            aes_gcm = AESGCM(encryption_key)
            encrypted_data = aes_gcm.encrypt(nonce, keypair_bytes, None)
            
            # Split encrypted data into ciphertext and authentication tag
            # AES-GCM appends the tag to the ciphertext
            ciphertext = encrypted_data[:-16]
            auth_tag = encrypted_data[-16:]
            
            # Create the encrypted blob: salt + nonce + ciphertext + auth_tag
            encrypted_blob = salt + nonce + ciphertext + auth_tag
            
            logger.info("Successfully generated and encrypted Solana keypair")
            return encrypted_blob
            
        except Exception as e:
            logger.error("Failed to generate and encrypt Solana keypair", error=str(e))
            raise RuntimeError(f"Keypair generation/encryption failed: {e}")
    
    def decrypt_keypair(self, encrypted_blob: bytes, passphrase: str) -> Keypair:
        """
        Decrypt a Solana keypair using the given passphrase.
        
        Args:
            encrypted_blob: Encrypted keypair blob
            passphrase: User-provided passphrase for decryption
            
        Returns:
            Solana Keypair object
            
        Raises:
            ValueError: If encrypted_blob format is invalid
            RuntimeError: If decryption fails (wrong passphrase or corrupted data)
        """
        if not encrypted_blob or len(encrypted_blob) < 44:  # Minimum size check
            raise ValueError("Invalid encrypted keypair format")
        
        try:
            # Parse the encrypted blob: salt + nonce + ciphertext + auth_tag
            salt = encrypted_blob[:16]
            nonce = encrypted_blob[16:28]
            ciphertext = encrypted_blob[28:-16]
            auth_tag = encrypted_blob[-16:]
            
            # Reconstruct the encrypted data for AES-GCM
            encrypted_data = ciphertext + auth_tag
            
            # Derive the same encryption key using Argon2
            ph = PasswordHasher(
                memory_cost=self.ARGON2_MEMORY,
                time_cost=self.ARGON2_ITERATIONS,
                parallelism=self.ARGON2_PARALLELISM,
                hash_len=self.AES_KEY_SIZE,
                salt_len=16
            )
            
            # Hash the passphrase with the salt to get a deterministic key
            hash_result = ph.hash(passphrase.encode('utf-8'), salt=salt)
            # Extract the hash part (remove the encoded parameters)
            encryption_key = hash_result.split('$')[-1].encode('utf-8')[:self.AES_KEY_SIZE]
            
            # Decrypt the keypair using AES-GCM
            aes_gcm = AESGCM(encryption_key)
            decrypted_bytes = aes_gcm.decrypt(nonce, encrypted_data, None)
            
            # Create Keypair object from decrypted bytes
            if not SOLANA_AVAILABLE:
                # Return mock keypair for testing
                logger.warning("Solana libraries not available - returning mock keypair")
                return MockKeypair(decrypted_bytes)
            else:
                # Create Solana Keypair from bytes
                keypair = Keypair.from_bytes(decrypted_bytes)
                logger.info("Successfully decrypted Solana keypair")
                return keypair
            
        except Exception as e:
            logger.error("Failed to decrypt Solana keypair", error=str(e))
            raise RuntimeError(f"Keypair decryption failed: {e}")
    
    def get_public_key(self, keypair: Keypair) -> str:
        """
        Get the public key from a Solana keypair.
        
        Args:
            keypair: Solana keypair object
            
        Returns:
            Public key as base58 string
            
        Raises:
            RuntimeError: If public key extraction fails
        """
        try:
            if not SOLANA_AVAILABLE:
                # Return mock public key for testing
                return "mock_public_key_" + secrets.token_hex(16)
            
            # Get public key from keypair
            public_key = keypair.public_key
            
            # Convert to base58 string
            public_key_str = str(public_key)
            
            logger.info("Successfully extracted public key", public_key=public_key_str)
            return public_key_str
            
        except Exception as e:
            logger.error("Failed to extract public key", error=str(e))
            raise RuntimeError(f"Public key extraction failed: {e}")
    
    def get_private_key(self, keypair: Keypair) -> str:
        """
        Get the private key from a Solana keypair.
        
        Args:
            keypair: Solana keypair object
            
        Returns:
            Private key as base58 string
            
        Raises:
            RuntimeError: If private key extraction fails
        """
        try:
            if not SOLANA_AVAILABLE:
                # Return mock private key for testing
                return "mock_private_key_" + secrets.token_hex(16)
            
            # Get private key from keypair
            private_key = keypair.secret_key
            
            # Convert to base58 string
            private_key_str = str(private_key)
            
            logger.info("Successfully extracted private key")
            return private_key_str
            
        except Exception as e:
            logger.error("Failed to extract private key", error=str(e))
            raise RuntimeError(f"Private key extraction failed: {e}")
    
    def validate_keypair(self, keypair: Keypair) -> bool:
        """
        Validate that a keypair is in the correct format.
        
        Args:
            keypair: Solana keypair object
            
        Returns:
            True if the keypair is valid, False otherwise
        """
        try:
            if not SOLANA_AVAILABLE:
                # Mock validation for testing
                return isinstance(keypair, MockKeypair)
            
            # Try to get public key to validate keypair
            public_key = keypair.public_key
            return public_key is not None
            
        except Exception:
            return False
    
    def validate_public_key(self, public_key_str: str) -> bool:
        """
        Validate that a public key is in the correct format.
        
        Args:
            public_key_str: Public key as base58 string
            
        Returns:
            True if the public key is valid, False otherwise
        """
        try:
            if not SOLANA_AVAILABLE:
                # Mock validation for testing
                return public_key_str.startswith("mock_public_key_")
            
            # Try to create PublicKey object
            public_key = PublicKey(public_key_str)
            return public_key is not None
            
        except Exception:
            return False
    
    def sign_message(self, keypair: Keypair, message: bytes) -> bytes:
        """
        Sign a message with the keypair.
        
        Args:
            keypair: Solana keypair object
            message: Message to sign
            
        Returns:
            Signature as bytes
            
        Raises:
            RuntimeError: If signing fails
        """
        try:
            if not SOLANA_AVAILABLE:
                # Return mock signature for testing
                return b"mock_signature_" + secrets.token_bytes(32)
            
            # Sign the message
            signature = keypair.sign(message)
            
            logger.info("Successfully signed message")
            return signature
            
        except Exception as e:
            logger.error("Failed to sign message", error=str(e))
            raise RuntimeError(f"Message signing failed: {e}")
    
    def verify_signature(self, public_key_str: str, message: bytes, signature: bytes) -> bool:
        """
        Verify a signature.
        
        Args:
            public_key_str: Public key as base58 string
            message: Original message
            signature: Signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not SOLANA_AVAILABLE:
                # Mock verification for testing
                return signature.startswith(b"mock_signature_")
            
            # Create PublicKey object
            public_key = PublicKey(public_key_str)
            
            # Verify signature
            is_valid = public_key.verify(message, signature)
            
            logger.info("Signature verification completed", is_valid=is_valid)
            return is_valid
            
        except Exception as e:
            logger.error("Failed to verify signature", error=str(e))
            return False


class MockKeypair:
    """Mock keypair for testing when Solana libraries are not available."""
    
    def __init__(self, keypair_bytes: bytes):
        """Initialize mock keypair."""
        self.keypair_bytes = keypair_bytes
        self.public_key = f"mock_public_key_{secrets.token_hex(16)}"
        self.secret_key = f"mock_secret_key_{secrets.token_hex(16)}"
    
    def sign(self, message: bytes) -> bytes:
        """Mock sign method."""
        return b"mock_signature_" + secrets.token_bytes(32)
    
    def __bytes__(self) -> bytes:
        """Return keypair as bytes."""
        return self.keypair_bytes


# Global Solana wallet manager instance
_solana_wallet_manager: Optional[SolanaWalletManager] = None


def get_solana_wallet_manager() -> SolanaWalletManager:
    """
    Get the global Solana wallet manager instance.
    
    Returns:
        Solana wallet manager instance
    """
    global _solana_wallet_manager
    
    if _solana_wallet_manager is None:
        _solana_wallet_manager = SolanaWalletManager()
    
    return _solana_wallet_manager


def generate_and_encrypt_keypair(passphrase: str) -> bytes:
    """
    Generate a new Solana keypair and encrypt it with the given passphrase.
    
    Args:
        passphrase: User-provided passphrase for encryption
        
    Returns:
        Encrypted keypair blob
    """
    return get_solana_wallet_manager().generate_and_encrypt_keypair(passphrase)


def decrypt_keypair(encrypted_blob: bytes, passphrase: str) -> Keypair:
    """
    Decrypt a Solana keypair using the given passphrase.
    
    Args:
        encrypted_blob: Encrypted keypair blob
        passphrase: User-provided passphrase for decryption
        
    Returns:
        Solana Keypair object
    """
    return get_solana_wallet_manager().decrypt_keypair(encrypted_blob, passphrase)
