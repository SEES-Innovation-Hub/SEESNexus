from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.models.project import Project, ProjectCategory, ProjectStatus
from app.models.user import User, UserRole
from app.schemas.envelope import success
from app.schemas.project import (
    PaginatedProjects,
    ProjectCreateRequest,
    ProjectPublic,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _serialize(project: Project) -> dict:
    return ProjectPublic.model_validate(project).model_dump(mode="json")


def _assert_can_edit(project: Project, user: User) -> None:
    if project.created_by_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this project",
        )


async def _get_project_or_404(db: AsyncSession, project_id: str) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _team_with_creator(db: AsyncSession, member_ids: list[str], creator_id: str) -> list[User]:
    """The team as sent, with the creator always on it (listed first).

    member_ids replaces the whole team, so without this an edit -- including
    an admin's -- could quietly take the creator off their own project.
    """
    ids = [creator_id, *(member_id for member_id in member_ids if member_id != creator_id)]
    return await _resolve_members(db, ids)


async def _resolve_members(db: AsyncSession, member_ids: list[str]) -> list[User]:
    """Map member ids to users, rejecting unknown ones with 400.

    An unvalidated id would otherwise hit the database as a foreign-key
    violation and escape as an unenveloped 500.
    """
    unique_ids = list(dict.fromkeys(member_ids))
    if not unique_ids:
        return []

    result = await db.execute(select(User).where(User.id.in_(unique_ids)))
    found = {user.id: user for user in result.scalars().all()}

    missing = [member_id for member_id in unique_ids if member_id not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown member id(s): {', '.join(missing)}",
        )

    return [found[member_id] for member_id in unique_ids]


@router.get("")
@router.get("/", include_in_schema=False)
async def list_projects(
    page: int = Query(default=1, ge=1),
    # No le= bound here on purpose: an oversized page_size is clamped server-side
    # by paginate() rather than rejected, per the contract.
    page_size: int = Query(default=20, ge=1),
    category: ProjectCategory | None = None,
    status_filter: ProjectStatus | None = Query(default=None, alias="status"),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Members only: any logged-in user can browse the project directory."""
    stmt = select(Project)
    if category is not None:
        stmt = stmt.where(Project.category == category)
    if status_filter is not None:
        stmt = stmt.where(Project.status == status_filter)
    stmt = stmt.order_by(Project.created_at.desc())

    projects, total = await paginate(db, stmt, page, page_size)
    effective_page_size = min(page_size, MAX_PAGE_SIZE)

    data = PaginatedProjects(
        items=[ProjectPublic.model_validate(p) for p in projects],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Any authenticated user may create a project — no role gate."""
    members = await _team_with_creator(db, payload.member_ids, current_user.id)

    project = Project(
        title=payload.title,
        description=payload.description,
        tech_stack=payload.tech_stack,
        category=payload.category,
        status=payload.status,
        github_url=payload.github_url,
        demo_url=payload.demo_url,
        thumbnail_url=payload.thumbnail_url,
        # Never taken from the body.
        created_by_id=current_user.id,
        members=members,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return success(data=_serialize(project), message="Project created")


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    return success(data=_serialize(project))


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Existence before permission: a missing project is a 404, never a 403.
    project = await _get_project_or_404(db, project_id)
    _assert_can_edit(project, current_user)

    fields = payload.model_dump(exclude_unset=True)
    member_ids = fields.pop("member_ids", None)

    for field, value in fields.items():
        setattr(project, field, value)

    if member_ids is not None:
        # member_ids replaces the full set; there are no add/remove sub-routes.
        project.members = await _team_with_creator(db, member_ids, project.created_by_id)

    await db.commit()
    await db.refresh(project)
    return success(data=_serialize(project), message="Project updated")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    _assert_can_edit(project, current_user)

    # members is selectin-loaded, so the ORM removes the project_members rows
    # with the parent -- no reliance on SQLite honouring ON DELETE CASCADE.
    await db.delete(project)
    await db.commit()
    # 200 + envelope rather than 204: every response carries {status, message, data}.
    return success(message="Project deleted")
