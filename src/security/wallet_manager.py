"""
Secure wallet management with encrypted private key storage.

This module provides secure generation, encryption, and decryption of private keys
using industry-standard cryptographic practices:
- Argon2 KDF for key derivation (resistant to GPU/ASIC attacks)
- AES-GCM for authenticated encryption (prevents tampering)
- Secure random number generation
- Proper authentication tag handling
"""

import secrets
from cryptography.hazmat.primitives import hashes, serialization
# Argon2 is provided by argon2-cffi package
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from argon2 import PasswordHasher
import structlog

logger = structlog.get_logger(__name__)


class WalletManager:
    """
    Secure wallet manager with encrypted private key storage.
    
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
        """Initialize the wallet manager."""
        self.password_hasher = PasswordHasher(
            memory_cost=self.ARGON2_MEMORY,
            time_cost=self.ARGON2_ITERATIONS,
            parallelism=self.ARGON2_PARALLELISM,
            hash_len=32,
            salt_len=16
        )
    
    def generate_and_encrypt_key(self, passphrase: str) -> bytes:
        """
        Generate a new private key and encrypt it with the given passphrase.
        
        Args:
            passphrase: User-provided passphrase for encryption
            
        Returns:
            Encrypted private key blob containing:
            - Argon2 salt (16 bytes)
            - AES-GCM nonce (12 bytes)
            - Encrypted private key
            - Authentication tag (16 bytes)
            
        Raises:
            ValueError: If passphrase is empty or too weak
            RuntimeError: If key generation or encryption fails
        """
        if not passphrase or len(passphrase) < 8:
            raise ValueError("Passphrase must be at least 8 characters long")
        
        try:
            # Generate a new private key using secp256k1 curve (Bitcoin/Ethereum standard)
            # This curve provides 128-bit security level
            private_key = ec.generate_private_key(
                curve=ec.SECP256K1(),
                backend=default_backend()
            )
            
            # Serialize the private key to PEM format
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
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
            
            # Encrypt the private key using AES-GCM
            aes_gcm = AESGCM(encryption_key)
            encrypted_data = aes_gcm.encrypt(nonce, private_key_pem, None)
            
            # Split encrypted data into ciphertext and authentication tag
            # AES-GCM appends the tag to the ciphertext
            ciphertext = encrypted_data[:-16]
            auth_tag = encrypted_data[-16:]
            
            # Create the encrypted blob: salt + nonce + ciphertext + auth_tag
            encrypted_blob = salt + nonce + ciphertext + auth_tag
            
            logger.info("Successfully generated and encrypted private key")
            return encrypted_blob
            
        except Exception as e:
            logger.error("Failed to generate and encrypt private key", error=str(e))
            raise RuntimeError(f"Key generation/encryption failed: {e}")
    
    def decrypt_key(self, encrypted_key: bytes, passphrase: str) -> str:
        """
        Decrypt a private key using the given passphrase.
        
        Args:
            encrypted_key: Encrypted private key blob
            passphrase: User-provided passphrase for decryption
            
        Returns:
            Private key in hexadecimal format
            
        Raises:
            ValueError: If encrypted_key format is invalid
            RuntimeError: If decryption fails (wrong passphrase or corrupted data)
        """
        if not encrypted_key or len(encrypted_key) < 44:  # Minimum size check
            raise ValueError("Invalid encrypted key format")
        
        try:
            # Parse the encrypted blob: salt + nonce + ciphertext + auth_tag
            salt = encrypted_key[:16]
            nonce = encrypted_key[16:28]
            ciphertext = encrypted_key[28:-16]
            auth_tag = encrypted_key[-16:]
            
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
            
            # Decrypt the private key using AES-GCM
            aes_gcm = AESGCM(encryption_key)
            decrypted_pem = aes_gcm.decrypt(nonce, encrypted_data, None)
            
            # Load the private key from PEM format
            private_key = serialization.load_pem_private_key(
                decrypted_pem,
                password=None,
                backend=default_backend()
            )
            
            # Convert to hexadecimal format
            # Extract the raw private key value from EC key
            if hasattr(private_key, 'private_numbers'):
                # For EC keys, get the raw private value
                private_value = private_key.private_numbers().private_value
                private_key_hex = format(private_value, '064x')  # 32 bytes = 64 hex chars
            else:
                # Fallback for other key types
                private_key_hex = private_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).hex()
            
            logger.info("Successfully decrypted private key")
            return private_key_hex
            
        except Exception as e:
            logger.error("Failed to decrypt private key", error=str(e))
            raise RuntimeError(f"Key decryption failed: {e}")
    
    def generate_wallet_address(self, private_key_hex: str) -> str:
        """
        Generate a wallet address from a private key.
        
        Args:
            private_key_hex: Private key in hexadecimal format
            
        Returns:
            Ethereum wallet address (checksummed)
            
        Raises:
            ValueError: If private key format is invalid
            RuntimeError: If address generation fails
        """
        try:
            # Convert hex string to bytes
            private_key_bytes = bytes.fromhex(private_key_hex)
            
            # Load the private key
            private_key = ec.derive_private_key(
                int.from_bytes(private_key_bytes, 'big'),
                curve=ec.SECP256K1(),
                backend=default_backend()
            )
            
            # Get the public key
            public_key = private_key.public_key()
            
            # Serialize the public key
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            
            # Extract the uncompressed public key (skip the first byte)
            uncompressed_public_key = public_key_bytes[1:]
            
            # Calculate the Ethereum address (last 20 bytes of Keccak-256 hash)
            from cryptography.hazmat.primitives import hashes
            digest = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
            digest.update(uncompressed_public_key)
            hash_bytes = digest.finalize()
            
            # Take the last 20 bytes for the address
            address_bytes = hash_bytes[-20:]
            address = "0x" + address_bytes.hex()
            
            # Convert to checksummed address (EIP-55)
            address = self._to_checksum_address(address)
            
            logger.info("Successfully generated wallet address", address=address)
            return address
            
        except Exception as e:
            logger.error("Failed to generate wallet address", error=str(e))
            raise RuntimeError(f"Address generation failed: {e}")
    
    def _to_checksum_address(self, address: str) -> str:
        """
        Convert an address to checksummed format (EIP-55).
        
        Args:
            address: Ethereum address in lowercase
            
        Returns:
            Checksummed address
        """
        # Remove 0x prefix
        address = address[2:].lower()
        
        # Calculate Keccak-256 hash
        digest = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
        digest.update(address.encode('utf-8'))
        hash_bytes = digest.finalize()
        hash_hex = hash_bytes.hex()
        
        # Apply checksum
        checksummed = "0x"
        for i, char in enumerate(address):
            if char.isalpha() and int(hash_hex[i], 16) >= 8:
                checksummed += char.upper()
            else:
                checksummed += char
        
        return checksummed
    
    def validate_private_key(self, private_key_hex: str) -> bool:
        """
        Validate that a private key is in the correct format.
        
        Args:
            private_key_hex: Private key in hexadecimal format
            
        Returns:
            True if the private key is valid, False otherwise
        """
        try:
            # Check if it's a valid hex string
            if not all(c in '0123456789abcdefABCDEF' for c in private_key_hex):
                return False
            
            # Check length (64 characters for 32 bytes)
            if len(private_key_hex) != 64:
                return False
            
            # Check if it's not zero or max value
            private_key_int = int(private_key_hex, 16)
            if private_key_int == 0 or private_key_int >= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141:
                return False
            
            return True
            
        except Exception:
            return False
    
    def validate_address(self, address: str) -> bool:
        """
        Validate that an address is in the correct format.
        
        Args:
            address: Ethereum address
            
        Returns:
            True if the address is valid, False otherwise
        """
        try:
            # Check if it starts with 0x
            if not address.startswith('0x'):
                return False
            
            # Check if it's a valid hex string
            if not all(c in '0123456789abcdefABCDEF' for c in address[2:]):
                return False
            
            # Check length (40 characters for 20 bytes)
            if len(address) != 42:
                return False
            
            return True
            
        except Exception:
            return False


# Global wallet manager instance
wallet_manager = WalletManager()


def generate_and_encrypt_key(passphrase: str) -> bytes:
    """
    Generate a new private key and encrypt it with the given passphrase.
    
    Args:
        passphrase: User-provided passphrase for encryption
        
    Returns:
        Encrypted private key blob
    """
    return wallet_manager.generate_and_encrypt_key(passphrase)


def decrypt_key(encrypted_key: bytes, passphrase: str) -> str:
    """
    Decrypt a private key using the given passphrase.
    
    Args:
        encrypted_key: Encrypted private key blob
        passphrase: User-provided passphrase for decryption
        
    Returns:
        Private key in hexadecimal format
    """
    return wallet_manager.decrypt_key(encrypted_key, passphrase)
