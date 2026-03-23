"""Unit tests for the BookRover FastAPI application factory (main.py).

Covers middleware behaviour — specifically the BodySizeLimitMiddleware that
rejects oversized request bodies with HTTP 413 before they reach route handlers.
"""

import pytest
from fastapi.testclient import TestClient

from bookrover.main import create_app, _MAX_BODY_BYTES

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Plain TestClient — no dependency overrides needed for middleware tests."""
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# BodySizeLimitMiddleware
# ---------------------------------------------------------------------------


def test_body_size_limit_returns_413_when_content_length_exceeds_limit(client):
    """Requests with Content-Length > 512 000 bytes must be rejected with 413."""
    oversized = _MAX_BODY_BYTES + 1
    response = client.post(
        "/dev/mock-token",
        content=b"x" * oversized,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(oversized),
        },
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_body_size_limit_returns_413_exactly_one_byte_over(client):
    """Content-Length of exactly max+1 must be rejected."""
    oversized = _MAX_BODY_BYTES + 1
    response = client.post(
        "/dev/mock-token",
        content=b"x",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(oversized),
        },
    )

    assert response.status_code == 413


def test_body_size_limit_passes_request_at_exact_limit(client):
    """A request whose Content-Length exactly equals the limit must not be rejected by the middleware."""
    # We send a small body but advertise Content-Length == limit; the middleware
    # only checks the header, so this should be passed through (the route itself
    # may reject it for other reasons — we only assert it is NOT 413).
    response = client.post(
        "/dev/mock-token",
        content=b"{}",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(_MAX_BODY_BYTES),
        },
    )

    assert response.status_code != 413


def test_body_size_limit_passes_normal_json_request(client):
    """A normal small JSON request must not be blocked by the body size middleware."""
    response = client.post(
        "/dev/mock-token",
        json={"email": "test@example.com"},
    )

    # 200 means the middleware passed it through (dev mode is default in tests)
    assert response.status_code == 200


def test_body_size_limit_is_not_triggered_for_get_requests(client):
    """GET requests with no body must not be affected by the body size middleware."""
    response = client.get("/me")

    # 401 because no auth header — middleware did not block it with 413
    assert response.status_code == 401
    assert response.status_code != 413
