"""
MiroFish Enterprise AES-256-GCM Vault Manager (Agent 20: DevOps & Vault Guard)
Provides envelope encryption for sensitive credentials, API keys, webhook URLs,
and private client data.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_VAULT_PATH = os.path.expanduser("~/.hermes/mirofish_vault.enc")
MASTER_KEY_ENV = "MIROFISH_VAULT_KEY"

def _derive_key(passphrase: Optional[str] = None) -> bytes:
    key_str = passphrase or os.environ.get(MASTER_KEY_ENV) or "mirofish-enterprise-default-vault-key-32b"
    raw = key_str.encode("utf-8")
    if len(raw) >= 32:
        return raw[:32]
    return raw.ljust(32, b"0")

class VaultManager:
    """Manages encrypted key-value storage using AES-256-GCM envelope encryption."""

    def __init__(self, vault_path: str = DEFAULT_VAULT_PATH, passphrase: Optional[str] = None):
        self.vault_path = vault_path
        self._key = _derive_key(passphrase)
        self._cache: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.vault_path):
            self._cache = {}
            return

        try:
            with open(self.vault_path, "rb") as f:
                data = f.read()
            if len(data) < 12:
                self._cache = {}
                return
            nonce = data[:12]
            ciphertext = data[12:]
            aesgcm = AESGCM(self._key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            self._cache = json.loads(decrypted.decode("utf-8"))
        except Exception:
            self._cache = {}

    def _save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.vault_path)), exist_ok=True)
        plaintext = json.dumps(self._cache, ensure_ascii=False).encode("utf-8")
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        with open(self.vault_path, "wb") as f:
            f.write(nonce + ciphertext)

    def set_secret(self, key: str, value: Any):
        self._cache[key] = value
        self._save()

    def get_secret(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def delete_secret(self, key: str):
        if key in self._cache:
            del self._cache[key]
            self._save()

    def list_keys(self):
        return list(self._cache.keys())

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        data = base64.b64decode(ciphertext_b64.encode("ascii"))
        nonce = data[:12]
        ct = data[12:]
        aesgcm = AESGCM(self._key)
        pt = aesgcm.decrypt(nonce, ct, None)
        return pt.decode("utf-8")

# Global singleton
_vault_instance = None

def get_vault() -> VaultManager:
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = VaultManager()
    return _vault_instance
