import base64
import logging
from typing import Any

from sqlalchemy import delete, select, update, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SecretTable

logger = logging.getLogger(__name__)


def _encode_for_db(payload: dict[str, str]) -> dict[str, bytes]:
    return {
        "encrypted_content": base64.b64decode(payload["ciphertext"]),
        "nonce": base64.b64decode(payload["nonce"]),
        "salt": base64.b64decode(payload["salt"]),
    }


def _decode_from_db(row: SecretTable) -> dict[str, str]:
    return {
        "ciphertext": base64.b64encode(row.encrypted_content).decode(),
        "nonce": base64.b64encode(row.nonce).decode(),
        "salt": base64.b64encode(row.salt).decode(),
    }


class SecretRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        creator_id: int,
        title: str,
        encrypted_payload: dict[str, str],
    ) -> SecretTable:
        enc = _encode_for_db(encrypted_payload)
        secret = SecretTable(
            title=title,
            creator_id=creator_id,
            **enc,
        )
        self._session.add(secret)
        await self._session.flush()
        await self._session.refresh(secret)
        logger.debug("Secret %s flushed for user %s", secret.id, creator_id)
        return secret

    async def delete(self, *, secret_id: int, owner_id: int) -> int:
        result = await self._session.execute(
            delete(SecretTable).where(
                SecretTable.id == secret_id,
                SecretTable.creator_id == owner_id,
            )
        )
        await self._session.flush()
        return result.rowcount

    async def mark_as_read(self, secret_id: int) -> None:
        await self._session.execute(
            update(SecretTable)
            .where(SecretTable.id == secret_id)
            .values(is_read=True)
        )
        await self._session.flush()

    async def get_by_id_and_owner(
        self, *, secret_id: int, owner_id: int
    ) -> SecretTable | None:
        result = await self._session.execute(
            select(SecretTable).where(
                SecretTable.id == secret_id,
                SecretTable.creator_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, owner_id: int) -> Sequence[Any]:
        result = await self._session.execute(
            select(
                SecretTable.id,
                SecretTable.title,
                SecretTable.is_read,
                SecretTable.created_at,
            )
            .where(SecretTable.creator_id == owner_id)
            .order_by(SecretTable.created_at.desc())
        )
        return result.all()

    def decode_payload(self, row: SecretTable) -> dict[str, str]:
        return _decode_from_db(row)

    async def exists_for_owner(self, secret_id: int, owner_id: int) -> bool:
        return (
            await self.get_by_id_and_owner(
                secret_id=secret_id, owner_id=owner_id
            )
            is not None
        )
