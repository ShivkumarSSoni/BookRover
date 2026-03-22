"""Unit tests for the Auth router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractAuthService injected via Depends(). No repository, no DynamoDB.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.interfaces.abstract_auth_service import AbstractAuthService
from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.routers.auth import get_auth_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    return MagicMock(spec=AbstractAuthService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import base64


def _make_token(email: str) -> str:
    return base64.urlsafe_b64encode(email.encode()).decode()


SELLER_EMAIL = "anand@example.com"
GL_EMAIL = "ravi@example.com"
ADMIN_EMAIL = "admin@example.com"

SELLER_ME = MeResponse(email=SELLER_EMAIL, roles=["seller"], seller_id="sel-001")
GL_ME = MeResponse(email=GL_EMAIL, roles=["group_leader"], group_leader_id="gl-001")
ADMIN_ME = MeResponse(email=ADMIN_EMAIL, roles=["admin"])
NEW_USER_ME = MeResponse(email="new@example.com", roles=[])


# ---------------------------------------------------------------------------
# GET /me — happy paths
# ---------------------------------------------------------------------------


def test_get_me_returns_200_for_seller(client, mock_service):
    mock_service.get_me.return_value = SELLER_ME
    token = _make_token(SELLER_EMAIL)
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == ["seller"]
    assert body["seller_id"] == "sel-001"
    assert body["group_leader_id"] is None


def test_get_me_returns_200_for_group_leader(client, mock_service):
    mock_service.get_me.return_value = GL_ME
    token = _make_token(GL_EMAIL)
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == ["group_leader"]
    assert body["group_leader_id"] == "gl-001"


def test_get_me_returns_200_for_admin(client, mock_service):
    mock_service.get_me.return_value = ADMIN_ME
    token = _make_token(ADMIN_EMAIL)
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["roles"] == ["admin"]


def test_get_me_returns_200_for_new_user_with_empty_roles(client, mock_service):
    mock_service.get_me.return_value = NEW_USER_ME
    token = _make_token("new@example.com")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["roles"] == []


# ---------------------------------------------------------------------------
# GET /me — auth failures
# ---------------------------------------------------------------------------


def test_get_me_returns_401_when_no_authorization_header(client, mock_service):
    response = client.get("/me")
    assert response.status_code == 401


def test_get_me_returns_401_when_token_is_not_base64_email(client, mock_service):
    response = client.get("/me", headers={"Authorization": "Bearer not-a-valid-token!!"})
    assert response.status_code == 401


def test_get_me_calls_service_with_decoded_email(client, mock_service):
    mock_service.get_me.return_value = SELLER_ME
    token = _make_token(SELLER_EMAIL)
    client.get("/me", headers={"Authorization": f"Bearer {token}"})

    mock_service.get_me.assert_called_once_with(SELLER_EMAIL)


# ---------------------------------------------------------------------------
# POST /dev/mock-token — dev mode enabled (APP_ENV=dev by default in tests)
# ---------------------------------------------------------------------------


def test_mock_token_returns_200_with_token_and_email(client, mock_service):
    response = client.post("/dev/mock-token", json={"email": "test@example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "test@example.com"
    assert isinstance(body["token"], str)
    assert len(body["token"]) > 0


def test_mock_token_token_decodes_to_original_email(client, mock_service):
    email = "mytest@bookrover.com"
    response = client.post("/dev/mock-token", json={"email": email})

    body = response.json()
    import base64
    decoded = base64.urlsafe_b64decode(body["token"] + "==").decode()
    assert decoded == email


def test_mock_token_returns_422_for_invalid_email(client, mock_service):
    response = client.post("/dev/mock-token", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_mock_token_returns_404_when_app_env_is_prod(mock_service):
    """When APP_ENV=prod, POST /dev/mock-token must return 404."""
    from bookrover.config import Settings
    from bookrover.dependencies import get_settings

    prod_settings = Settings(app_env="prod")

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    app.dependency_overrides[get_settings] = lambda: prod_settings
    prod_client = TestClient(app)
    response = prod_client.post("/dev/mock-token", json={"email": "admin@example.com"})
    assert response.status_code == 404
