from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional, require_admin
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.models.events import Event, EventRegistration, EventType, RegistrationStatus
from app.models.user import User, UserRole
from app.schemas.envelope import success
from app.schemas.events import (
    EventCreate,
    EventParticipantResponse,
    EventRegistrationResponse,
    EventResponse,
    EventUpdate,
    MyRegistrationResponse,
    PaginatedEventsResponse,
    RegisterStudentRequest,
)

router = APIRouter(prefix="/events", tags=["events"])


def _may_see_virtual_link(event: Event, viewer: User | None) -> bool:
    """Who gets the meeting link.

    Tech Doc §5.5 makes the event list and detail readable by anyone, and §4.2
    says nothing about who may see virtual_link -- so the routes stay public and
    the link is withheld instead. Publishing it with the event would hand a
    joinable meeting URL to every anonymous visitor the moment an admin created
    the event.

    Admins see it because they run the event. A waitlisted student does not:
    they have no place yet, and that is the whole distinction waitlisting draws.
    """
    if viewer is None:
        return False
    if viewer.role == UserRole.ADMIN:
        return True
    return any(
        registration.student_id == viewer.id
        and registration.status == RegistrationStatus.CONFIRMED
        for registration in event.registrations
    )


def _event_response(event: Event, viewer: User | None) -> EventResponse:
    """Build the response for one event, as seen by `viewer`.

    Event.registrations is lazy="selectin", so the rows are already loaded by the
    time we get here -- counting them in Python costs no extra query, on the list
    route as much as on detail.
    """
    confirmed = sum(
        1 for r in event.registrations if r.status == RegistrationStatus.CONFIRMED
    )
    response = EventResponse.model_validate(event)
    return response.model_copy(
        update={
            "confirmed_count": confirmed,
            "spots_left": (
                None
                if event.max_participants is None
                else max(event.max_participants - confirmed, 0)
            ),
            "virtual_link": (
                event.virtual_link if _may_see_virtual_link(event, viewer) else None
            ),
        }
    )


def _serialize_event(event: Event, viewer: User | None) -> dict:
    return _event_response(event, viewer).model_dump(mode="json")


async def _confirmed_count(db: AsyncSession, event_id: str) -> int:
    """How many students hold a place. Reads committed state, not loaded rows."""
    result = await db.execute(
        select(func.count())
        .select_from(EventRegistration)
        .where(
            EventRegistration.event_id == event_id,
            EventRegistration.status == RegistrationStatus.CONFIRMED,
        )
    )
    return result.scalar_one()


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
    upcoming: bool = Query(
        default=False, description="Only events that have not started yet."
    ),
    include_deleted: bool = Query(
        default=False, description="Admins only: also return soft-deleted events."
    ),
    viewer: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if include_deleted:
        # Refused rather than silently ignored: a caller asking for deleted
        # events should be told they cannot have them, not handed a filtered
        # list they will mistake for the full one.
        #
        # 401 for no credentials and 403 for the wrong role, matching what
        # get_current_user and require_roles do everywhere else.
        if viewer is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        if viewer.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an admin may list deleted events",
            )

    stmt = select(Event)
    if not include_deleted:
        stmt = stmt.where(Event.deleted_at.is_(None))
    if event_type is not None:
        stmt = stmt.where(Event.event_type == event_type)
    if upcoming:
        stmt = stmt.where(Event.start_date >= datetime.now(timezone.utc))
    # Soonest first, which is the order the filter is usually asked for.
    stmt = stmt.order_by(Event.start_date.asc())
    events, total = await paginate(db, stmt, page, page_size)
    effective_page_size = min(page_size, MAX_PAGE_SIZE)
    data = PaginatedEventsResponse(
        items=[_event_response(event, viewer) for event in events],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


# Declared above /{event_id}: FastAPI matches in declaration order, so after it
# this path would be swallowed as an event id of "registrations". Same reason
# /hardware/loans/my sits above /hardware/{hardware_id}.
@router.get("/registrations/my")
async def list_my_registrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Every registration the caller holds, whatever its status.

    Deliberately ignores the registration deadline and the event start date: a
    student needs to see what they signed up for most of all once sign-ups have
    closed. Cancelled registrations are included too, so the screen can show
    that a place was given up rather than silently dropping the row.
    """
    result = await db.execute(
        select(EventRegistration, Event)
        .join(Event, Event.id == EventRegistration.event_id)
        .where(
            EventRegistration.student_id == current_user.id,
            Event.deleted_at.is_(None),
        )
        .order_by(Event.start_date.asc())
    )
    data = [
        MyRegistrationResponse(
            id=registration.id,
            event_id=registration.event_id,
            student_id=registration.student_id,
            status=registration.status,
            registered_at=registration.registered_at,
            event_title=event.title,
            start_date=event.start_date,
            end_date=event.end_date,
            location=event.location,
            is_virtual=event.is_virtual,
            virtual_link=(
                event.virtual_link
                if registration.status == RegistrationStatus.CONFIRMED
                else None
            ),
        ).model_dump(mode="json")
        for registration, event in result.all()
    ]
    return success(data=data)


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    viewer: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    event = await _get_event_or_404(db, event_id)
    return success(data=_serialize_event(event, viewer))


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
    return success(data=_serialize_event(event, admin), message="Event created")


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
    updates = payload.model_dump(exclude_unset=True)

    # Checked against the payload, before anything is assigned to the event.
    # Any query issued after an assignment -- _confirmed_count below is one --
    # triggers an autoflush that writes the pending value, so a rejection has
    # to happen before the object is touched or the rejected cap reaches the
    # database anyway.
    #
    # Shrinking the cap below the number of students who already hold a place
    # would leave the event oversubscribed with no way to say who lost their
    # seat. Same guard, same reasoning as adjust_total_quantity() in
    # services/loans.py. The row is locked above, so the count cannot move
    # underneath the check.
    if updates.get("max_participants") is not None:
        confirmed = await _confirmed_count(db, event.id)
        if updates["max_participants"] < confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "max_participants cannot be lower than the number of confirmed "
                    f"registrations ({confirmed})"
                ),
            )

    for field, value in updates.items():
        setattr(event, field, value)

    try:
        _validate_event_dates(event)
    except HTTPException:
        # Same hazard as above: the fields are already assigned, so discard them
        # rather than leave a dirty instance for the next query to flush.
        await db.rollback()
        raise

    await db.commit()
    await db.refresh(event)
    return success(data=_serialize_event(event, admin), message="Event updated")


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
    if existing is not None and existing.status != RegistrationStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="You are already registered for this event")

    confirmed_count = await _confirmed_count(db, event.id)
    registration_status = (
        RegistrationStatus.WAITLISTED
        if event.max_participants is not None and confirmed_count >= event.max_participants
        else RegistrationStatus.CONFIRMED
    )

    if existing is not None:
        # A cancelled row is revived rather than replaced: uq_event_registration_student
        # allows only one row per student per event, so a student who cancelled
        # could otherwise never sign up again. registered_at is reset so that
        # anyone who joined the waitlist in the meantime keeps their place in the
        # queue ahead of the returning student.
        existing.status = registration_status
        existing.registered_at = now
        await db.commit()
        await db.refresh(existing)
        return success(
            data=EventRegistrationResponse.model_validate(existing).model_dump(mode="json"),
            message="Registration completed",
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


@router.delete("/{event_id}/register")
async def cancel_registration(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Give up a place, and hand it to the first student on the waitlist.

    The cancellation and the promotion share one transaction: if they could
    drift apart, an event would either lose a place permanently or hand the same
    place to two students.
    """
    # Lock the event so two simultaneous cancellations cannot both promote the
    # same waitlisted student. Same idiom as update_event.
    event = (
        await db.execute(
            select(Event).where(Event.id == event_id, Event.deleted_at.is_(None)).with_for_update()
        )
    ).scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    registration = (
        await db.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event.id,
                EventRegistration.student_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered for this event",
        )
    if registration.status == RegistrationStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This registration is already cancelled",
        )

    held_a_place = registration.status == RegistrationStatus.CONFIRMED
    registration.status = RegistrationStatus.CANCELLED

    promoted: EventRegistration | None = None
    if held_a_place:
        # Only a confirmed place frees a seat. A waitlisted student cancelling
        # promotes nobody, because they were not occupying anything.
        promoted = (
            await db.execute(
                select(EventRegistration)
                .where(
                    EventRegistration.event_id == event.id,
                    EventRegistration.status == RegistrationStatus.WAITLISTED,
                )
                .order_by(EventRegistration.registered_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if promoted is not None:
            promoted.status = RegistrationStatus.CONFIRMED

    await db.commit()
    await db.refresh(registration)

    return success(
        data={
            "registration": EventRegistrationResponse.model_validate(registration).model_dump(
                mode="json"
            ),
            "promoted_student_id": promoted.student_id if promoted is not None else None,
        },
        message="Registration cancelled",
    )


@router.post("/{event_id}/restore")
async def restore_event(
    event_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Undo a soft delete.

    Without this, deleting the wrong event is unrecoverable through the API and
    needs hand-written SQL against production. Registrations survive a delete
    (see delete_event), so a restored event comes back with its sign-ups intact.
    """
    event = await _get_event_or_404(db, event_id, include_deleted=True)
    if event.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Event is not deleted"
        )
    event.deleted_at = None
    await db.commit()
    await db.refresh(event)
    return success(data=_serialize_event(event, admin), message="Event restored")


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
