from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.hardware import HardwareCategory, HardwareStatus, LoanStatus


class HardwarePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    serial_number: str
    category: HardwareCategory
    status: HardwareStatus
    image_url: str | None
    quantity: int
    available_quantity: int
    added_by_id: str


class HardwareCreateRequest(BaseModel):
    """available_quantity and added_by_id are absent on purpose.

    A new item has every unit free, so availability is derived from quantity;
    the owner comes from the access token. Accepting either from the body would
    let a caller lend out units that were never bought.
    """

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    serial_number: str = Field(min_length=1, max_length=255)
    category: HardwareCategory
    status: HardwareStatus = HardwareStatus.AVAILABLE
    image_url: str | None = Field(default=None, max_length=500)
    quantity: int = Field(ge=1)


class HardwareUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    serial_number: str | None = Field(default=None, min_length=1, max_length=255)
    category: HardwareCategory | None = None
    status: HardwareStatus | None = None
    image_url: str | None = Field(default=None, max_length=500)
    # Changing this moves available_quantity by the same delta -- see the route.
    quantity: int | None = Field(default=None, ge=1)


class PaginatedHardware(BaseModel):
    items: list[HardwarePublic]
    page: int
    page_size: int
    total: int
    total_pages: int


class LoanCreateRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=1000)
    expected_return_date: datetime | None = None


class LoanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hardware_id: str
    hardware_name: str | None = None
    borrower_id: str
    approved_by_id: str | None
    status: LoanStatus
    purpose: str
    request_date: datetime | None
    approval_date: datetime | None
    expected_return_date: datetime | None
    actual_return_date: datetime | None

    @model_validator(mode="before")
    @classmethod
    def _pull_hardware_name(cls, data: Any) -> Any:
        # Lift the related item's name onto the flat response when validating
        # from an ORM row. HardwareLoan.hardware is selectin-loaded, so the
        # attribute is present without a trailing round trip. A plain dict
        # (e.g. in tests) is passed through unchanged.
        if isinstance(data, dict):
            return data
        hardware = getattr(data, "hardware", None)
        if hardware is None:
            return data
        return {
            "id": data.id,
            "hardware_id": data.hardware_id,
            "hardware_name": hardware.name,
            "borrower_id": data.borrower_id,
            "approved_by_id": data.approved_by_id,
            "status": data.status,
            "purpose": data.purpose,
            "request_date": data.request_date,
            "approval_date": data.approval_date,
            "expected_return_date": data.expected_return_date,
            "actual_return_date": data.actual_return_date,
        }
