import os
from dotenv import load_dotenv
from app.core.services import encryption_client
from app.config.logging_config import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


class EncryptionService:
    """
    Service for encrypting and decrypting strings using a consistent key.
    """
    _KEY = None

    @classmethod
    def _get_key(cls):
        """Get the encryption key, loading it if necessary."""
        if cls._KEY is None:
            key_str = os.getenv("FERNET_KEY")
            if not key_str:
                logger.error("FERNET_KEY environment variable not found")
                raise ValueError(
                    "FERNET_KEY environment variable is required for encryption")

            try:
                # Convert string key to bytes
                cls._KEY = key_str.encode('utf-8')
                logger.debug("Encryption key loaded successfully")
            except Exception as e:
                logger.error(f"Error loading encryption key: {e}")
                raise ValueError(f"Invalid FERNET_KEY format: {e}")

        return cls._KEY

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypts a string using the class key.
        Args:
            plaintext (str): The string to encrypt.
        Returns:
            str: The encrypted text, base64-encoded.
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty or None plaintext")

        try:
            key = cls._get_key()
            encrypted_bytes = encryption_client.encrypt_string(key, plaintext)
            # Fernet returns base64-encoded bytes, decode to str for storage
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise ValueError(f"Encryption failed: {e}")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypts a ciphertext using the class key.
        Args:
            ciphertext (str): The encrypted text, base64-encoded.
        Returns:
            str: The decrypted string.
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty or None ciphertext")

        try:
            key = cls._get_key()
            # Accept both str and bytes for ciphertext, but ensure bytes for decryption
            if isinstance(ciphertext, str):
                ciphertext_bytes = ciphertext.encode("utf-8")
            else:
                ciphertext_bytes = ciphertext
            decrypted_text = encryption_client.decrypt_string(
                key, ciphertext_bytes)
            return decrypted_text
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise ValueError(f"Decryption failed: {e}")
