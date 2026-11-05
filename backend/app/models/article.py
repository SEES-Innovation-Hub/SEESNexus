import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Article(Base):
    """Contributor-authored technical article (Tech Doc §4.2).

    Replaces the four-column stand-in that previously lived in models/stubs.py
    and existed only so /admin/dashboard could count real rows.

    status and deleted_at are separate on purpose. ARCHIVED is an editorial
    state: the author took a published piece down and may put it back.
    deleted_at means removed. §4.3 forbids hard-deleting a user's articles, so
    DELETE sets the column instead of dropping the row.
    """

    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # The public routes address an article by slug, not id (§5.6).
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Cloudinary URL supplied by the client; this backend never uploads.
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), default=ArticleStatus.DRAFT, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    # Set the first time the article is published, and left alone afterwards, so
    # later edits do not reorder the public list.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
