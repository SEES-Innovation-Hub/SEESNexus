"""Articles: news, write-ups and announcements published by SEES."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class ArticleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # URL-friendly handle, e.g. /articles/floodguard-wins-ieee-award. Generated
    # from the title on create and then left alone, so shared links keep working
    # when a title is edited. Unique across deleted articles too, so restoring
    # one later can never clash.
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Short teaser for cards and link previews.
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # The body, as Markdown. The frontend renders it; the API stores it as given.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Cloudinary URL supplied by the client, like Project.thumbnail_url.
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), default=ArticleStatus.DRAFT, nullable=False
    )
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Set the first time the article is published and kept after that, so
    # unpublishing to fix a typo and republishing does not bump it to the top.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # selectin: the author's name is serialised on every read, and a default lazy
    # load raises MissingGreenlet under async SQLAlchemy.
    author: Mapped[User] = relationship(lazy="selectin")
