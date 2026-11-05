from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_optional, require_roles
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.core.slug import unique_slug
from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.schemas.article import (
    ArticleCreateRequest,
    ArticlePublic,
    ArticleUpdateRequest,
    PaginatedArticles,
)
from app.schemas.envelope import success

router = APIRouter(prefix="/articles", tags=["articles"])

# §5.6: contributors author articles, admins may do anything.
require_author = require_roles(UserRole.CONTRIBUTOR, UserRole.ADMIN)


def _serialize(article: Article) -> dict:
    return ArticlePublic.model_validate(article).model_dump(mode="json")


def _may_edit(article: Article, user: User) -> bool:
    return article.author_id == user.id or user.role == UserRole.ADMIN


def _may_read_unpublished(article: Article, viewer: User | None) -> bool:
    return viewer is not None and _may_edit(article, viewer)


async def _get_article_or_404(db: AsyncSession, slug: str) -> Article:
    result = await db.execute(
        select(Article).where(Article.slug == slug, Article.deleted_at.is_(None))
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.get("")
@router.get("/", include_in_schema=False)
async def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    tag: str | None = Query(default=None, description="Return only articles carrying this tag."),
    author_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Public: published articles only, per §5.6 ("List published articles").

    Drafts and archived pieces are reachable only through GET /{slug}, and only
    by their author or an admin.
    """
    stmt = select(Article).where(
        Article.deleted_at.is_(None), Article.status == ArticleStatus.PUBLISHED
    )
    if author_id is not None:
        stmt = stmt.where(Article.author_id == author_id)
    # Newest first: published_at is fixed at first publication, so later edits
    # do not shuffle the list.
    stmt = stmt.order_by(Article.published_at.desc(), Article.created_at.desc())

    articles, total = await paginate(db, stmt, page, page_size)

    if tag is not None:
        # tags is a JSON column, and JSON containment is not portable across
        # SQLite and Postgres, so the filter is applied after the query. It
        # therefore narrows the current page rather than the whole set; a real
        # tag index belongs in a follow-up if tag browsing becomes a main route.
        articles = [article for article in articles if tag in (article.tags or [])]

    effective_page_size = min(page_size, MAX_PAGE_SIZE)
    data = PaginatedArticles(
        items=[ArticlePublic.model_validate(article) for article in articles],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_article(
    payload: ArticleCreateRequest,
    author: User = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    published_at = (
        datetime.now(timezone.utc) if payload.status == ArticleStatus.PUBLISHED else None
    )
    article = Article(
        title=payload.title,
        slug=await unique_slug(db, payload.title),
        content=payload.content,
        excerpt=payload.excerpt,
        cover_image_url=payload.cover_image_url,
        status=payload.status,
        tags=payload.tags,
        # Never taken from the body.
        author_id=author.id,
        published_at=published_at,
    )
    db.add(article)
    try:
        await db.commit()
    except IntegrityError as exc:
        # unique_slug checks before inserting, so this is the narrow race of two
        # simultaneous creates with the same title. Better a 409 the author can
        # retry than a silently mangled slug.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An article with this title was just created; try again",
        ) from exc
    await db.refresh(article)
    return success(data=_serialize(article), message="Article created")


@router.get("/{slug}")
async def get_article(
    slug: str,
    viewer: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    article = await _get_article_or_404(db, slug)
    if article.status != ArticleStatus.PUBLISHED and not _may_read_unpublished(article, viewer):
        # 404, not 403: a stranger should not learn that a draft exists at this
        # slug, since the slug is derived from the title.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return success(data=_serialize(article))


@router.put("/{slug}")
async def update_article(
    slug: str,
    payload: ArticleUpdateRequest,
    current_user: User = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    article = await _get_article_or_404(db, slug)
    if not _may_edit(article, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this article",
        )

    updates = payload.model_dump(exclude_unset=True)

    # Resolved before anything is assigned: unique_slug runs a query, and a
    # query after an assignment autoflushes the pending values.
    new_slug = None
    if "title" in updates and updates["title"] != article.title:
        new_slug = await unique_slug(db, updates["title"], exclude_id=article.id)

    for field, value in updates.items():
        setattr(article, field, value)
    if new_slug is not None:
        article.slug = new_slug

    # Stamped once, at first publication, and never moved again -- an edit years
    # later must not jump the article back to the top of the list.
    if article.status == ArticleStatus.PUBLISHED and article.published_at is None:
        article.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(article)
    return success(data=_serialize(article), message="Article updated")


@router.delete("/{slug}")
async def delete_article(
    slug: str,
    current_user: User = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete. §4.3 forbids removing a user's articles outright."""
    article = await _get_article_or_404(db, slug)
    if not _may_edit(article, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this article",
        )
    article.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return success(message="Article deleted")
