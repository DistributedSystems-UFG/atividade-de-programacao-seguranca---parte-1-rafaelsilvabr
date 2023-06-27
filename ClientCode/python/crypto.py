from cryptography.fernet import Fernet
import json, const

def encrypt(message: str, key: bytes = const.FERNET_KEY) -> str:
    return Fernet(key).encrypt(message.encode()).decode()

def decrypt(token: str, key: bytes = const.FERNET_KEY) -> str:
    return Fernet(key).decrypt(token.encode()).decode()

