import logging
from datetime import datetime, timezone

from app.tasks.observers.base import SecretExpirationObserver, ExpiredSecret

logger = logging.getLogger("audit")


class AuditObserver(SecretExpirationObserver):
    def on_secrets_expired(self, secrets: list[ExpiredSecret]) -> None:
        for secret in secrets:
            logger.info(
                "[AUDIT] secret_id=%s title=%r creator_id=%s expired_at=%s processed_at=%s",
                secret.id,
                secret.title,
                secret.creator_id,
                secret.expires_at.isoformat(),
                datetime.now(timezone.utc).isoformat(),
            )
