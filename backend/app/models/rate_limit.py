import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RateLimitEvent(Base):
    """One counted request, e.g. a login attempt from an IP address.

    Kept in Postgres rather than in memory or Redis so limits hold across
    restarts and across several API instances, with nothing extra to run.
    Rows older than a day are pruned (services/rate_limit.py).
    """

    __tablename__ = "rate_limit_events"
    __table_args__ = (Index("ix_rate_limit_events_key_created_at", "key", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # e.g. "login:ip:203.0.113.7" or "send-code:email:ada@unilag.edu.ng"
    key: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
