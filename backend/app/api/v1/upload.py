"""Single-image upload backed by Cloudinary.

Profile photos, project thumbnails, event banners, article covers and hardware
photos all live in Cloudinary. Clients POST a multipart file here and get a
secure URL back in the usual envelope -- they never see the Cloudinary SDK or
its credentials.
"""
import logging

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.envelope import success

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)

# 5 MiB. Large enough for a reasonable photo straight off a phone, small
# enough that a stray binary upload fails fast rather than tying up a worker.
MAX_IMAGE_BYTES = 5 * 1024 * 1024

# Everything uploaded through the app goes in one folder of the account.
CLOUDINARY_FOLDER = "sees-nexus"


def _sniff_image_type(body: bytes) -> str | None:
    """The real format, from the file's first bytes -- not the client's claim.

    Only raster formats a browser shows in an <img>. SVG is deliberately out:
    it is XML that can carry script, and a JPEG/PNG/WebP/GIF covers every
    photo or logo this app needs.
    """
    if body.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if body.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "webp"
    return None


def _configure_cloudinary() -> None:
    """Push settings into the Cloudinary SDK's module-level config.

    Called per-request because the SDK caches globally -- doing it at import
    time would read the config before pytest's monkeypatch had a chance to
    swap in test values, and would also mask a mid-run env change.
    """
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def is_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET
    )


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    if not is_configured():
        # Fail with a clear 503 rather than letting Cloudinary return an
        # opaque auth error from inside the SDK.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload is not configured",
        )

    # Read into memory with a hard cap. UploadFile streams off disk, so this
    # is bounded even for a client that lies about Content-Length.
    body = await file.read(MAX_IMAGE_BYTES + 1)
    if len(body) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(body) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MiB limit",
        )
    if _sniff_image_type(body) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JPEG, PNG, WebP or GIF image",
        )

    _configure_cloudinary()
    try:
        # The SDK is synchronous (it uses blocking HTTP). Run in a worker
        # thread, or every other request would wait for the upload to finish.
        result = await run_in_threadpool(
            cloudinary.uploader.upload,
            body,
            resource_type="image",
            folder=CLOUDINARY_FOLDER,
        )
    except Exception as exc:  # cloudinary raises its own exception types
        # The provider's message can name the cloud or the key; log it, don't return it.
        logger.error("Cloudinary upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The image couldn't be uploaded. Try again in a moment.",
        ) from exc

    url = result.get("secure_url") or result.get("url")
    if not url:
        logger.error("Cloudinary returned no URL: %r", result)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The image couldn't be uploaded. Try again in a moment.",
        )
    return success(data={"url": url}, message="Image uploaded")
