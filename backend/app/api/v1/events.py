from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.models.events import Event, EventRegistration, EventType, RegistrationStatus
from app.models.user import User
from app.schemas.envelope import success
from app.schemas.events import (
    EventCreate,
    EventParticipantResponse,
    EventRegistrationResponse,
    EventResponse,
    EventUpdate,
    PaginatedEventsResponse,
    RegisterStudentRequest,
)

router = APIRouter(prefix="/events", tags=["events"])


def _serialize_event(event: Event) -> dict:
    return EventResponse.model_validate(event).model_dump(mode="json")


async def _get_event_or_404(db: AsyncSession, event_id: str, *, include_deleted: bool = False) -> Event:
    stmt = select(Event).where(Event.id == event_id)
    if not include_deleted:
        stmt = stmt.where(Event.deleted_at.is_(None))
    event = (await db.execute(stmt)).scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def _validate_event_dates(event: Event) -> None:
    if event.end_date <= event.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    if event.registration_deadline > event.start_date:
        raise HTTPException(
            status_code=400, detail="registration_deadline must be no later than start_date"
        )
    if not event.is_virtual and event.virtual_link is not None:
        raise HTTPException(status_code=400, detail="virtual_link is only allowed for virtual events")


@router.get("")
@router.get("/", include_in_schema=False)
async def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    event_type: EventType | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).where(Event.deleted_at.is_(None))
    if event_type is not None:
        stmt = stmt.where(Event.event_type == event_type)
    stmt = stmt.order_by(Event.start_date.asc())
    events, total = await paginate(db, stmt, page, page_size)
    effective_page_size = min(page_size, MAX_PAGE_SIZE)
    data = PaginatedEventsResponse(
        items=[EventResponse.model_validate(event) for event in events],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await _get_event_or_404(db, event_id)
    return success(data=_serialize_event(event))


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_event(
    payload: EventCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    event = Event(**payload.model_dump(), created_by_id=admin.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return success(data=_serialize_event(event), message="Event created")


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    payload: EventUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    event = (
        await db.execute(
            select(Event)
            .where(Event.id == event_id, Event.deleted_at.is_(None))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    _validate_event_dates(event)
    await db.commit()
    await db.refresh(event)
    return success(data=_serialize_event(event), message="Event updated")


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    event = await _get_event_or_404(db, event_id)
    event.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return success(message="Event deleted")


@router.post("/{event_id}/register")
async def register_for_event(
    event_id: str,
    payload: RegisterStudentRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del payload
    event = await _get_event_or_404(db, event_id)
    now = datetime.now(timezone.utc)
    deadline = event.registration_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now > deadline:
        raise HTTPException(status_code=400, detail="Registration deadline has passed")

    existing = (
        await db.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event.id,
                EventRegistration.student_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="You are already registered for this event")

    confirmed_count = (
        await db.execute(
            select(func.count())
            .select_from(EventRegistration)
            .where(
                EventRegistration.event_id == event.id,
                EventRegistration.status == RegistrationStatus.CONFIRMED,
            )
        )
    ).scalar_one()
    registration_status = (
        RegistrationStatus.WAITLISTED
        if event.max_participants is not None and confirmed_count >= event.max_participants
        else RegistrationStatus.CONFIRMED
    )
    registration = EventRegistration(
        event_id=event.id, student_id=current_user.id, status=registration_status
    )
    db.add(registration)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="You are already registered for this event") from exc
    await db.refresh(registration)
    return success(
        data=EventRegistrationResponse.model_validate(registration).model_dump(mode="json"),
        message="Registration completed",
    )


@router.get("/{event_id}/participants")
async def list_participants(
    event_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    event = await _get_event_or_404(db, event_id)
    result = await db.execute(
        select(EventRegistration, User)
        .join(User, User.id == EventRegistration.student_id)
        .where(EventRegistration.event_id == event.id)
        .order_by(EventRegistration.registered_at.asc())
    )
    data = [
        EventParticipantResponse(
            id=registration.id,
            event_id=registration.event_id,
            student_id=registration.student_id,
            status=registration.status,
            registered_at=registration.registered_at,
            student_name=user.full_name,
            student_email=user.email,
        ).model_dump(mode="json")
        for registration, user in result.all()
    ]
    return success(data=data)
