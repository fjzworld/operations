from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import os

# 获取或生成一个用于加密的 Key
# 在生产环境中，这应该是一个固定的 Secret，从环境变量读取
# 这里为了演示，我们基于 SECRET_KEY 生成一个合法的 Fernet Key
def get_cipher_suite():
    # Fernet key must be 32 url-safe base64-encoded bytes
    key = settings.SECRET_KEY[:32].encode()
    # Pad if too short
    if len(key) < 32:
        key = key + b'=' * (32 - len(key))
    
    # Ensure it's valid base64
    try:
        base64.urlsafe_b64decode(key)
    except:
        key = Fernet.generate_key()
        
    return Fernet(base64.urlsafe_b64encode(key[:32]))

def encrypt_string(text: str) -> str:
    if not text:
        return None
    cipher = get_cipher_suite()
    return cipher.encrypt(text.encode()).decode()

def decrypt_string(text: str) -> str:
    if not text:
        return None
    cipher = get_cipher_suite()
    return cipher.decrypt(text.encode()).decode()
