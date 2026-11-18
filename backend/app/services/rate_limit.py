"""Database-backed rate limits.

Each limited action records a row in rate_limit_events; a request is refused
with 429 when its key already has `limit` rows inside `window`. Postgres holds
the counts, so limits survive restarts and are shared by every API instance
without running Redis. The check-then-insert can let a burst overshoot by a
request or two under heavy concurrency, which is fine for abuse limits.
"""
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.rate_limit import RateLimitEvent

# Rows older than this are never needed again (no window is longer).
RETENTION = timedelta(days=1)
# Pruning on a small share of requests keeps the table small without a cron job.
PRUNE_PROBABILITY = 0.02


@dataclass(frozen=True)
class Limit:
    name: str
    limit: int
    window: timedelta


# Generous for a person, tight for a script. Changing a number here is all it takes.
LOGIN_PER_IP = Limit("login:ip", 30, timedelta(minutes=15))
LOGIN_PER_EMAIL = Limit("login:email", 10, timedelta(minutes=15))
SEND_CODE_PER_IP = Limit("send-code:ip", 10, timedelta(hours=1))
SEND_CODE_PER_EMAIL = Limit("send-code:email", 3, timedelta(minutes=15))
VERIFY_CODE_PER_IP = Limit("verify-code:ip", 30, timedelta(minutes=15))
ADMIN_KEY_PER_IP = Limit("admin-key:ip", 10, timedelta(minutes=15))


def client_ip(request: Request) -> str:
    """The caller's IP address.

    Behind TRUSTED_PROXY_COUNT proxies, the address is the entry that many
    places from the right of X-Forwarded-For: each trusted proxy appends the
    address it received the request from, and anything further left was
    written by the client and can be forged.
    """
    hops = settings.TRUSTED_PROXY_COUNT
    if hops > 0:
        header = request.headers.get("x-forwarded-for", "")
        forwarded = [part.strip() for part in header.split(",") if part.strip()]
        if len(forwarded) >= hops:
            return forwarded[-hops]
    return request.client.host if request.client else "unknown"


async def hit(db: AsyncSession, limit: Limit, subject: str) -> None:
    """Count one request against `limit` for `subject`, or raise 429.

    Commits, so the count sticks even if the request fails afterwards (a wrong
    password must still count as an attempt).
    """
    key = f"{limit.name}:{subject.lower()}"
    now = datetime.now(timezone.utc)
    since = now - limit.window

    count = (
        await db.execute(
            select(func.count()).select_from(RateLimitEvent).where(
                RateLimitEvent.key == key, RateLimitEvent.created_at > since
            )
        )
    ).scalar_one()

    if count >= limit.limit:
        oldest = (
            await db.execute(
                select(func.min(RateLimitEvent.created_at)).where(
                    RateLimitEvent.key == key, RateLimitEvent.created_at > since
                )
            )
        ).scalar_one()
        if oldest is not None and oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)  # SQLite drops tzinfo
        retry_after = max(1, math.ceil(((oldest or now) + limit.window - now).total_seconds()))
        minutes = math.ceil(retry_after / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(retry_after)},
        )

    db.add(RateLimitEvent(key=key, created_at=now))
    if random.random() < PRUNE_PROBABILITY:
        await db.execute(delete(RateLimitEvent).where(RateLimitEvent.created_at < now - RETENTION))
    await db.commit()


async def clear(db: AsyncSession, limit: Limit, subject: str) -> None:
    """Forget the count for `subject`, e.g. after a successful login."""
    await db.execute(delete(RateLimitEvent).where(RateLimitEvent.key == f"{limit.name}:{subject.lower()}"))
    await db.commit()
