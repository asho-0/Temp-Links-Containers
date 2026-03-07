import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="send_verification_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_verification_email_task(self, email: str, token: str):
    import asyncio
    from app.services.auth.email import EmailService

    try:
        asyncio.run(EmailService().send_verification_email(email, token))
        logger.info("Verification email sent to %s", email)
    except Exception as exc:
        logger.warning("Failed to send email to %s: %s", email, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="cleanup_old_secrets")
def cleanup_old_secrets():
    from app.db.session import SyncSessionLocal
    from app.services.cleaner.worker import SyncSecretService

    with SyncSessionLocal() as session:
        service = SyncSecretService(session)
        count = service.cleanup_expired_secrets(days=30)

    logger.info("cleanup_old_secrets: removed %d expired secrets", count)
    return count
