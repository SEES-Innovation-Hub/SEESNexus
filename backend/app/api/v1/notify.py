from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import SendCodeRequest, VerifyCodeRequest
from app.schemas.envelope import success
from app.services import email, otp, rate_limit

router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/send-code")
async def send_code(payload: SendCodeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Every call sends a real email: limit per sender (a script spraying
    # addresses) and per recipient (someone flooding one inbox).
    await rate_limit.hit(db, rate_limit.SEND_CODE_PER_IP, rate_limit.client_ip(request))
    await rate_limit.hit(db, rate_limit.SEND_CODE_PER_EMAIL, payload.email)

    code = await otp.issue_code(db, payload.email)

    try:
        sent = await email.send_otp_email(payload.email, code)
    except email.EmailSendError as exc:
        # The code row is already committed, so a retry costs nothing and
        # reuses none of this one's state.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the verification code. Please try again.",
        ) from exc

    data = {"email": payload.email}

    # Handing the code back is a local-development affordance only, and it is
    # gated on Brevo being absent rather than on the flag alone. Returning it
    # from an environment that can send email would defeat the entire check:
    # the caller would be told the secret they are being tested on, so anyone
    # could verify an address they do not own.
    if settings.OTP_DEBUG_RETURN_CODE and not email.is_configured():
        data["debug_code"] = code

    message = (
        "Verification code sent"
        if sent
        else "Verification code generated, but email is not configured"
    )
    return success(data=data, message=message)


@router.post("/verify-code")
async def verify_code(payload: VerifyCodeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Per-code attempts are capped in otp.check_code; this caps one client
    # cycling through many addresses.
    await rate_limit.hit(db, rate_limit.VERIFY_CODE_PER_IP, rate_limit.client_ip(request))
    result = await otp.check_code(db, payload.email, payload.code)
    if result is not otp.CodeCheck.OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=otp.CHECK_MESSAGES[result])
    return success(message="Code verified")
