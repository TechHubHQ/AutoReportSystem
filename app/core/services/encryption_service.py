import os
from dotenv import load_dotenv
from app.core.services import encryption_client


load_dotenv()

class EncryptionService:
    """
    Service for encrypting and decrypting strings using a consistent key.
    """
    _KEY = os.getenv("FERNET_KEY")

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypts a string using the class key.
        Args:
            plaintext (str): The string to encrypt.
        Returns:
            str: The encrypted text, base64-encoded.
        """
        encrypted_bytes = encryption_client.encrypt_string(cls._KEY, plaintext)
        # Fernet returns base64-encoded bytes, decode to str for storage
        return encrypted_bytes.decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypts a ciphertext using the class key.
        Args:
            ciphertext (str): The encrypted text, base64-encoded.
        Returns:
            str: The decrypted string.
        """
        # Accept both str and bytes for ciphertext, but ensure bytes for decryption
        if isinstance(ciphertext, str):
            ciphertext_bytes = ciphertext.encode("utf-8")
        else:
            ciphertext_bytes = ciphertext
        decrypted_text = encryption_client.decrypt_string(cls._KEY, ciphertext_bytes)
        return decrypted_text
