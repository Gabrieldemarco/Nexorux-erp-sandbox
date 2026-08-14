from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    full_name: str = Field(..., min_length=1, max_length=255)
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    is_active: bool = True
    settings: Optional[dict] = None

    @field_validator('tenant_id', 'company_id', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return None
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=150)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    settings: Optional[dict] = None


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=150)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[dict] = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class PasswordRecoveryRequest(BaseModel):
    """Request reset for a registered account email."""

    email: Optional[EmailStr] = None

    @field_validator("email", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip() or None
        return v

    def resolved_email(self) -> str:
        value = (self.email or "").strip()
        if not value or "@" not in value:
            raise ValueError("Debés indicar el correo registrado")
        return value.lower()


class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=8)


class PasswordRecoveryResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    settings: Optional[dict] = None
    permission_codes: List[str] = Field(default_factory=list)
    role_keys: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
