import logging
from sqlalchemy.orm import Session
from app.db.repositories.cleaner.worker_repo import SyncSecretRepository

logger = logging.getLogger(__name__)

class SyncSecretService:
    def __init__(self, session: Session):
        self._repo = SyncSecretRepository(session)

    def cleanup_expired_secrets(self, days: int = 30) -> int:
        logger.info("Service: Starting cleanup process for secrets older than %d days.", days)
        
        deleted_count = self._repo.delete_expired_secrets(days)
        
        if deleted_count > 0:
            logger.info("Service: Cleanup completed successfully. %d items removed.", deleted_count)
        else:
            logger.info("Service: No expired secrets found to clean up.")
            
        return deleted_count