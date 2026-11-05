import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HardwareCategory(str, enum.Enum):
    MEASUREMENT = "MEASUREMENT"
    MICROCONTROLLER = "MICROCONTROLLER"
    COMPONENT = "COMPONENT"


class HardwareStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    MAINTENANCE = "MAINTENANCE"


class Hardware(Base):
    __tablename__ = "hardware"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[HardwareCategory] = mapped_column(Enum(HardwareCategory), nullable=False)
    status: Mapped[HardwareStatus] = mapped_column(
        Enum(HardwareStatus), default=HardwareStatus.AVAILABLE, nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    added_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)


class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
    # A borrower withdrawing their own pending request. Kept distinct from
    # REJECTED so the loan history says who ended the request: REJECTED is an
    # admin's decision, CANCELLED is the student's own.
    CANCELLED = "CANCELLED"


class HardwareLoan(Base):
    __tablename__ = "hardware_loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hardware_id: Mapped[str] = mapped_column(String(36), ForeignKey("hardware.id"), nullable=False)
    borrower_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.PENDING, nullable=False)
    purpose: Mapped[str] = mapped_column(String(1000), nullable=False)
    request_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Eager-loaded so LoanPublic.hardware_name can be filled without a per-row
    # round trip when the loan list routes serialise many loans at once.
    hardware: Mapped["Hardware"] = relationship(lazy="selectin")
