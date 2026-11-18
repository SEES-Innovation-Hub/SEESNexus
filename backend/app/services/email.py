"""Transactional email, via Brevo.

Two messages: the registration OTP, and "you are off the waitlist". The
provider setup lives here rather than in the routes, for the same reason as
services/loans.py: the route decides policy, this module knows the provider.

Tech Doc §3 names `sib-api-v3-sdk`. Brevo has replaced that package with
`brevo-python`, whose 5.x releases import as `brevo` (not `brevo_python`) and
ship a native async client -- so the send is awaited directly rather than being
pushed through a threadpool, and nothing blocks the event loop.
"""
import html
import logging
from datetime import datetime
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

SUBJECT = "Your SEES Nexus verification code"
RESET_SUBJECT = "Reset your SEES Nexus password"
PROMOTION_SUBJECT = "You have a place: {title}"

# Cached per API key: the Brevo client owns an httpx connection pool and exposes
# no close()/aclose(), so building one per email would leak sockets. Keying the
# cache on the token means a settings change (as in tests) rebuilds it rather
# than silently reusing a client bound to the old key.
_client: Any = None
_client_key: str | None = None


class EmailSendError(RuntimeError):
    """Brevo could not be reached, or refused the message."""


def is_configured() -> bool:
    """Whether this deployment can actually send email."""
    return bool(settings.BREVO_API_KEY)


def _body(code: str, reset: bool = False) -> tuple[str, str]:
    minutes = settings.OTP_EXPIRE_MINUTES
    what = "password reset code" if reset else "verification code"
    ignore = (
        "If you didn't ask to reset your password, ignore this email; your password stays the same."
        if reset
        else "If you did not request it, ignore this email."
    )
    text = f"Your SEES Nexus {what} is {code}.\n\nIt expires in {minutes} minutes. {ignore}\n"
    html = (
        f"<p>Your SEES Nexus {what} is <strong>{code}</strong>.</p>"
        f"<p>It expires in {minutes} minutes. {ignore}</p>"
    )
    return text, html


def _get_client() -> Any:
    global _client, _client_key

    # Imported lazily so the app still boots, and the test suite still runs,
    # when this optional dependency is not installed.
    from brevo import AsyncBrevo

    if _client is None or _client_key != settings.BREVO_API_KEY:
        _client = AsyncBrevo(api_key=settings.BREVO_API_KEY)
        _client_key = settings.BREVO_API_KEY
    return _client


async def _send(to_email: str, subject: str, text_content: str, html_content: str) -> None:
    """Send one message. Raises EmailSendError on any failure.

    Callers check is_configured() first; this assumes a key is set.
    """
    from brevo import SendTransacEmailRequestSender, SendTransacEmailRequestToItem

    try:
        await _get_client().transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(
                email=settings.BREVO_SENDER_EMAIL,
                name=settings.BREVO_SENDER_NAME,
            ),
            to=[SendTransacEmailRequestToItem(email=to_email)],
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )
    except Exception as exc:
        # Deliberately broad: an outbound HTTP call fails in many ways (Brevo
        # API errors, DNS, TLS, timeouts) and every one of them means the same
        # thing to the caller -- the message did not go out. The body is never
        # logged; for the OTP it is the secret being delivered.
        logger.error("Could not send %r to %s: %s", subject, to_email, exc)
        raise EmailSendError("Could not send the email") from exc


async def send_otp_email(to_email: str, code: str, *, reset: bool = False) -> bool:
    """Email a verification code.

    Returns False when Brevo is not configured: that is the local-development
    path, where /notify/send-code hands the code back in the response instead.

    Raises EmailSendError when Brevo *is* configured but the send fails, so the
    route can answer 502 rather than report a success that never happened.
    """
    if not is_configured():
        logger.warning("BREVO_API_KEY is unset -- no verification email sent to %s", to_email)
        return False

    text_content, html_content = _body(code, reset=reset)
    await _send(to_email, RESET_SUBJECT if reset else SUBJECT, text_content, html_content)
    return True


async def send_waitlist_promotion_email(
    to_email: str, full_name: str, event_title: str, start_date: datetime
) -> bool:
    """Tell a student they moved off the waitlist and now hold a place.

    Best effort, and never raises: it runs as a background task after the
    response is sent, and the promotion itself has already been committed. A
    student who misses the email still sees CONFIRMED in the app.
    """
    if not is_configured():
        logger.info("BREVO_API_KEY is unset -- no promotion email sent to %s", to_email)
        return False

    when = start_date.strftime("%A %d %B %Y, %H:%M UTC")
    text_content = (
        f"Hi {full_name},\n\n"
        f"A place opened up and you have moved off the waitlist for \"{event_title}\".\n"
        f"Your registration is now confirmed. The event starts {when}.\n\n"
        "If you can no longer go, please cancel in SEES Nexus so the next person gets the place.\n"
    )
    html_content = (
        f"<p>Hi {html.escape(full_name)},</p>"
        f"<p>A place opened up and you have moved off the waitlist for "
        f"<strong>{html.escape(event_title)}</strong>. Your registration is now confirmed. "
        f"The event starts {when}.</p>"
        "<p>If you can no longer go, please cancel in SEES Nexus so the next person gets the place.</p>"
    )
    try:
        await _send(
            to_email,
            PROMOTION_SUBJECT.format(title=event_title)[:200],
            text_content,
            html_content,
        )
    except EmailSendError:
        return False
    return True
