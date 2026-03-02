import logging
from datetime import datetime, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import SecretTable
from app.tasks.celery_app import celery_app
from app.tasks.observers.base import ExpiredSecret
from app.tasks.observers.subject import SecretExpirationSubject
from app.tasks.observers.cleanup_observer import CleanupObserver
from app.tasks.observers.audit_observer import AuditObserver
from app.tasks.observers.notification_observer import NotificationObserver

logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.DATABASE_URL_psycopg)


def _build_subject(session: Session) -> SecretExpirationSubject:
    subject = SecretExpirationSubject()
    subject.attach(CleanupObserver(session))  # удалить из БД
    subject.attach(AuditObserver())  # залогировать
    subject.attach(NotificationObserver())  # уведомить владельца
    return subject


@celery_app.task(
    name="app.tasks.cleanup.delete_expired_secrets",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def delete_expired_secrets(self) -> dict[str, int | str]:
    try:
        with Session(sync_engine) as session:
            with session.begin():
                rows = session.execute(
                    select(
                        SecretTable.id,
                        SecretTable.title,
                        SecretTable.creator_id,
                        SecretTable.expires_at,
                    ).where(SecretTable.expires_at < datetime.now(timezone.utc))
                ).all()

                expired = [
                    ExpiredSecret(
                        id=row.id,
                        title=row.title,
                        creator_id=row.creator_id,
                        expires_at=row.expires_at,
                    )
                    for row in rows
                ]

                subject = _build_subject(session)
                subject.notify(expired)

        return {"deleted": len(expired), "status": "ok"}

    except Exception as exc:
        logger.error("Cleanup task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
