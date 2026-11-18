"""The admin key: the only way anyone becomes an ADMIN.

Used at sign-up (POST /auth/register with admin_key) and when an existing admin
promotes someone (PUT /admin/users/{id}/role with role ADMIN). The key is the
ADMIN_REGISTRATION_KEY setting, shared privately by the project owners.
"""
import logging
import secrets

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def assert_admin_key(candidate: str | None) -> None:
    """403 unless candidate is this deployment's admin key.

    Constant-time comparison, so response timing says nothing about how much of
    a guess was right. Failures are logged (never the key itself) so repeated
    attempts show up in the logs.
    """
    expected = settings.ADMIN_REGISTRATION_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts can't be created: no admin key is configured on this server",
        )
    if not candidate or not secrets.compare_digest(candidate.strip().encode(), expected.encode()):
        logger.warning("Rejected an admin key")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")
