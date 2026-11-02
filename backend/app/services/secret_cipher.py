"""
Enkripsi Rahasia dan Kredensial menggunakan AES-GCM
Memastikan API Key dan token tidak tersimpan dalam bentuk plaintext di database
"""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _get_aes_key(key_str: str) -> bytes:
    raw = key_str.encode("utf-8")
    if len(raw) >= 32:
        return raw[:32]
    return raw.ljust(32, b"0")

def encrypt_secret(plaintext: str, key_str: str) -> str:
    """Enkripsi string rahasia menggunakan AES-GCM 256-bit."""
    if not plaintext:
        return ""
    key = _get_aes_key(key_str)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")

def decrypt_secret(encrypted_b64: str, key_str: str) -> str:
    """Dekripsi string rahasia terenkripsi AES-GCM."""
    if not encrypted_b64:
        return ""
    key = _get_aes_key(key_str)
    aesgcm = AESGCM(key)
    data = base64.b64decode(encrypted_b64.encode("utf-8"))
    nonce = data[:12]
    ct = data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")
