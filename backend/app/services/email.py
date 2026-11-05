"""Transactional email, via Brevo.

There is only one message today -- the registration OTP -- but the provider
setup belongs in a service rather than in the route, for the same reason as
services/loans.py: the route decides policy, this module knows the provider.

Tech Doc §3 names `sib-api-v3-sdk`. Brevo has replaced that package with
`brevo-python`, whose 5.x releases import as `brevo` (not `brevo_python`) and
ship a native async client -- so the send is awaited directly rather than being
pushed through a threadpool, and nothing blocks the event loop.
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

SUBJECT = "Your SEES Nexus verification code"

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


def _body(code: str) -> tuple[str, str]:
    minutes = settings.OTP_EXPIRE_MINUTES
    text = (
        f"Your SEES Nexus verification code is {code}.\n\n"
        f"It expires in {minutes} minutes. If you did not request it, ignore this email.\n"
    )
    html = (
        f"<p>Your SEES Nexus verification code is <strong>{code}</strong>.</p>"
        f"<p>It expires in {minutes} minutes. If you did not request it, ignore this email.</p>"
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


async def send_otp_email(to_email: str, code: str) -> bool:
    """Email a verification code.

    Returns False when Brevo is not configured: that is the local-development
    path, where /notify/send-code hands the code back in the response instead.

    Raises EmailSendError when Brevo *is* configured but the send fails, so the
    route can answer 502 rather than report a success that never happened.
    """
    if not is_configured():
        logger.warning("BREVO_API_KEY is unset -- no verification email sent to %s", to_email)
        return False

    from brevo import SendTransacEmailRequestSender, SendTransacEmailRequestToItem

    text_content, html_content = _body(code)

    try:
        await _get_client().transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(
                email=settings.BREVO_SENDER_EMAIL,
                name=settings.BREVO_SENDER_NAME,
            ),
            to=[SendTransacEmailRequestToItem(email=to_email)],
            subject=SUBJECT,
            text_content=text_content,
            html_content=html_content,
        )
    except Exception as exc:
        # Deliberately broad: an outbound HTTP call fails in many ways (Brevo
        # API errors, DNS, TLS, timeouts) and every one of them means the same
        # thing to the caller -- the code did not go out. The code itself is
        # never logged; it is the secret being delivered.
        logger.error("Could not send the verification email to %s: %s", to_email, exc)
        raise EmailSendError("Could not send the verification email") from exc

    return True
