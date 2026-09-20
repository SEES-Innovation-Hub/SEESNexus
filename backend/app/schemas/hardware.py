from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    borrower_id: str
    approved_by_id: str | None
    status: LoanStatus
    purpose: str
    request_date: datetime | None
    approval_date: datetime | None
    expected_return_date: datetime | None
    actual_return_date: datetime | None
