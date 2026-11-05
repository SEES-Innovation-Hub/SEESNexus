from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Fresh in-memory SQLite DB per test — fast and fully isolated.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Ada Student",
        email="ada@unilag.edu.ng",
        password=hash_password("StrongPass1"),
        department="EEE",
        level="200 Level",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_student_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Grace Student",
        email="grace@unilag.edu.ng",
        password=hash_password("StrongPass2"),
        department="EEE",
        level="300 Level",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Admin User",
        email="admin@unilag.edu.ng",
        password=hash_password("AdminPass1"),
        department="EEE",
        level="Staff",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_token(client: AsyncClient, student_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "StrongPass1"}
    )
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def other_student_token(client: AsyncClient, other_student_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": other_student_user.email, "password": "StrongPass2"},
    )
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": "AdminPass1"}
    )
    return resp.json()["data"]["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
