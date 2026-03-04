from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SecretCreateScheme(BaseModel):
    title: str = Field(..., max_length=50)
    content: str = Field(
        ..., description="Plaintext — encrypted before storage"
    )
    encryption_password: str = Field(..., min_length=8)


class SecretReadScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    is_read: bool


class SecretDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    is_read: bool


class SecretDecryptRequestScheme(BaseModel):
    encryption_password: str = Field(
        ..., min_length=8, description="User's key to decrypt"
    )


class ShareLinkCreateScheme(BaseModel):
    encryption_password: str
    expires_minutes: int = Field(gt=0, le=60 * 24 * 30)
