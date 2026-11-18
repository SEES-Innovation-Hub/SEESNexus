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
    # Always null on events served to students: they only ever see live events.
    # Set when an admin views a deleted event (GET /events?deleted=true, or
    # GET /events/{id}), which is how the app offers "restore".
    deleted_at: datetime | None = None

    # Filled by _event_response() in api/v1/events.py, which is the only place
    # allowed to build this model: the counts come from the registrations, not
    # from a column, and virtual_link is withheld from callers who are not
    # entitled to it. They default rather than being required so that
    # model_validate() can still read an Event ORM instance directly.
    confirmed_count: int = 0
    # Confirmed students checked in (by an admin, or themselves with the code).
    attended_count: int = 0
    # Whether self check-in is open. The code itself is admins-only.
    checkin_open: bool = False
    checkin_code: str | None = None
    # None means unlimited, matching max_participants (Tech Doc §4.2).
    spots_left: int | None = None


class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    student_id: str
    status: RegistrationStatus
    registered_at: datetime
    attended_at: datetime | None = None


class CheckInRequest(BaseModel):
    code: str = Field(min_length=1, max_length=12)


class AttendanceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attended: bool


class MyRegistrationResponse(EventRegistrationResponse):
    """One row of GET /events/registrations/my: the registration plus its event."""

    # 1 = next in line. Null unless status is WAITLISTED.
    waitlist_position: int | None = None
    # The organisers deleted the event after the student registered.
    event_deleted: bool = False
    event: EventResponse


class EventParticipantResponse(EventRegistrationResponse):
    student_name: str
    student_email: str


class PaginatedEventsResponse(BaseModel):
    items: list[EventResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
