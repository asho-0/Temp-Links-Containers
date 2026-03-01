import logging

import bcrypt

from app.db.models import UserTable
from app.db.repositories.auth.user_repo import UserRepository
from app.core.security import create_access_token
from app.services.auth.exceptions import (
    EmailAlreadyRegistered,
    UsernameTaken,
    InvalidCredentials,
)

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def register(
        self, username: str, email: str, password: str
    ) -> UserTable:
        if await self._repo.get_by_email(email):
            raise EmailAlreadyRegistered("Email already registered")
        if await self._repo.get_by_username(username):
            raise UsernameTaken("Username already taken")

        user = await self._repo.add(
            UserTable(
                username=username,
                email=email,
                hashed_password=_hash_password(password),
            )
        )
        logger.info("User %s registered", user.id)
        return user

    async def login(self, email: str, password: str) -> str:
        user = await self._repo.get_by_email(email)
        if not user or not _verify_password(password, user.hashed_password):
            raise InvalidCredentials("Invalid email or password")

        token = create_access_token(subject=user.id)
        logger.info("User %s logged in", user.id)
        return token

    async def delete_user(self, user_id: int) -> None:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise InvalidCredentials("User is not exists")

        await self._repo.delete(user)
        logger.info("User %s deleted", user_id)
