from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.events import EventType, RegistrationStatus


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    event_type: EventType
    location: str = Field(min_length=1, max_length=500)
    is_virtual: bool = False
    virtual_link: str | None = Field(default=None, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    start_date: datetime
    end_date: datetime
    registration_deadline: datetime
    max_participants: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "EventCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if self.registration_deadline > self.start_date:
            raise ValueError("registration_deadline must be no later than start_date")
        if not self.is_virtual and self.virtual_link is not None:
            raise ValueError("virtual_link is only allowed for virtual events")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    event_type: EventType | None = None
    location: str | None = Field(default=None, min_length=1, max_length=500)
    is_virtual: bool | None = None
    virtual_link: str | None = Field(default=None, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_deadline: datetime | None = None
    max_participants: int | None = Field(default=None, gt=0)


class RegisterStudentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    event_type: EventType
    location: str
    is_virtual: bool
    virtual_link: str | None
    banner_url: str | None
    start_date: datetime
    end_date: datetime
    registration_deadline: datetime
    max_participants: int | None
    created_by_id: str
    created_at: datetime


class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    student_id: str
    status: RegistrationStatus
    registered_at: datetime


class EventParticipantResponse(EventRegistrationResponse):
    student_name: str
    student_email: str


class PaginatedEventsResponse(BaseModel):
    items: list[EventResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
