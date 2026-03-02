from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExpiredSecret:
    id: int
    title: str
    creator_id: int
    expires_at: datetime


class SecretExpirationObserver(ABC):
    @abstractmethod
    def on_secrets_expired(self, secrets: list[ExpiredSecret]) -> None:
        """called when expired secrets founded"""
