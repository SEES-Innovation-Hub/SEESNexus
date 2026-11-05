"""The one place Hardware.available_quantity is ever written.

Tech Doc §4.3 requires the quantity arithmetic to live in a single transactional
service function rather than being spread across route handlers, so that the
counter and the loan status can never drift apart. Both the /admin routes (§5.7
approve/reject) and the /hardware routes (§5.4 request/return) call through here.

If you find yourself assigning to available_quantity anywhere else, that is the
bug this module exists to prevent.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hardware import Hardware, HardwareLoan, HardwareStatus, LoanStatus
from app.models.user import User
from app.schemas.hardware import LoanCreateRequest

# Loan states that still hold a claim on the item -- used to stop a borrower
# queueing up duplicate requests for the same piece of equipment.
ACTIVE_LOAN_STATES = (LoanStatus.PENDING, LoanStatus.APPROVED)


async def get_hardware_for_update(db: AsyncSession, hardware_id: str) -> Hardware:
    """Fetch an item with a row lock held for the rest of the transaction.

    Without the lock, two admins approving the last unit at the same moment both
    read available_quantity = 1 and both decrement, lending out a unit that does
    not exist. SQLAlchemy's SQLite dialect drops FOR UPDATE silently, so the test
    suite cannot prove this works -- CI runs Postgres, which is where it counts.
    """
    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id).with_for_update())
    hardware = result.scalar_one_or_none()
    if hardware is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware item not found")
    return hardware


def _apply_availability_delta(hardware: Hardware, delta: int) -> None:
    hardware.available_quantity += delta

    # MAINTENANCE is set by hand and means the item is off the floor entirely.
    # Units moving in or out must not quietly put it back in service.
    if hardware.status is HardwareStatus.MAINTENANCE:
        return

    hardware.status = (
        HardwareStatus.BORROWED if hardware.available_quantity == 0 else HardwareStatus.AVAILABLE
    )


def adjust_total_quantity(hardware: Hardware, new_quantity: int) -> None:
    """Change how many units the lab owns, carrying availability with it.

    If the lab owns 5 with 2 out on loan and buys 3 more, the result is 8 owned
    and 6 free -- not 8 free, which would forget the units that are out.
    """
    delta = new_quantity - hardware.quantity
    if hardware.available_quantity + delta < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="quantity cannot be lower than the number of units currently on loan",
        )

    hardware.quantity = new_quantity
    _apply_availability_delta(hardware, delta)


async def request_loan(
    db: AsyncSession, hardware: Hardware, borrower: User, payload: LoanCreateRequest
) -> HardwareLoan:
    """Create a PENDING loan. Deliberately does not touch the counter.

    Units move on approval, not on request (§4.3) -- otherwise a student could
    empty the shelf by filing requests nobody ever approves.
    """
    hardware = await get_hardware_for_update(db, hardware.id)

    if hardware.status is HardwareStatus.MAINTENANCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is under maintenance and cannot be borrowed",
        )
    if hardware.available_quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No units of this item are available"
        )

    existing = await db.execute(
        select(HardwareLoan).where(
            HardwareLoan.hardware_id == hardware.id,
            HardwareLoan.borrower_id == borrower.id,
            HardwareLoan.status.in_(ACTIVE_LOAN_STATES),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an open loan or request for this item",
        )

    loan = HardwareLoan(
        hardware_id=hardware.id,
        # Never taken from the body.
        borrower_id=borrower.id,
        status=LoanStatus.PENDING,
        purpose=payload.purpose,
        expected_return_date=payload.expected_return_date,
        # The column is nullable with no server default, and GET /admin/loans
        # orders by it -- unset, rows sort unpredictably.
        request_date=datetime.now(timezone.utc),
    )
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return loan


async def approve_loan(db: AsyncSession, loan: HardwareLoan, admin: User) -> HardwareLoan:
    loan = (
        await db.execute(
            select(HardwareLoan).where(HardwareLoan.id == loan.id).with_for_update()
        )
    ).scalar_one()
    _assert_pending(loan)

    hardware = await get_hardware_for_update(db, loan.hardware_id)
    if hardware.available_quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No units available to lend"
        )

    _apply_availability_delta(hardware, -1)
    loan.status = LoanStatus.APPROVED
    loan.approved_by_id = admin.id
    loan.approval_date = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(loan)
    return loan


async def reject_loan(db: AsyncSession, loan: HardwareLoan, admin: User) -> HardwareLoan:
    """A rejected loan never held a unit, so the counter is untouched."""
    loan = (
        await db.execute(
            select(HardwareLoan).where(HardwareLoan.id == loan.id).with_for_update()
        )
    ).scalar_one()
    _assert_pending(loan)

    loan.status = LoanStatus.REJECTED
    loan.approved_by_id = admin.id
    loan.approval_date = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(loan)
    return loan


async def cancel_loan(db: AsyncSession, loan: HardwareLoan, borrower: User) -> HardwareLoan:
    """The borrower withdraws their own pending request.

    Like reject_loan, the counter is untouched: a pending loan never held a unit,
    because units move on approval (see request_loan). Unlike reject_loan, this
    is the student's own decision, so the status is CANCELLED rather than
    REJECTED and no approver is recorded -- nobody approved or refused anything.

    Because ACTIVE_LOAN_STATES covers only PENDING and APPROVED, cancelling also
    releases the duplicate-request block, so the student can ask for the same
    item again.
    """
    loan = (
        await db.execute(
            select(HardwareLoan).where(HardwareLoan.id == loan.id).with_for_update()
        )
    ).scalar_one()

    # Ownership before state: a student poking at someone else's loan id should
    # not be able to tell a pending request from an approved one.
    if loan.borrower_id != borrower.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own loan request",
        )
    # An approved loan is returned, not cancelled -- the unit is already out.
    _assert_pending(loan)

    loan.status = LoanStatus.CANCELLED

    await db.commit()
    await db.refresh(loan)
    return loan


async def return_loan(db: AsyncSession, loan: HardwareLoan) -> HardwareLoan:
    """Give the unit back. Who may call this is the route's decision, not ours."""
    loan = (
        await db.execute(
            select(HardwareLoan).where(HardwareLoan.id == loan.id).with_for_update()
        )
    ).scalar_one()
    if loan.status is not LoanStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only an approved loan can be returned"
        )

    hardware = await get_hardware_for_update(db, loan.hardware_id)
    _apply_availability_delta(hardware, 1)

    loan.status = LoanStatus.RETURNED
    loan.actual_return_date = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(loan)
    return loan


def _assert_pending(loan: HardwareLoan) -> None:
    if loan.status is not LoanStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan is not pending")
