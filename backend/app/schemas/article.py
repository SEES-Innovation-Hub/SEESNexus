from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.models.article import ArticleStatus

MAX_TAGS = 10
MAX_TAG_LENGTH = 40


def _clean_tags(value: list[str] | None) -> list[str] | None:
    """Normalise tags: strip, drop blanks, de-duplicate preserving order.

    Same treatment and the same reasoning as _clean_tech_stack in
    schemas/project.py: these render as badges on a public page, so entry and
    list sizes are capped rather than accepting unbounded free text.

    Limits raise PydanticCustomError rather than a bare ValueError, because the
    global RequestValidationError handler json-encodes exc.errors() directly and
    a ValueError lands in the error's ctx as a non-serializable object.
    """
    if value is None:
        return None

    cleaned: list[str] = []
    for raw in value:
        tag = raw.strip()
        if not tag:
            continue
        if len(tag) > MAX_TAG_LENGTH:
            raise PydanticCustomError(
                "tag_too_long",
                "tags entries must be at most {max_length} characters",
                {"max_length": MAX_TAG_LENGTH},
            )
        if tag not in cleaned:
            cleaned.append(tag)

    if len(cleaned) > MAX_TAGS:
        raise PydanticCustomError(
            "too_many_tags",
            "tags accepts at most {max_items} entries",
            {"max_items": MAX_TAGS},
        )
    return cleaned


class ArticleCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    excerpt: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list)
    # §5.6 calls the create route "Create draft", so a piece is unpublished
    # unless the author explicitly says otherwise.
    status: ArticleStatus = ArticleStatus.DRAFT

    # slug is absent on purpose: it is derived from the title, never supplied.

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _clean_tags(value) or []


class ArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    excerpt: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    status: ArticleStatus | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        return _clean_tags(value)


class ArticlePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    content: str
    excerpt: str | None
    cover_image_url: str | None
    status: ArticleStatus
    tags: list[str]
    author_id: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaginatedArticles(BaseModel):
    items: list[ArticlePublic]
    page: int
    page_size: int
    total: int
    total_pages: int
