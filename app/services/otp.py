import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.verification_code import VerificationCode


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def issue_code(db: AsyncSession, email: str) -> str:
    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    record = VerificationCode(email=email, code=code, expires_at=expires_at, is_used=False)
    db.add(record)
    await db.commit()
    # In production this is sent via Brevo (Tech Doc §9.1); here we hand it
    # back to the caller so the route can decide whether to email it or
    # (in dev/test) return it directly.
    return code


async def verify_code(db: AsyncSession, email: str, code: str) -> bool:
    result = await db.execute(
        select(VerificationCode)
        .where(VerificationCode.email == email, VerificationCode.code == code)
        .order_by(VerificationCode.expires_at.desc())
    )
    record = result.scalars().first()

    if record is None or record.is_used:
        return False

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        # SQLite drops tzinfo on round-trip even for timezone-aware columns;
        # treat naive values as UTC to keep the comparison valid everywhere.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return False

    record.is_used = True
    await db.commit()
    return True


async def was_code_verified(db: AsyncSession, email: str, code: str) -> bool:
    """
    Used at /auth/register time to confirm this exact code was already
    consumed by a prior successful /notify/verify-code call for this email
    (Tech Doc §5.1: register "requires prior OTP verification").
    """
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.is_used.is_(True),
        )
    )
    return result.scalars().first() is not None
