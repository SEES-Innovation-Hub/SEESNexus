import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodePurpose(str, enum.Enum):
    # Proves the address before an account is created (/notify/send-code).
    REGISTER = "REGISTER"
    # Lets the owner of an existing account set a new password.
    RESET_PASSWORD = "RESET_PASSWORD"


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    # Stored as a plain string (not a DB enum) so adding a purpose needs no migration.
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, default=CodePurpose.REGISTER.value)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Wrong guesses against this code. At MAX_ATTEMPTS it stops working, so a
    # 6-digit code can't be brute-forced within its 10 minutes.
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
