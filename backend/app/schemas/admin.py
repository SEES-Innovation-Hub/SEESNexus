from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.hardware import LoanStatus
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


class LoanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hardware_id: str
    borrower_id: str
    approved_by_id: str | None
    status: LoanStatus
    purpose: str
    request_date: datetime | None
    approval_date: datetime | None
    expected_return_date: datetime | None
    actual_return_date: datetime | None
