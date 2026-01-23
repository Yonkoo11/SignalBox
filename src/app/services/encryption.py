from cryptography.fernet import Fernet
import base64
import hashlib

from app.config import config


def get_fernet():
    key = config.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY not set")
    # Ensure key is 32 bytes for Fernet
    key_bytes = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt(value: str) -> str:
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    f = get_fernet()
    return f.decrypt(value.encode()).decode()
