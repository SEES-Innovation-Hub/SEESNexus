from pydantic import BaseModel, Field

from app.models.user import UserRole


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    students: int
    contributors: int
    admins: int
    total_projects: int
    total_events: int
    total_articles: int
    total_hardware_items: int
    pending_loans: int
    approved_loans: int


class RoleChangeRequest(BaseModel):
    role: UserRole
    # Required when the new role is ADMIN: nobody becomes an admin without the
    # admin key, not even when another admin promotes them.
    admin_key: str | None = Field(default=None, max_length=256)


# LoanPublic moved to app/schemas/hardware.py -- a loan is a hardware entity and
# both the /admin and /hardware routes serialize it.
