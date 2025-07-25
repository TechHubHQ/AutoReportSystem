from cryptography.fernet import Fernet


def generate_key():
    """
    Generates a new Fernet key.
    Returns:
        bytes: The generated key.
    """
    return Fernet.generate_key()


def get_cipher(key: bytes):
    """
    Returns a Fernet cipher instance for the given key.
    Args:
        key (bytes): The Fernet key.
    Returns:
        Fernet: The Fernet cipher instance.
    """
    return Fernet(key)


def encrypt_string(key: bytes, plaintext: str) -> bytes:
    """
    Encrypts a string using the provided key.
    Args:
        key (bytes): The Fernet key.
        plaintext (str): The string to encrypt.
    Returns:
        bytes: The encrypted text.
    """
    cipher = get_cipher(key)
    return cipher.encrypt(plaintext.encode())


def decrypt_string(key: bytes, ciphertext: bytes) -> str:
    """
    Decrypts a ciphertext using the provided key.
    Args:
        key (bytes): The Fernet key.
        ciphertext (bytes): The encrypted text.
    Returns:
        str: The decrypted string.
    """
    cipher = get_cipher(key)
    return cipher.decrypt(ciphertext).decode()


# Example usage (for demonstration; remove or modify as needed)
if __name__ == "__main__":
    key = generate_key()
    print(f"Encryption Key (store securely): {key.decode()}")

    original_text = "some string"
    encrypted_text = encrypt_string(key, original_text)
    print(f"Encrypted: {encrypted_text.decode()}")

    decrypted_text = decrypt_string(key, encrypted_text)
    print(f"Decrypted: {decrypted_text}")
