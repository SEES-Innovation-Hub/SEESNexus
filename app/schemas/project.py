from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectCategory, ProjectStatus

MAX_TECH_STACK_ITEMS = 20
MAX_TECH_STACK_ITEM_LENGTH = 50


def _clean_tech_stack(value: list[str] | None) -> list[str] | None:
    """Normalise tech_stack: strip, drop blanks, de-duplicate preserving order.

    These render as badges on a public page, so entry and list sizes are capped
    rather than accepting unbounded free text.
    """
    if value is None:
        return None

    cleaned: list[str] = []
    for raw in value:
        item = raw.strip()
        if not item:
            continue
        if len(item) > MAX_TECH_STACK_ITEM_LENGTH:
            raise ValueError(
                f"tech_stack entries must be at most {MAX_TECH_STACK_ITEM_LENGTH} characters"
            )
        if item not in cleaned:
            cleaned.append(item)

    if len(cleaned) > MAX_TECH_STACK_ITEMS:
        raise ValueError(f"tech_stack accepts at most {MAX_TECH_STACK_ITEMS} entries")
    return cleaned


class ProjectMemberPublic(BaseModel):
    """Deliberately excludes email — the project endpoints are public."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    profile_image_url: str | None


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    tech_stack: list[str] = Field(default_factory=list)
    category: ProjectCategory
    status: ProjectStatus = ProjectStatus.IDEATION
    github_url: str | None = Field(default=None, max_length=500)
    demo_url: str | None = Field(default=None, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    member_ids: list[str] = Field(default_factory=list)

    @field_validator("tech_stack")
    @classmethod
    def _validate_tech_stack(cls, value: list[str]) -> list[str]:
        return _clean_tech_stack(value) or []


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    tech_stack: list[str] | None = None
    category: ProjectCategory | None = None
    status: ProjectStatus | None = None
    github_url: str | None = Field(default=None, max_length=500)
    demo_url: str | None = Field(default=None, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    member_ids: list[str] | None = None

    @field_validator("tech_stack")
    @classmethod
    def _validate_tech_stack(cls, value: list[str] | None) -> list[str] | None:
        return _clean_tech_stack(value)


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    tech_stack: list[str]
    github_url: str | None
    demo_url: str | None
    status: ProjectStatus
    category: ProjectCategory
    thumbnail_url: str | None
    created_by_id: str
    members: list[ProjectMemberPublic]
    created_at: datetime
    updated_at: datetime


class PaginatedProjects(BaseModel):
    items: list[ProjectPublic]
    page: int
    page_size: int
    total: int
    total_pages: int
