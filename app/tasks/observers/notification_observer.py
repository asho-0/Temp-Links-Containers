import logging

from app.tasks.observers.base import SecretExpirationObserver, ExpiredSecret

logger = logging.getLogger(__name__)


class NotificationObserver(SecretExpirationObserver):
    def on_secrets_expired(self, secrets: list[ExpiredSecret]) -> None:
        for secret in secrets:
            logger.info(
                "NotificationObserver: notify user %s — secret %r has expired",
                secret.creator_id,
                secret.title,
            )
            # TODO: send_email(user_id=secret.creator_id, ...)
