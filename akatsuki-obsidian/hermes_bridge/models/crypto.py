import os
import base64
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("akatsuki.crypto")

AES_KEY_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16


def _derive_key(master_key: str, salt: bytes = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", master_key.encode(), salt, 100000, dklen=AES_KEY_SIZE)
    return key, salt


def _aes_gcm_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        nonce = os.urandom(NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce, b""
    except ImportError:
        try:
            from Crypto.Cipher import AES
            cipher = AES.new(key, AES.MODE_GCM, nonce=os.urandom(NONCE_SIZE))
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)
            return ciphertext, cipher.nonce, tag
        except ImportError:
            logger.warning("No crypto library available (install cryptography or pycryptodome)")
            return plaintext, b"", b""


def _aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes) -> Optional[bytes]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except ImportError:
        try:
            from Crypto.Cipher import AES
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)
        except ImportError:
            return ciphertext


class VaultEncryption:
    def __init__(self, master_key: str = ""):
        self.master_key = master_key or os.environ.get("AKATSUKI_ENCRYPTION_KEY", "")
        self._enabled = bool(self.master_key)

    def is_enabled(self) -> bool:
        return self._enabled

    def encrypt_content(self, plaintext: str) -> str:
        if not self._enabled:
            return plaintext
        key, salt = _derive_key(self.master_key)
        ciphertext, nonce, tag = _aes_gcm_encrypt(key, plaintext.encode())
        payload = base64.b64encode(salt + nonce + tag + ciphertext).decode()
        return f"#AKATSUKI-ENCRYPTED#{payload}"

    def decrypt_content(self, data: str) -> str:
        if not self._enabled:
            return data
        if not data.startswith("#AKATSUKI-ENCRYPTED#"):
            return data
        try:
            raw = base64.b64decode(data[len("#AKATSUKI-ENCRYPTED#"):])
            salt, nonce, tag, ciphertext = raw[:16], raw[16:28], raw[28:44], raw[44:]
            key = hashlib.pbkdf2_hmac("sha256", self.master_key.encode(), salt, 100000, dklen=AES_KEY_SIZE)
            plaintext = _aes_gcm_decrypt(key, ciphertext, nonce, tag)
            if plaintext is None:
                return data
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return data

    def encrypt_note(self, note_dict: dict) -> dict:
        if not self._enabled:
            return note_dict
        result = dict(note_dict)
        if "content" in result and result["content"]:
            result["content"] = self.encrypt_content(result["content"])
        return result

    def decrypt_note(self, note_dict: dict) -> dict:
        if not self._enabled:
            return note_dict
        result = dict(note_dict)
        if "content" in result and result["content"]:
            result["content"] = self.decrypt_content(result["content"])
        return result