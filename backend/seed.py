"""
Populates sample data for frontend development, per Tech Doc §9.2.
Safe to re-run: skips seeding if a seed admin user already exists.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_models
from app.core.security import hash_password
from app.models.article import Article, ArticleStatus
from app.models.events import Event, EventType
from app.models.hardware import Hardware, HardwareCategory
from app.models.user import User, UserRole

SEED_ADMIN_EMAIL = "admin@seesnexus.dev"


async def seed() -> None:
    # Postgres is migrated by Alembic first (docker-compose does that); only the
    # zero-setup SQLite database needs its tables made here.
    if settings.is_sqlite:
        await init_models()

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL))
        if existing.scalar_one_or_none() is not None:
            print("Seed data already present — skipping.")
            return

        admin = User(
            full_name="Seed Admin",
            email=SEED_ADMIN_EMAIL,
            password=hash_password("ChangeMe123"),
            department="EEE",
            level="Staff",
            role=UserRole.ADMIN,
        )
        student = User(
            full_name="Seed Student",
            email="student@seesnexus.dev",
            password=hash_password("ChangeMe123"),
            department="EEE",
            level="200 Level",
            role=UserRole.STUDENT,
        )
        db.add_all([admin, student])
        await db.flush()

        hardware = Hardware(
            name="Digital Oscilloscope",
            description="Rigol DS1054Z",
            serial_number="SEED-OSC-001",
            category=HardwareCategory.MEASUREMENT,
            quantity=3,
            available_quantity=3,
            added_by_id=admin.id,
        )
        db.add(hardware)

        now = datetime.now(timezone.utc)
        db.add_all(
            [
                Event(
                    title="Freshers' Orientation",
                    description="Meet SEES, tour the Innovation Hub and learn how to borrow lab equipment.",
                    event_type=EventType.ORIENTATION,
                    location="SEES Innovation Hub",
                    start_date=now + timedelta(days=7),
                    end_date=now + timedelta(days=7, hours=3),
                    registration_deadline=now + timedelta(days=6),
                    max_participants=50,
                    created_by_id=admin.id,
                ),
                Event(
                    title="Embedded Systems Workshop",
                    description="Hands-on with microcontrollers: blink, sense, and talk to the cloud.",
                    event_type=EventType.WORKSHOP,
                    location="Online",
                    is_virtual=True,
                    virtual_link="https://meet.example.com/sees-embedded",
                    start_date=now + timedelta(days=14),
                    end_date=now + timedelta(days=14, hours=2),
                    registration_deadline=now + timedelta(days=13),
                    max_participants=2,
                    created_by_id=admin.id,
                ),
                Article(
                    title="Welcome to SEES Nexus",
                    slug="welcome-to-sees-nexus",
                    summary="Projects, hardware and events, all in one place.",
                    content=(
                        "## What's here\n\n"
                        "- **Projects**: show what you're building\n"
                        "- **Hardware**: borrow lab equipment\n"
                        "- **Events**: register for workshops and hackathons\n\n"
                        "New semester, new heights."
                    ),
                    status=ArticleStatus.PUBLISHED,
                    published_at=now,
                    author_id=admin.id,
                ),
            ]
        )

        await db.commit()
        print(f"Seeded: admin={SEED_ADMIN_EMAIL} / ChangeMe123 (dev only — rotate before any shared use)")


if __name__ == "__main__":
    asyncio.run(seed())
