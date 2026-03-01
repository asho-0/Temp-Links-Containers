import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_dependency, transaction
from app.db.repositories.bl.secret_repo import SecretRepository
from app.services.bl.secret import SecretService
from app.db.schemas.secret_schm import (
    SecretCreateScheme,
    SecretDecryptRequestScheme,
    SecretDetailScheme,
    SecretReadScheme,
)
from app.core.dependencies.user import get_current_user_id

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/secrets", tags=["secrets"])


def get_secret_service(
    session: AsyncSession = Depends(db_dependency),
) -> SecretService:
    return SecretService(SecretRepository(session))


@api_router.post(
    "/",
    response_model=SecretReadScheme,
    status_code=status.HTTP_201_CREATED,
)
async def create_secret(
    body: SecretCreateScheme,
    current_user_id: int = Depends(get_current_user_id),
    service: SecretService = Depends(get_secret_service),
):
    async with transaction():
        secret = await service.create(
            creator_id=current_user_id,
            title=body.title,
            plaintext=body.content,
            password=body.encryption_password,
            expires_at=body.expires_at,
            paranoid=True,
        )
    return secret


@api_router.get(
    "/",
    response_model=list[SecretReadScheme],
)
async def list_secrets(
    current_user_id: int = Depends(get_current_user_id),
    service: SecretService = Depends(get_secret_service),
):
    return await service.list_for_user(current_user_id)


@api_router.post("/decrypt/{secret_id}", response_model=SecretDetailScheme)
async def decrypt_secret(
    secret_id: int,
    body: SecretDecryptRequestScheme,
    current_user_id: int = Depends(get_current_user_id),
    service: SecretService = Depends(get_secret_service),
):
    try:
        async with transaction():
            secret, plaintext = await service.get_and_decrypt(
                secret_id=secret_id,
                owner_id=current_user_id,
                password=body.encryption_password,
            )
    except PermissionError as exc:
        logger.warning(
            "decrypt denied | secret=%s user=%s | %s",
            secret_id,
            current_user_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValueError as exc:
        logger.info(
            "decrypt expired | secret=%s user=%s", secret_id, current_user_id
        )
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc))
    except Exception:
        logger.exception(
            "decrypt failed | secret=%s user=%s", secret_id, current_user_id
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Decryption failed: wrong password or corrupted data.",
        )

    return SecretDetailScheme.model_validate(
        {**secret.__dict__, "content": plaintext}
    )


@api_router.delete(
    "/{secret_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_secret(
    secret_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: SecretService = Depends(get_secret_service),
):
    try:
        async with transaction():
            await service.delete(secret_id=secret_id, owner_id=current_user_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
