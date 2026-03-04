import os
import base64
import hashlib
import typing as t

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.bl.encryption.base_strategy import EncryptionStrategy


class StandardStrategy(EncryptionStrategy):
    _ITERATIONS = 600_000

    def __init__(self, password: str) -> None:
        if not password:
            raise ValueError("Password must not be empty.")
        self._key = self._derive_fernet_key(password.encode())
        self._fernet = Fernet(self._key)

    @staticmethod
    def _derive_fernet_key(password: bytes) -> bytes:
        salt = b"standard-strategy-fixed-salt"
        raw = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password,
            salt=salt,
            iterations=StandardStrategy._ITERATIONS,
            dklen=32,
        )
        return base64.urlsafe_b64encode(raw)

    @property
    def name(self) -> str:
        return "Standard (Fernet + PBKDF2-SHA256)"

    def encrypt(self, plaintext: str) -> dict[str, t.Any]:
        token = self._fernet.encrypt(plaintext.encode())
        return {
            "strategy": "standard",
            "token": token.decode(),
        }

    def decrypt(self, payload: dict[str, t.Any]) -> str:
        token = payload["token"].encode()
        return self._fernet.decrypt(token).decode()


class ParanoidStrategy(EncryptionStrategy):
    _ITERATIONS = 600_000

    def __init__(self, password: str) -> None:
        if not password:
            raise ValueError("Password must not be empty.")
        self._password = password.encode()

    @property
    def name(self) -> str:
        return "Paranoid (AES-256-GCM + PBKDF2-SHA256 — zero-knowledge)"

    def _derive_key(self, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=self._password,
            salt=salt,
            iterations=self._ITERATIONS,
            dklen=32,
        )

    def encrypt(self, plaintext: str) -> dict[str, t.Any]:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = self._derive_key(salt)
        cipher = AESGCM(key).encrypt(
            nonce, plaintext.encode(), associated_data=None
        )
        return {
            "strategy": "paranoid",
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(cipher).decode(),
        }

    def decrypt(self, payload: dict[str, t.Any]) -> str:
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])
        key = self._derive_key(salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, associated_data=None)
        return plaintext.decode()


def get_strategy(password: str, paranoid: bool = True) -> EncryptionStrategy:
    return (
        ParanoidStrategy(password) if paranoid else StandardStrategy(password)
    )
