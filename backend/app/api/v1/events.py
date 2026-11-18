from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
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


def _may_see_virtual_link(event: Event, viewer: User) -> bool:
    """Who gets the meeting link.

    Every event route now requires a login, but being a member is not enough to
    join the meeting: the link goes to admins, who run the event, and to students
    holding a CONFIRMED place. A waitlisted student does not see it -- they have
    no place yet, and that is the whole distinction waitlisting draws. Nor does a
    student who cancelled.
    """
    if viewer.role == UserRole.ADMIN:
        return True
    return any(
        registration.student_id == viewer.id
        and registration.status == RegistrationStatus.CONFIRMED
        for registration in event.registrations
    )


def _event_response(event: Event, viewer: User) -> EventResponse:
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


def _serialize_event(event: Event, viewer: User) -> dict:
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


async def _promote_waitlisted(db: AsyncSession, event: Event) -> list[EventRegistration]:
    """Move waitlisted students into any free places, first come first served.

    Called whenever a place may have opened up: a confirmed student cancels, or
    an admin raises (or removes) max_participants. The caller must hold the event
    row lock and commits afterwards.

    "First come" is registered_at. A student who cancels and registers again gets
    a fresh registered_at, so they rejoin the back of the queue rather than
    keeping their old position.
    """
    waitlisted_stmt = (
        select(EventRegistration)
        .where(
            EventRegistration.event_id == event.id,
            EventRegistration.status == RegistrationStatus.WAITLISTED,
        )
        .order_by(EventRegistration.registered_at.asc(), EventRegistration.id.asc())
    )
    if event.max_participants is not None:
        free = event.max_participants - await _confirmed_count(db, event.id)
        if free <= 0:
            return []
        waitlisted_stmt = waitlisted_stmt.limit(free)

    promoted = list((await db.execute(waitlisted_stmt)).scalars().all())
    for registration in promoted:
        registration.status = RegistrationStatus.CONFIRMED
    return promoted


def _as_utc(value: datetime) -> datetime:
    # SQLite drops tzinfo on round-trip even for timezone-aware columns.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


async def _get_event_or_404(
    db: AsyncSession,
    event_id: str,
    *,
    include_deleted: bool = False,
    for_update: bool = False,
) -> Event:
    """Fetch an event, 404 if it is missing or (by default) soft-deleted.

    for_update takes a row lock for the rest of the transaction. Every route that
    moves a student between CONFIRMED and WAITLISTED takes it, so two of them
    cannot both read "one place left" and both fill it. SQLite ignores FOR
    UPDATE; Postgres, where it matters, honours it.
    """
    stmt = select(Event).where(Event.id == event_id)
    if not include_deleted:
        stmt = stmt.where(Event.deleted_at.is_(None))
    if for_update:
        stmt = stmt.with_for_update()
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
    deleted: bool = Query(
        default=False,
        description="Admins only: list soft-deleted events instead, so they can be restored.",
    ),
    viewer: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Members only. The list carries no meeting links unless the viewer is entitled."""
    if deleted and viewer.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list deleted events",
        )
    stmt = select(Event).where(
        Event.deleted_at.is_not(None) if deleted else Event.deleted_at.is_(None)
    )
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


# Declared above GET /{event_id} so the literal path is matched first. It is two
# segments deep, so it would not collide today, but keep it here regardless.
@router.get("/registrations/my")
async def list_my_registrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Every event the caller has registered for, in any state.

    Nothing is filtered by date or deadline: a student must be able to check
    their place after registration closes, and see past events they attended.
    Cancelled registrations are included so the app can offer to register again.
    Events an admin has since deleted are included too, flagged event_deleted,
    so the student learns the event is off rather than seeing it silently vanish.
    """
    result = await db.execute(
        select(EventRegistration, Event)
        .join(Event, Event.id == EventRegistration.event_id)
        .where(EventRegistration.student_id == current_user.id)
        .order_by(Event.start_date.desc())
    )
    data = []
    for registration, event in result.all():
        waitlist_position = None
        if registration.status == RegistrationStatus.WAITLISTED:
            queue = sorted(
                (r for r in event.registrations if r.status == RegistrationStatus.WAITLISTED),
                key=lambda r: (_as_utc(r.registered_at), r.id),
            )
            waitlist_position = next(
                i for i, r in enumerate(queue, start=1) if r.id == registration.id
            )
        data.append(
            MyRegistrationResponse(
                id=registration.id,
                event_id=registration.event_id,
                student_id=registration.student_id,
                status=registration.status,
                registered_at=registration.registered_at,
                waitlist_position=waitlist_position,
                event_deleted=event.deleted_at is not None,
                event=_event_response(event, current_user),
            ).model_dump(mode="json")
        )
    return success(data=data)


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    viewer: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Admins can open a deleted event (deleted_at is set on it) so they can
    # decide whether to restore it. Everyone else gets the same 404 as for an
    # event that never existed.
    event = await _get_event_or_404(
        db, event_id, include_deleted=viewer.role == UserRole.ADMIN
    )
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

    # Raising the cap, or clearing it to unlimited, opens places that the
    # waitlist should fill straight away rather than waiting for a cancellation.
    if "max_participants" in updates:
        await _promote_waitlisted(db, event)

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


@router.post("/{event_id}/restore")
async def restore_event(
    event_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Undo DELETE /{event_id}.

    Deletion only ever set deleted_at, so every registration is still there and
    comes back exactly as it was -- confirmed students keep their places.
    """
    event = await _get_event_or_404(db, event_id, include_deleted=True)
    if event.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is not deleted")
    event.deleted_at = None
    await db.commit()
    await db.refresh(event)
    return success(data=_serialize_event(event, admin), message="Event restored")


@router.post("/{event_id}/register")
async def register_for_event(
    event_id: str,
    payload: RegisterStudentRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del payload
    event = await _get_event_or_404(db, event_id, for_update=True)
    now = datetime.now(timezone.utc)
    if now > _as_utc(event.registration_deadline):
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
        # (event_id, student_id) is unique, so a student who cancelled re-uses
        # their row. registered_at is reset: they rejoin the back of the queue.
        registration = existing
        registration.status = registration_status
        registration.registered_at = now
    else:
        registration = EventRegistration(
            event_id=event.id,
            student_id=current_user.id,
            status=registration_status,
            # Set here rather than left to the server default: the waitlist is
            # ordered by this column, and SQLite's CURRENT_TIMESTAMP only has
            # one-second resolution, which ties students who sign up together.
            registered_at=now,
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
    """Withdraw from an event. Frees the place for the next waitlisted student.

    Allowed until the event starts -- including after the registration deadline,
    since that is exactly when a freed place is most useful to the waitlist. The
    row is kept as CANCELLED rather than deleted so the history survives and the
    admin participant list still shows who dropped out.
    """
    event = await _get_event_or_404(db, event_id, for_update=True)
    if datetime.now(timezone.utc) >= _as_utc(event.start_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This event has already started, so the registration can no longer be cancelled",
        )

    registration = (
        await db.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event.id,
                EventRegistration.student_id == current_user.id,
                EventRegistration.status != RegistrationStatus.CANCELLED,
            )
        )
    ).scalar_one_or_none()
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered for this event",
        )

    held_a_place = registration.status == RegistrationStatus.CONFIRMED
    registration.status = RegistrationStatus.CANCELLED
    # Flush before promoting, so the count of confirmed places that
    # _promote_waitlisted reads no longer includes this one.
    await db.flush()
    if held_a_place:
        await _promote_waitlisted(db, event)

    await db.commit()
    await db.refresh(registration)
    return success(
        data=EventRegistrationResponse.model_validate(registration).model_dump(mode="json"),
        message="Registration cancelled",
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
