from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.pagination import MAX_PAGE_SIZE, paginate, total_pages
from app.models.hardware import Hardware, HardwareCategory, HardwareLoan, HardwareStatus
from app.models.user import User
from app.schemas.envelope import success
from app.schemas.hardware import (
    HardwareCreateRequest,
    HardwarePublic,
    HardwareUpdateRequest,
    LoanCreateRequest,
    LoanPublic,
    PaginatedHardware,
)
from app.services import loans

router = APIRouter(prefix="/hardware", tags=["hardware"])


def _serialize(hardware: Hardware) -> dict:
    return HardwarePublic.model_validate(hardware).model_dump(mode="json")


async def _get_hardware_or_404(db: AsyncSession, hardware_id: str) -> Hardware:
    """Read-only lookup. Anything that moves the counter goes through
    loans.get_hardware_for_update() instead, which takes the row lock."""
    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id))
    hardware = result.scalar_one_or_none()
    if hardware is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware item not found")
    return hardware


async def _assert_serial_available(db: AsyncSession, serial: str, exclude_id: str | None = None) -> None:
    """serial_number is unique in the schema; an unchecked duplicate reaches the
    database as an IntegrityError and escapes as an unenveloped 500."""
    stmt = select(Hardware.id).where(Hardware.serial_number == serial)
    if exclude_id is not None:
        stmt = stmt.where(Hardware.id != exclude_id)

    if (await db.execute(stmt)).scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Serial number {serial} is already registered",
        )


@router.get("")
@router.get("/", include_in_schema=False)
async def list_hardware(
    page: int = Query(default=1, ge=1),
    # No le= bound here on purpose: an oversized page_size is clamped server-side
    # by paginate() rather than rejected, matching /projects.
    page_size: int = Query(default=20, ge=1),
    category: HardwareCategory | None = None,
    status_filter: HardwareStatus | None = Query(default=None, alias="status"),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Members only: any logged-in user can browse the hardware shelf."""
    stmt = select(Hardware)
    if category is not None:
        stmt = stmt.where(Hardware.category == category)
    if status_filter is not None:
        stmt = stmt.where(Hardware.status == status_filter)
    # Hardware has no created_at column (§4.2), so the shelf is ordered by name.
    stmt = stmt.order_by(Hardware.name.asc())

    items, total = await paginate(db, stmt, page, page_size)
    effective_page_size = min(page_size, MAX_PAGE_SIZE)

    data = PaginatedHardware(
        items=[HardwarePublic.model_validate(item) for item in items],
        page=page,
        page_size=effective_page_size,
        total=total,
        total_pages=total_pages(total, effective_page_size),
    )
    return success(data=data.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_hardware(
    payload: HardwareCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _assert_serial_available(db, payload.serial_number)

    hardware = Hardware(
        name=payload.name,
        description=payload.description,
        serial_number=payload.serial_number,
        category=payload.category,
        status=payload.status,
        image_url=payload.image_url,
        quantity=payload.quantity,
        # Derived, never accepted from the body: a new item has every unit free.
        available_quantity=payload.quantity,
        # Never taken from the body.
        added_by_id=current_user.id,
    )
    db.add(hardware)
    await db.commit()
    await db.refresh(hardware)
    return success(data=_serialize(hardware), message="Hardware item created")


# --- Loan routes ---------------------------------------------------------
# These MUST stay above the /{hardware_id} routes below. FastAPI matches in
# declaration order, so moving them down makes "loans" match as a hardware id
# and every loan endpoint 404s. Do not alphabetise this file.


@router.get("/loans/my")
async def list_my_loans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Every state, not just the open ones: §5.4 calls this "my loan history", and
    # a student who returns an item should still see that they once borrowed it.
    result = await db.execute(
        select(HardwareLoan)
        .where(HardwareLoan.borrower_id == current_user.id)
        .order_by(HardwareLoan.request_date.desc())
    )
    my_loans = result.scalars().all()
    data = [LoanPublic.model_validate(loan).model_dump(mode="json") for loan in my_loans]
    return success(data=data)


@router.post("/loans/{loan_id}/cancel")
async def cancel_loan_request(
    loan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw your own pending request.

    Admins reject (PUT /admin/loans/{id}/reject); borrowers cancel. Until this
    existed, a student's own request blocked them from re-requesting the item
    until an admin acted on it, because ACTIVE_LOAN_STATES includes PENDING.
    """
    result = await db.execute(select(HardwareLoan).where(HardwareLoan.id == loan_id))
    loan = result.scalar_one_or_none()
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    # Ownership and state checks live in the service, per §4.3.
    loan = await loans.cancel_loan(db, loan, current_user)
    return success(
        data=LoanPublic.model_validate(loan).model_dump(mode="json"),
        message="Loan request cancelled",
    )


@router.get("/{hardware_id}")
async def get_hardware(
    hardware_id: str,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hardware = await _get_hardware_or_404(db, hardware_id)
    return success(data=_serialize(hardware))


@router.put("/{hardware_id}")
async def update_hardware(
    hardware_id: str,
    payload: HardwareUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    hardware = await loans.get_hardware_for_update(db, hardware_id)

    fields = payload.model_dump(exclude_unset=True)
    new_quantity = fields.pop("quantity", None)
    # Pulled out so it is applied last: an admin naming a status explicitly
    # outranks the one derived from the new stock level.
    explicit_status = fields.pop("status", None)

    serial = fields.get("serial_number")
    if serial is not None and serial != hardware.serial_number:
        await _assert_serial_available(db, serial, exclude_id=hardware.id)

    for field, value in fields.items():
        setattr(hardware, field, value)

    if new_quantity is not None:
        loans.adjust_total_quantity(hardware, new_quantity)
    if explicit_status is not None:
        hardware.status = explicit_status

    await db.commit()
    await db.refresh(hardware)
    return success(data=_serialize(hardware), message="Hardware item updated")


@router.delete("/{hardware_id}")
async def retire_hardware(
    hardware_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: the row is never removed.

    HardwareLoan.hardware_id is a non-nullable FK, so a hard delete either fails
    at the database or destroys loan history -- and §4.3 asks for institutional
    history to survive across cohorts. MAINTENANCE takes the item off the floor,
    and loans.request_loan() already refuses to lend a MAINTENANCE item, so it
    cannot be borrowed again. Same call this codebase already made for users,
    where DELETE /admin/users/{id} flips is_active instead of deleting.
    """
    hardware = await _get_hardware_or_404(db, hardware_id)
    hardware.status = HardwareStatus.MAINTENANCE
    await db.commit()
    await db.refresh(hardware)
    return success(data=_serialize(hardware), message="Hardware item retired")


@router.post("/{hardware_id}/loan", status_code=status.HTTP_201_CREATED)
async def request_hardware_loan(
    hardware_id: str,
    payload: LoanCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hardware = await _get_hardware_or_404(db, hardware_id)
    loan = await loans.request_loan(db, hardware, current_user, payload)
    return success(data=LoanPublic.model_validate(loan).model_dump(mode="json"), message="Loan requested")
