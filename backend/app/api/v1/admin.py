from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.article import Article
from app.models.events import Event
from app.models.hardware import Hardware, HardwareLoan, LoanStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.admin import DashboardStats, RoleChangeRequest
from app.schemas.auth import UserPublic
from app.schemas.envelope import success
from app.schemas.hardware import LoanPublic
from app.services import loans

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


async def _count(db: AsyncSession, model, *filters) -> int:
    stmt = select(func.count()).select_from(model)
    if filters:
        stmt = stmt.where(*filters)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    stats = DashboardStats(
        total_users=await _count(db, User),
        active_users=await _count(db, User, User.is_active.is_(True)),
        students=await _count(db, User, User.role == UserRole.STUDENT),
        contributors=await _count(db, User, User.role == UserRole.CONTRIBUTOR),
        admins=await _count(db, User, User.role == UserRole.ADMIN),
        total_projects=await _count(db, Project),
        # Events are soft-deleted, so the bare row count includes events an
        # admin has already deleted and which no longer appear on any route.
        total_events=await _count(db, Event, Event.deleted_at.is_(None)),
        total_articles=await _count(db, Article, Article.deleted_at.is_(None)),
        total_hardware_items=await _count(db, Hardware),
        pending_loans=await _count(db, HardwareLoan, HardwareLoan.status == LoanStatus.PENDING),
        approved_loans=await _count(db, HardwareLoan, HardwareLoan.status == LoanStatus.APPROVED),
    )
    return success(data=stats.model_dump())


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    data = [UserPublic.model_validate(u).model_dump(mode="json") for u in users]
    return success(data=data)


@router.put("/users/{user_id}/role")
async def change_role(
    user_id: str,
    payload: RoleChangeRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Guard the lab against the last admin demoting themselves and locking the
    # whole admin surface. A different admin can still change this one's role.
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return success(data=UserPublic.model_validate(user).model_dump(mode="json"), message="Role updated")


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Same reason as change_role: self-deactivation would lock the acting admin
    # out of every endpoint on their next request (get_current_user rejects
    # inactive users).
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate yourself",
        )

    # Soft-delete only: Tech Doc §4.3 forbids cascade-deleting a user's
    # projects/articles/loans, so we deactivate rather than hard-delete.
    user.is_active = False
    await db.commit()
    return success(message="User deactivated")


@router.put("/users/{user_id}/activate")
async def activate_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return success(
        data=UserPublic.model_validate(user).model_dump(mode="json"),
        message="User reactivated",
    )


@router.get("/loans")
async def list_loans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HardwareLoan).order_by(HardwareLoan.request_date.desc()))
    loans = result.scalars().all()
    data = [LoanPublic.model_validate(loan).model_dump(mode="json") for loan in loans]
    return success(data=data)


@router.put("/loans/{loan_id}/approve")
async def approve_loan(
    loan_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    # State checks and the available_quantity arithmetic live in the service, per
    # Tech Doc §4.3 -- the /hardware return route shares the same code.
    loan = await _get_loan_or_404(db, loan_id)
    loan = await loans.approve_loan(db, loan, admin)
    return success(data=LoanPublic.model_validate(loan).model_dump(mode="json"), message="Loan approved")


@router.put("/loans/{loan_id}/reject")
async def reject_loan(loan_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    loan = await _get_loan_or_404(db, loan_id)
    loan = await loans.reject_loan(db, loan, admin)
    return success(data=LoanPublic.model_validate(loan).model_dump(mode="json"), message="Loan rejected")


@router.put("/loans/{loan_id}/return")
async def return_loan(loan_id: str, db: AsyncSession = Depends(get_db)):
    # Admin confirms the physical return. The service enforces that only an
    # APPROVED loan can be returned and bumps the availability counter back up
    # under a row lock, so no additional guard is needed here.
    loan = await _get_loan_or_404(db, loan_id)
    loan = await loans.return_loan(db, loan)
    return success(data=LoanPublic.model_validate(loan).model_dump(mode="json"), message="Loan returned")


async def _get_loan_or_404(db: AsyncSession, loan_id: str) -> HardwareLoan:
    result = await db.execute(select(HardwareLoan).where(HardwareLoan.id == loan_id))
    loan = result.scalar_one_or_none()
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan
