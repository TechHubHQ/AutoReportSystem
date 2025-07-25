import os
from cryptography.fernet import Fernet
from config.config import settings


class EncryptionService:
    """
    Service for encrypting and decrypting SMTP passwords.
    """

    _key_env_var = settings.SMTP_ENV_KEY

    @classmethod
    def _get_key(cls):
        key = os.environ.get(cls._key_env_var)
        if not key:
            key = Fernet.generate_key()
        else:
            key = key.encode() if isinstance(key, str) else key
        return key

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypts the given plaintext string and returns a base64-encoded ciphertext.
        """
        key = cls._get_key()
        f = Fernet(key)
        token = f.encrypt(plaintext.encode())
        return token.decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypts the given base64-encoded ciphertext and returns the plaintext string.
        """
        key = cls._get_key()
        f = Fernet(key)
        plaintext = f.decrypt(ciphertext.encode())
        return plaintext.decode()
