"""
Populates sample data for frontend development, per Tech Doc §9.2.
Safe to re-run: skips seeding if a seed admin user already exists.
"""
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_models
from app.core.security import hash_password
from app.models.hardware import Hardware, HardwareCategory
from app.models.user import User, UserRole

SEED_ADMIN_EMAIL = "admin@seesnexus.dev"


async def seed() -> None:
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

        await db.commit()
        print(f"Seeded: admin={SEED_ADMIN_EMAIL} / ChangeMe123 (dev only — rotate before any shared use)")


if __name__ == "__main__":
    asyncio.run(seed())
