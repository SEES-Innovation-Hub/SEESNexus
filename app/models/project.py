import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class ProjectStatus(str, enum.Enum):
    IDEATION = "IDEATION"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProjectCategory(str, enum.Enum):
    IOT = "IOT"
    AI_ML = "AI_ML"
    EMBEDDED = "EMBEDDED"
    WEB = "WEB"
    MOBILE = "MOBILE"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.IDEATION, nullable=False
    )
    category: Mapped[ProjectCategory] = mapped_column(Enum(ProjectCategory), nullable=False)
    # Cloudinary URL supplied by the client; this backend never uploads (Tech Doc §6).
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # The join table carries no payload, so members are exposed as users directly.
    # lazy="selectin" is required: members serialize on every read, and a default
    # lazy load raises MissingGreenlet under async SQLAlchemy.
    members: Mapped[list[User]] = relationship(secondary="project_members", lazy="selectin")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
