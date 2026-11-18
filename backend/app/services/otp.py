"""One-time email codes: issuing, checking, and the attempt lock.

Each (email, purpose) has at most one live code: issuing a new one deletes the
old. A code dies after MAX_ATTEMPTS wrong guesses, so a 6-digit code (a million
possibilities) can't be brute-forced in its lifetime -- five tries is a 1 in
200,000 chance. Wrong guesses are counted on the email's current code, since
a guess that matches nothing has no row of its own to count on.
"""
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.verification_code import CodePurpose, VerificationCode

MAX_ATTEMPTS = 5


class CodeCheck(str, Enum):
    OK = "ok"
    WRONG = "wrong"
    # No live code: never sent, expired, or already used.
    MISSING = "missing"
    # Too many wrong guesses; a new code has to be requested.
    LOCKED = "locked"


CHECK_MESSAGES = {
    CodeCheck.WRONG: "That code isn't right. Check the email and try again.",
    CodeCheck.MISSING: "That code has expired or was already used. Request a new one.",
    CodeCheck.LOCKED: "Too many wrong tries. Request a new code.",
}


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _as_utc(value: datetime) -> datetime:
    # SQLite drops tzinfo on round-trip even for timezone-aware columns.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


async def issue_code(db: AsyncSession, email: str, purpose: CodePurpose = CodePurpose.REGISTER) -> str:
    """A fresh code for `email`, replacing any unused one for the same purpose.

    Deleting (rather than flagging) the old code keeps was_code_verified
    simple: only codes that really were verified are ever marked used.
    """
    await db.execute(
        delete(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose.value,
            VerificationCode.is_used.is_(False),
        )
    )
    code = generate_code()
    db.add(
        VerificationCode(
            email=email,
            code=code,
            purpose=purpose.value,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            is_used=False,
            attempts=0,
        )
    )
    await db.commit()
    return code


async def check_code(
    db: AsyncSession, email: str, code: str, purpose: CodePurpose = CodePurpose.REGISTER
) -> CodeCheck:
    """Check a guess against the email's live code. Consumes it on success."""
    record = (
        await db.execute(
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.purpose == purpose.value,
                VerificationCode.is_used.is_(False),
            )
            .order_by(VerificationCode.expires_at.desc())
            .with_for_update()
        )
    ).scalars().first()

    if record is None or _as_utc(record.expires_at) < datetime.now(timezone.utc):
        return CodeCheck.MISSING
    if record.attempts >= MAX_ATTEMPTS:
        return CodeCheck.LOCKED

    if not secrets.compare_digest(code.strip().encode(), record.code.encode()):
        record.attempts += 1
        await db.commit()
        return CodeCheck.LOCKED if record.attempts >= MAX_ATTEMPTS else CodeCheck.WRONG

    record.is_used = True
    await db.commit()
    return CodeCheck.OK


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
            VerificationCode.purpose == CodePurpose.REGISTER.value,
            VerificationCode.is_used.is_(True),
        )
    )
    return result.scalars().first() is not None
