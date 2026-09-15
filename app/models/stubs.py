"""
Minimal stand-ins for entities owned by the Events/Articles verticals
(other engineers' tasks per the task sheets). They exist here only so the
Admin dashboard aggregation endpoint (§5.7) has real tables to count against
instead of hardcoded numbers -- avoiding the v1 "static dashboard" mistake.
Whoever builds those verticals for real should replace/extend these; keep the
table names identical so data isn't lost. Projects has since been built out
for real in app/models/project.py.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
