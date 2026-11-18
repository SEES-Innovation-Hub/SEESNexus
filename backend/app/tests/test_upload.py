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


async def test_upload_checks_the_bytes_not_the_label(
    client: AsyncClient, student_token: str, configured_cloudinary
):
    # A script renamed to .png and labelled image/png is still refused.
    disguised = await client.post(
        ENDPOINT,
        files={"file": ("cat.png", b"<script>alert(1)</script>", "image/png")},
        headers=auth_header(student_token),
    )
    assert disguised.status_code == 400
    svg = await client.post(
        ENDPOINT,
        files={"file": ("logo.svg", b'<svg xmlns="http://www.w3.org/2000/svg"/>', "image/svg+xml")},
        headers=auth_header(student_token),
    )
    assert svg.status_code == 400
    assert svg.json()["message"] == "File must be a JPEG, PNG, WebP or GIF image"


async def test_provider_errors_are_not_leaked(
    client: AsyncClient, student_token: str, configured_cloudinary, monkeypatch
):
    import cloudinary.uploader

    def broken(data, **kwargs):
        raise RuntimeError("Invalid api_key test-key for cloud test-cloud")

    monkeypatch.setattr(cloudinary.uploader, "upload", broken)
    resp = await client.post(
        ENDPOINT, files={"file": ("tiny.png", PNG_1x1, "image/png")}, headers=auth_header(student_token)
    )
    assert resp.status_code == 502
    assert "test-key" not in resp.json()["message"]


async def test_real_sdk_sends_a_signed_upload(client: AsyncClient, student_token: str, monkeypatch):
    """The real Cloudinary SDK, pointed at a local stand-in for api.cloudinary.com.

    The other tests replace the SDK call; this one checks what our settings
    make it actually send: a signed multipart POST to the account's upload
    endpoint, into our folder, and that we return the secure_url it answers.
    """
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    import cloudinary

    seen: dict = {}

    class FakeCloudinary(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (http.server's naming)
            seen["path"] = self.path
            seen["body"] = self.rfile.read(int(self.headers["Content-Length"]))
            payload = json.dumps(
                {"secure_url": "https://res.cloudinary.com/sees-test/image/upload/v1/sees-nexus/x.png"}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), FakeCloudinary)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "sees-test")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "123456789")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "not-a-real-secret")
    cloudinary.config(upload_prefix=f"http://127.0.0.1:{server.server_port}")
    try:
        resp = await client.post(
            ENDPOINT, files={"file": ("tiny.png", PNG_1x1, "image/png")}, headers=auth_header(student_token)
        )
    finally:
        server.shutdown()
        cloudinary.config(upload_prefix=None)

    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["url"].endswith("/sees-nexus/x.png")
    assert seen["path"] == "/v1_1/sees-test/image/upload"
    body = seen["body"]
    for field in (b'name="signature"', b'name="api_key"', b"123456789", b'name="folder"', b"sees-nexus"):
        assert field in body
    assert b"not-a-real-secret" not in body  # the secret signs the request; it is never sent
    assert PNG_1x1 in body
