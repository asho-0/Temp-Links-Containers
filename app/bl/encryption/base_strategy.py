import typing as t
from abc import ABC, abstractmethod


class EncryptionStrategy(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> dict[str, t.Any]: ...

    @abstractmethod
    def decrypt(self, payload: dict[str, t.Any]) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...
