import logging

from app.bl.encryption.encrypter import get_strategy
from app.bl.encryption.base_strategy import EncryptionStrategy
from app.db.models import SecretTable
from app.db.repositories.bl.secret_repo import SecretRepository

logger = logging.getLogger(__name__)


class SecretService:
    def __init__(self, repo: SecretRepository) -> None:
        self._repo = repo

    async def create(
        self,
        *,
        creator_id: int,
        title: str,
        plaintext: str,
        password: str,
        paranoid: bool = True,
    ) -> SecretTable:
        strategy: EncryptionStrategy = get_strategy(password, paranoid=paranoid)
        encrypted_payload = strategy.encrypt(plaintext)

        secret = await self._repo.add(
            creator_id=creator_id,
            title=title,
            encrypted_payload=encrypted_payload,
        )
        logger.info(
            "Secret %s created for user %s (strategy=%s)",
            secret.id,
            creator_id,
            "paranoid" if paranoid else "standard",
        )
        return secret

    async def delete(self, *, secret_id: int, owner_id: int) -> None:
        deleted = await self._repo.delete(
            secret_id=secret_id, owner_id=owner_id
        )
        if deleted == 0:
            raise PermissionError(
                f"Secret {secret_id} not found or access denied."
            )

    async def list_for_user(self, owner_id: int):
        return await self._repo.list_for_user(owner_id)

    async def get_and_decrypt(
        self,
        *,
        secret_id: int,
        owner_id: int,
        password: str | None,
        paranoid: bool = True,
    ) -> tuple[SecretTable, str]:
        secret = await self._repo.get_by_id_and_owner(
            secret_id=secret_id, owner_id=owner_id
        )

        if secret is None:
            raise PermissionError(
                f"Secret {secret_id} not found or access denied."
            )

        strategy: EncryptionStrategy = get_strategy(
            password or "", paranoid=paranoid
        )
        plaintext = strategy.decrypt(self._repo.decode_payload(secret))

        if not secret.is_read:
            await self._repo.mark_as_read(secret_id)
            logger.info("Secret %s marked as read", secret_id)

        return secret, plaintext

    async def exists_for_owner(self, secret_id: int, owner_id: int) -> bool:
        return await self._repo.exists_for_owner(
            secret_id=secret_id, owner_id=owner_id
        )
