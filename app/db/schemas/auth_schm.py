from pydantic import BaseModel, EmailStr, Field


class UserRegisterScheme(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginScheme(BaseModel):
    email: EmailStr
    password: str


class TokenScheme(BaseModel):
    access_token: str
    token_type: str = "bearer"
