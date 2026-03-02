from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_dependency, transaction
from app.db.repositories.auth.user_repo import UserRepository
from app.services.auth import AuthService
from app.services.auth.email import EmailService
from app.db.schemas.auth_schm import (
    UserRegisterScheme,
    UserLoginScheme,
    TokenScheme,
)
from app.core.dependencies.user import get_current_user_id
from app.services.auth.exceptions import (
    EmailAlreadyRegistered,
    UsernameTaken,
    InvalidCredentials,
    EmailNotVerified,
    InvalidVerificationToken,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: AsyncSession = Depends(db_dependency),
) -> AuthService:
    return AuthService(
        repo=UserRepository(session),
        email_svc=EmailService(),
    )


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterScheme, service: AuthService = Depends(get_auth_service)
):
    try:
        async with transaction():
            await service.register(
                username=body.username, email=body.email, password=body.password
            )
    except (EmailAlreadyRegistered, UsernameTaken) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return {
        "message": "Registration successful. Please check your email to verify your account."
    }


@auth_router.get("/verify")
async def verify_email(
    token: str, service: AuthService = Depends(get_auth_service)
):
    try:
        await service.verify_email(token)
    except InvalidVerificationToken as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return {"message": "Email verified successfully. You can now log in."}


@auth_router.post("/login", response_model=TokenScheme)
async def login(
    body: UserLoginScheme, service: AuthService = Depends(get_auth_service)
):
    try:
        token = await service.login(email=body.email, password=body.password)
    except EmailNotVerified as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        )
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )
    return TokenScheme(access_token=token)


@auth_router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service),
):
    try:
        async with transaction():
            await service.delete_user(current_user_id)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found {exc}",
        )
