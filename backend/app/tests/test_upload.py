import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

ENDPOINT = "/api/v1/upload/image"


@pytest.fixture
def configured_cloudinary(monkeypatch):
    """Pretend Cloudinary is configured; replace the uploader with a stub."""
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "test-key")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "test-secret")

    import cloudinary.uploader

    def fake_upload(data, **kwargs):
        return {
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/v1/abc.png",
            "url": "http://res.cloudinary.com/test-cloud/image/upload/v1/abc.png",
        }

    monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)


# A tiny valid PNG: 1x1 pixel, transparent.
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00"
    b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def test_upload_requires_auth(client: AsyncClient, configured_cloudinary):
    resp = await client.post(
        ENDPOINT, files={"file": ("tiny.png", PNG_1x1, "image/png")}
    )
    assert resp.status_code == 401


async def test_upload_happy_path(
    client: AsyncClient, student_token: str, configured_cloudinary
):
    resp = await client.post(
        ENDPOINT,
        files={"file": ("tiny.png", PNG_1x1, "image/png")},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["url"].startswith("https://res.cloudinary.com/")


async def test_upload_rejects_non_image(
    client: AsyncClient, student_token: str, configured_cloudinary
):
    resp = await client.post(
        ENDPOINT,
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400


async def test_upload_rejects_empty_file(
    client: AsyncClient, student_token: str, configured_cloudinary
):
    resp = await client.post(
        ENDPOINT,
        files={"file": ("tiny.png", b"", "image/png")},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400


async def test_upload_rejects_oversized_file(
    client: AsyncClient, student_token: str, configured_cloudinary
):
    oversized = b"\x00" * (5 * 1024 * 1024 + 10)
    resp = await client.post(
        ENDPOINT,
        files={"file": ("huge.png", oversized, "image/png")},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400


async def test_upload_503_when_cloudinary_not_configured(
    client: AsyncClient, student_token: str, monkeypatch
):
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "")

    resp = await client.post(
        ENDPOINT,
        files={"file": ("tiny.png", PNG_1x1, "image/png")},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 503
