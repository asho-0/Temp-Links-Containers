import typing as t
from abc import ABC, abstractmethod


class EncryptionStrategy(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> dict[str, t.Any]:
        """Шифрует текст, возвращает payload для хранения."""

    @abstractmethod
    def decrypt(self, payload: dict[str, t.Any]) -> str:
        """Расшифровывает payload, возвращает plaintext."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Человекочитаемое название стратегии."""
