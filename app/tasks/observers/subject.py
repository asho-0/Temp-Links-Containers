import logging
from app.tasks.observers.base import SecretExpirationObserver, ExpiredSecret

logger = logging.getLogger(__name__)


class SecretExpirationSubject:
    def __init__(self) -> None:
        self._observers: list[SecretExpirationObserver] = []

    def attach(self, observer: SecretExpirationObserver) -> None:
        self._observers.append(observer)
        logger.debug("Observer attached: %s", type(observer).__name__)

    def detach(self, observer: SecretExpirationObserver) -> None:
        self._observers.remove(observer)
        logger.debug("Observer detached: %s", type(observer).__name__)

    def notify(self, secrets: list[ExpiredSecret]) -> None:
        if not secrets:
            logger.debug("No expired secrets — observers not notified")
            return

        logger.info(
            "Notifying %s observer(s) about %s expired secret(s)",
            len(self._observers),
            len(secrets),
        )
        for observer in self._observers:
            try:
                observer.on_secrets_expired(secrets)
            except Exception as exc:
                logger.error(
                    "Observer %s failed: %s",
                    type(observer).__name__,
                    exc,
                    exc_info=True,
                )
