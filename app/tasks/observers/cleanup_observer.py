import logging
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.db.models import SecretTable
from app.tasks.observers.base import SecretExpirationObserver, ExpiredSecret

logger = logging.getLogger(__name__)


class CleanupObserver(SecretExpirationObserver):
    def __init__(self, session: Session) -> None:
        self._session = session

    def on_secrets_expired(self, secrets: list[ExpiredSecret]) -> None:
        if not secrets:
            return

        ids = [s.id for s in secrets]
        self._session.execute(
            delete(SecretTable).where(SecretTable.id.in_(ids))
        )
        logger.info("CleanupObserver: deleted %s secret(s) %s", len(ids), ids)
