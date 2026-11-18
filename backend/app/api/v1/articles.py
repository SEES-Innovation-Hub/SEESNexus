"""Articles: list, read, write, edit and delete.

Who may do what:

| Action          | Who                                                         |
|-----------------|-------------------------------------------------------------|
| List / read     | Any logged-in member sees PUBLISHED articles. A DRAFT is    |
|                 | visible only to its author and to admins.                   |
| Create          | CONTRIBUTOR or ADMIN.                                       |
| Edit / delete   | The article's author, or any ADMIN.                         |

Delete is soft (deleted_at), like events: the row and its slug are kept.
"""
import re
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.schemas.article import (
    ArticleCreateRequest,
    ArticleListItem,
    ArticlePublic,
    ArticleUpdateRequest,
    PaginatedArticles,
)
from app.schemas.envelope import success

router = APIRouter(prefix="/articles", tags=["articles"])

require_writer = require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN)


def _serialize(article: Article) -> dict:
    return ArticlePublic.model_validate(article).model_dump(mode="json")


def _slugify(title: str) -> str:
    # "Café & Circuits: Week 1!" -> "cafe-circuits-week-1"
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    # Leave room for a "-NN" suffix inside the 255-character column.
    return slug[:240].rstrip("-") or "article"


async def _slug_taken(db: AsyncSession, slug: str, exclude_id: str | None = None) -> bool:
    stmt = select(Article.id).where(Article.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(Article.id != exclude_id)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """base, or base-2, base-3, ... -- whichever is free first."""
    candidate, n = base, 1
    while await _slug_taken(db, candidate):
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def _can_edit(article: Article, user: User) -> bool:
    return article.author_id == user.id or user.role == UserRole.ADMIN


def _can_view(article: Article, user: User) -> bool:
    return article.status == ArticleStatus.PUBLISHED or _can_edit(article, user)


async def _get_article_or_404(db: AsyncSession, id_or_slug: str) -> Article:
    """Look an article up by id or by slug. Deleted articles are never served.

    A slug could in principle equal another article's id (a UUID is a valid
    slug), so when both match, the id wins.
    """
    result = await db.execute(
        select(Article).where(
            or_(Article.id == id_or_slug, Article.slug == id_or_slug),
            Article.deleted_at.is_(None),
        )
    )
    matches = result.scalars().all()
    for article in matches:
        if article.id == id_or_slug:
            return article
    if matches:
        return matches[0]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")


def _mark_published(article: Article) -> None:
    if article.status == ArticleStatus.PUBLISHED and article.published_at is None:
        article.published_at = datetime.now(timezone.utc)


@router.get("")
@router.get("/", include_in_schema=False)
async def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    mine: bool = Query(default=False, description="Only articles the caller wrote, drafts included."),
    status_filter: ArticleStatus | None = Query(
        default=None,
        alias="status",
        description="Admins: any status. Others: DRAFT is only meaningful with mine=true.",
    ),
    search: str | None = Query(default=None, max_length=100, description="Match in the title."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Article).where(Article.deleted_at.is_(None))

    if mine:
        stmt = stmt.where(Article.author_id == current_user.id)
    elif current_user.role != UserRole.ADMIN:
        # Members browsing the feed see published work only -- never someone
        # else's drafts, whatever status they ask for.
        stmt = stmt.where(Article.status == ArticleStatus.PUBLISHED)

    if status_filter is not None:
        stmt = stmt.where(Article.status == status_filter)
    if search:
        stmt = stmt.where(Article.title.ilike(f"%{search}%"))

    # Newest first. Drafts have no published_at, so they fall back to created_at.
    stmt = stmt.order_by(Article.published_at.desc().nulls_last(), Article.created_at.desc())

    articles, total = await paginate(db, stmt, page, page_size)
    effective_page_size = min(page_size, MAX_PAGE_SIZE)
    data = PaginatedArticles(
        items=[ArticleListItem.model_validate(a) for a in articles],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


@router.get("/{id_or_slug}")
async def get_article(
    id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await _get_article_or_404(db, id_or_slug)
    # A draft someone else wrote is a 404, not a 403: its existence is not
    # anyone else's business until it is published.
    if not _can_view(article, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return success(data=_serialize(article))


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_article(
    payload: ArticleCreateRequest,
    current_user: User = Depends(require_writer),
    db: AsyncSession = Depends(get_db),
):
    if payload.slug is not None:
        if await _slug_taken(db, payload.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Slug '{payload.slug}' is already in use"
            )
        slug = payload.slug
    else:
        slug = await _unique_slug(db, _slugify(payload.title))

    article = Article(
        title=payload.title,
        slug=slug,
        summary=payload.summary,
        content=payload.content,
        cover_image_url=payload.cover_image_url,
        status=payload.status,
        # Never taken from the body.
        author_id=current_user.id,
    )
    _mark_published(article)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return success(data=_serialize(article), message="Article created")


@router.put("/{id_or_slug}")
async def update_article(
    id_or_slug: str,
    payload: ArticleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await _get_article_or_404(db, id_or_slug)
    if not _can_view(article, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    if not _can_edit(article, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this article",
        )

    fields = payload.model_dump(exclude_unset=True)
    # title and content are required columns; an explicit null would be a 500.
    for required in ("title", "content", "status", "slug"):
        if required in fields and fields[required] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{required} cannot be null")

    new_slug = fields.get("slug")
    if new_slug is not None and new_slug != article.slug:
        if await _slug_taken(db, new_slug, exclude_id=article.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Slug '{new_slug}' is already in use"
            )

    for field, value in fields.items():
        setattr(article, field, value)
    _mark_published(article)

    await db.commit()
    await db.refresh(article)
    return success(data=_serialize(article), message="Article updated")


@router.delete("/{id_or_slug}")
async def delete_article(
    id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = await _get_article_or_404(db, id_or_slug)
    if not _can_view(article, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    if not _can_edit(article, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this article",
        )
    article.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return success(message="Article deleted")
