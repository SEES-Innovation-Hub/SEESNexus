import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventType(str, enum.Enum):
    HACKATHON = "HACKATHON"
    WORKSHOP = "WORKSHOP"
    SEMINAR = "SEMINAR"
    CONFERENCE = "CONFERENCE"
    # Welcome sessions for new members at the start of a semester.
    ORIENTATION = "ORIENTATION"


class RegistrationStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    is_virtual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    virtual_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Set by an admin to open self check-in; confirmed members type it in at the
    # event. Null = check-in closed. Only ever sent to admins.
    checkin_code: Mapped[str | None] = mapped_column(String(12), nullable=True)

    registrations: Mapped[list["EventRegistration"]] = relationship(
        back_populates="event", lazy="selectin", cascade="save-update, merge"
    )


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (UniqueConstraint("event_id", "student_id", name="uq_event_registration_student"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus), nullable=False, default=RegistrationStatus.CONFIRMED
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # When an admin checked the student in at the event. Null = not (yet) marked
    # as attended. Only a CONFIRMED registration can carry it.
    attended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped[Event] = relationship(back_populates="registrations")
