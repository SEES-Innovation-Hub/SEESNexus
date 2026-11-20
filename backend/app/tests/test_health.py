import pytest
from httpx import AsyncClient

import app.main as main

pytestmark = pytest.mark.asyncio


async def test_health_is_ok_when_the_database_answers(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


async def test_health_is_503_when_the_database_is_down(client: AsyncClient, monkeypatch):
    class DeadEngine:
        def connect(self):
            raise ConnectionRefusedError("database is down")

    monkeypatch.setattr(main, "engine", DeadEngine())
    resp = await client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "error", "message": "Database unavailable", "data": None}


async def test_database_ssl_is_added_to_the_url():
    from app.core.config import Settings

    s = Settings(DATABASE_URL="postgres://u:p@h/db", DATABASE_SSL="require", SECRET_KEY="a-real-secret-123")
    assert s.DATABASE_URL == "postgresql+asyncpg://u:p@h/db?ssl=require"
    # Never applied to SQLite.
    assert "ssl" not in Settings(DATABASE_URL="sqlite+aiosqlite:///x.db", DATABASE_SSL="require").DATABASE_URL
