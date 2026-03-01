from sqlalchemy import String, LargeBinary, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class UserTable(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    secrets: Mapped[list["SecretTable"]] = relationship(
        "SecretTable", back_populates="user", cascade="all, delete-orphan"
    )


class SecretTable(Base):
    __tablename__ = "secret"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)

    encrypted_content: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    creator_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now()
    )
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["UserTable"] = relationship(
        "UserTable", back_populates="secrets"
    )
