from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import SendCodeRequest, VerifyCodeRequest
from app.schemas.envelope import success
from app.services import otp

router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/send-code")
async def send_code(payload: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    code = await otp.issue_code(db, payload.email)

    # TODO(production): send via Brevo (BREVO_API_KEY / BREVO_SENDER_EMAIL, §9.1)
    # instead of returning the code directly.
    data = {"email": payload.email}
    if settings.OTP_DEBUG_RETURN_CODE:
        data["debug_code"] = code

    return success(data=data, message="Verification code sent")


@router.post("/verify-code")
async def verify_code(payload: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    is_valid = await otp.verify_code(db, payload.email, payload.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code"
        )
    return success(message="Code verified")
