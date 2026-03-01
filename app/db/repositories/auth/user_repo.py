from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserTable


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> UserTable | None:
        return await self._session.scalar(
            select(UserTable).where(UserTable.email == email)
        )

    async def get_by_username(self, username: str) -> UserTable | None:
        return await self._session.scalar(
            select(UserTable).where(UserTable.username == username)
        )

    async def get_by_id(self, user_id: int) -> UserTable | None:
        return await self._session.scalar(
            select(UserTable).where(UserTable.id == user_id)
        )

    async def add(self, user: UserTable) -> UserTable:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, user: UserTable) -> None:
        await self._session.delete(user)
        await self._session.flush()
