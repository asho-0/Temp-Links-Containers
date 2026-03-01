from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SecretCreateScheme(BaseModel):
    title: str = Field(..., max_length=50)
    content: str = Field(
        ..., description="Plaintext — encrypted before storage"
    )
    expires_at: datetime
    encryption_password: str = Field(..., min_length=8)

    @field_validator("expires_at")
    @classmethod
    def expires_at_must_be_future(cls, v: datetime) -> datetime:
        if v <= datetime.now(v.tzinfo):
            raise ValueError("expires_at must be in the future")
        return v.replace(tzinfo=None)


class SecretReadScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    expires_at: datetime
    is_read: bool


class SecretDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    expires_at: datetime
    is_read: bool


class SecretDecryptRequestScheme(BaseModel):
    encryption_password: str = Field(
        ..., min_length=8, description="User's key to decrypt"
    )
