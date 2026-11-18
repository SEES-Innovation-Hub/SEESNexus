from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_key import assert_admin_key
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token_claims,
    hash_password,
    issued_before_password_change,
    verify_password,
)
from app.models.user import User, UserRole
from app.models.verification_code import CodePurpose
from app.schemas.auth import (
    AccessTokenData,
    AdminKeyCheckRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPairData,
    UserPublic,
    UserUpdateRequest,
)
from app.schemas.envelope import success
from app.services import email, otp, rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin-key/check")
async def check_admin_key(
    payload: AdminKeyCheckRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    """Let the sign-up form check the key before the email code is spent.

    /notify/verify-code uses the code up, so a key that is only checked at
    /register would make someone who mistyped it start over with a new code.
    Guessing through here is hopeless: the key is at least 24 characters, and
    each IP gets ten tries per quarter hour.
    """
    await rate_limit.hit(db, rate_limit.ADMIN_KEY_PER_IP, rate_limit.client_ip(request))
    assert_admin_key(payload.admin_key)
    return success(message="Admin key accepted")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Checked first: a bad key must never fall through to a student account.
    is_admin = bool(payload.admin_key and payload.admin_key.strip())
    if is_admin:
        assert_admin_key(payload.admin_key)

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
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Per IP stops one machine guessing across many accounts; per email stops
    # many machines guessing one account's password.
    await rate_limit.hit(db, rate_limit.LOGIN_PER_IP, rate_limit.client_ip(request))
    await rate_limit.hit(db, rate_limit.LOGIN_PER_EMAIL, payload.email)

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

    # A real login wipes this account's count, so typos earlier don't lock
    # the owner out later. The per-IP count stays.
    await rate_limit.clear(db, rate_limit.LOGIN_PER_EMAIL, payload.email)

    tokens = TokenPairData(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return success(data=tokens.model_dump(), message="Login successful")


FORGOT_PASSWORD_MESSAGE = "If an account uses that email, a reset code is on its way."


async def _send_reset_email(to_email: str, code: str) -> None:
    try:
        await email.send_otp_email(to_email, code, reset=True)
    except email.EmailSendError:
        pass  # already logged by the email service; the response can't say anything


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Email a reset code to the account's owner.

    The answer is the same whether or not an account exists, and the email is
    sent after the response, so neither the message nor the timing tells a
    stranger which addresses are registered.
    """
    await rate_limit.hit(db, rate_limit.SEND_CODE_PER_IP, rate_limit.client_ip(request))
    await rate_limit.hit(db, rate_limit.SEND_CODE_PER_EMAIL, payload.email)

    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    data: dict = {"email": payload.email}
    if user is not None and user.is_active:
        code = await otp.issue_code(db, payload.email, CodePurpose.RESET_PASSWORD)
        background_tasks.add_task(_send_reset_email, payload.email, code)
        # Local development only, exactly as /notify/send-code: never when
        # Brevo is configured, so production can't leak it.
        if settings.OTP_DEBUG_RETURN_CODE and not email.is_configured():
            data["debug_code"] = code
    return success(data=data, message=FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Set a new password with the emailed code. Signs out every existing session."""
    await rate_limit.hit(db, rate_limit.VERIFY_CODE_PER_IP, rate_limit.client_ip(request))

    result = await otp.check_code(db, payload.email, payload.code, CodePurpose.RESET_PASSWORD)
    if result is not otp.CodeCheck.OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=otp.CHECK_MESSAGES[result])

    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if user is None or not user.is_active:
        # Only reachable if the account was deactivated after the code was sent.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=otp.CHECK_MESSAGES[otp.CodeCheck.MISSING]
        )

    user.password = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()
    # Let the owner log straight in, even if a guesser had used up the limit.
    await rate_limit.clear(db, rate_limit.LOGIN_PER_EMAIL, payload.email)
    return success(message="Password changed. Log in with your new password.")


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_id, issued_at = decode_token_claims(payload.refresh_token, TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid")
    if issued_before_password_change(issued_at, user.password_changed_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your password was changed. Please log in again.",
        )

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
