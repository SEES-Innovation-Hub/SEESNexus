import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.models.article import ArticleStatus

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _check_slug(value: str | None) -> str | None:
    # PydanticCustomError, not ValueError: see _clean_tech_stack in schemas/project.py.
    if value is not None and not SLUG_PATTERN.match(value):
        raise PydanticCustomError(
            "invalid_slug",
            "slug may contain only lowercase letters, digits and single hyphens",
        )
    return value


class ArticleCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: ArticleStatus = ArticleStatus.DRAFT
    # Optional: generated from the title when omitted.
    slug: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        return _check_slug(value)


class ArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    status: ArticleStatus | None = None
    # Changing the slug breaks links that were already shared, so it is never
    # changed implicitly -- only when sent here.
    slug: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        return _check_slug(value)


class ArticleAuthor(BaseModel):
    """Deliberately excludes email, like ProjectMemberPublic."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    profile_image_url: str | None


class ArticlePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    summary: str | None
    content: str
    cover_image_url: str | None
    status: ArticleStatus
    author_id: str
    author: ArticleAuthor | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ArticleListItem(BaseModel):
    """A list row: everything but the body. A page of 20 full articles is a lot
    to ship just to draw cards; GET /articles/{id_or_slug} returns the content."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    summary: str | None
    cover_image_url: str | None
    status: ArticleStatus
    author_id: str
    author: ArticleAuthor | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class PaginatedArticles(BaseModel):
    items: list[ArticleListItem]
    page: int
    page_size: int
    total: int
    total_pages: int
