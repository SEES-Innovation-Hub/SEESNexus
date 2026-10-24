from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    department: str = Field(min_length=1, max_length=255)
    level: str | None = None
    # Proof that /notify/verify-code succeeded for this email, per Tech Doc §5.1
    # ("Create account (requires prior OTP verification)").
    verification_code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPairData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    department: str
    level: str | None
    role: UserRole
    profile_image_url: str | None
    bio: str | None
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    level: str | None = None
    bio: str | None = None
    profile_image_url: str | None = None


class UserSearchResult(BaseModel):
    """Narrow projection for the teammate picker.

    Deliberately leaves out email, role, bio, is_active, department -- any
    logged-in user can call /users/search, and only the minimum needed to
    render a result row belongs in the response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    profile_image_url: str | None
