from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

MAX_PAGE_SIZE = 100


async def paginate(db: AsyncSession, stmt: Select, page: int, page_size: int) -> tuple[list, int]:
    """Run a SELECT as one page of results. Returns (items, total).

    page_size is clamped here rather than in the schema alone: list endpoints are
    public, so the cap has to hold server-side regardless of the query string.
    """
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    # Count off the filtered statement, not the bare table, so filters apply.
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


def total_pages(total: int, page_size: int) -> int:
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    return (total + page_size - 1) // page_size
