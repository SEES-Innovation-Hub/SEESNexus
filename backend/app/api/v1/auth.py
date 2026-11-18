import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    AccessTokenData,
    AdminKeyCheckRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairData,
    UserPublic,
    UserUpdateRequest,
)
from app.schemas.envelope import success
from app.services import otp

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _assert_admin_key(candidate: str) -> None:
    """403 unless candidate is this deployment's ADMIN_REGISTRATION_KEY.

    Constant-time comparison, so response timing says nothing about how much of
    a guess was right. Failures are logged (never the key itself) so repeated
    attempts show up in the logs.
    """
    expected = settings.ADMIN_REGISTRATION_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin sign-up is not enabled on this server",
        )
    if not secrets.compare_digest(candidate.strip().encode(), expected.encode()):
        logger.warning("Rejected an admin registration key")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")


@router.post("/admin-key/check")
async def check_admin_key(payload: AdminKeyCheckRequest):
    """Let the sign-up form check the key before the email code is spent.

    /notify/verify-code uses the code up, so a key that is only checked at
    /register would make someone who mistyped it start over with a new code.
    Guessing through here is hopeless: the key is at least 24 characters.
    """
    _assert_admin_key(payload.admin_key)
    return success(message="Admin key accepted")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Checked first: a bad key must never fall through to a student account.
    is_admin = bool(payload.admin_key and payload.admin_key.strip())
    if is_admin:
        _assert_admin_key(payload.admin_key)

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if not await otp.was_code_verified(db, payload.email, payload.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email has not been verified. Call /notify/send-code and /notify/verify-code first.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password=hash_password(payload.password),
        department=payload.department,
        level=payload.level,
        role=UserRole.ADMIN if is_admin else UserRole.STUDENT,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return success(
        data=UserPublic.model_validate(user).model_dump(mode="json"),
        message="Admin account created" if is_admin else "Account created",
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

    tokens = TokenPairData(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return success(data=tokens.model_dump(), message="Login successful")


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_id = decode_token(payload.refresh_token, TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid")

    token = AccessTokenData(access_token=create_access_token(user.id))
    return success(data=token.model_dump(), message="Access token refreshed")


@router.get("/validate/token")
async def validate_token(current_user: User = Depends(get_current_user)):
    return success(data={"valid": True, "user_id": current_user.id}, message="Token is valid")


@router.get("/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return success(data=UserPublic.model_validate(current_user).model_dump(mode="json"))


@router.put("/me")
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return success(
        data=UserPublic.model_validate(current_user).model_dump(mode="json"),
        message="Profile updated",
    )
