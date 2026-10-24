from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserSearchResult
from app.schemas.envelope import success

router = APIRouter(prefix="/users", tags=["users"])

# Narrow, by design: the picker shows at most ten rows and the server never
# needs to decide which eleven matches "would have been best". A cap also
# bounds the result size regardless of what the client sends.
SEARCH_RESULT_LIMIT = 10


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1, max_length=100),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Case-insensitive substring match on full_name for the teammate picker."""
    needle = q.strip()
    if not needle:
        # min_length=1 only guards the raw value; whitespace-only still gets
        # here and would otherwise return every active user.
        return success(data=[])

    result = await db.execute(
        select(User)
        .where(User.is_active.is_(True), User.full_name.ilike(f"%{needle}%"))
        .order_by(User.full_name.asc())
        .limit(SEARCH_RESULT_LIMIT)
    )
    users = result.scalars().all()
    data = [UserSearchResult.model_validate(u).model_dump(mode="json") for u in users]
    return success(data=data)
