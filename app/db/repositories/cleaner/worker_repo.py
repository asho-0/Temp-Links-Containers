import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import SecretTable, UserTable

logger = logging.getLogger(__name__)


class SyncSecretRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: int) -> UserTable | None:
        return self._session.scalar(
            select(UserTable).where(UserTable.id == user_id)
        )

    def delete_expired_secrets(self, days: int = 30) -> int:
        threshold = datetime.utcnow() - timedelta(days=days)
        try:
            stmt = delete(SecretTable).where(SecretTable.created_at < threshold)
            result = self._session.execute(stmt)
            self._session.commit()

            deleted_count = int(result.rowcount or 0)
            return deleted_count
        except Exception as e:
            logger.error(
                "Failed to cleanup expired secrets: %s", str(e), exc_info=True
            )
            self._session.rollback()
            return 0

    def get_secret_by_id(self, secret_id: int) -> SecretTable | None:
        return self._session.scalar(
            select(SecretTable).where(SecretTable.id == secret_id)
        )
