"""Single-image upload backed by Cloudinary.

The lab's profile pictures, project thumbnails, and hardware photos all live in
Cloudinary. Clients POST a multipart file here and get a secure URL back in
the usual envelope -- they never see the Cloudinary SDK.
"""
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.envelope import success

router = APIRouter(prefix="/upload", tags=["upload"])

# 5 MiB. Large enough for a reasonable photo straight off a phone, small
# enough that a stray binary upload fails fast rather than tying up a worker.
MAX_IMAGE_BYTES = 5 * 1024 * 1024


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


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    if not (
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    ):
        # Fail with a clear 503 rather than letting Cloudinary return an
        # opaque auth error from inside the SDK.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload is not configured",
        )

    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read into memory with a hard cap. UploadFile streams off disk, so this
    # is bounded even for a client that lies about Content-Length.
    body = await file.read(MAX_IMAGE_BYTES + 1)
    if len(body) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )
    if len(body) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MiB limit",
        )

    _configure_cloudinary()
    try:
        result = cloudinary.uploader.upload(body, resource_type="image")
    except Exception as exc:  # cloudinary raises its own exception types
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image upload failed: {exc}",
        ) from exc

    url = result.get("secure_url") or result.get("url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image upload failed: provider returned no URL",
        )
    return success(data={"url": url}, message="Image uploaded")
