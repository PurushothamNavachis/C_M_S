from pydantic import BaseModel, ConfigDict, Field, EmailStr

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None
    role: str | None = None
    exp: int | None = None

class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str
