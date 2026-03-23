"""Unit tests for the Auth router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractAuthService injected via Depends(). No repository, no DynamoDB.

Covers both dev/test mode (base64url token) and prod mode (Cognito JWT via
mocked CognitoJWTVerifier dependency).
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.interfaces.abstract_auth_service import AbstractAuthService
from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.routers.auth import get_auth_service, get_cognito_verifier
from bookrover.utils.cognito_jwt_verifier import CognitoJWTVerifier

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


# ---------------------------------------------------------------------------
# GET /me — production mode (Cognito JWT path)
# ---------------------------------------------------------------------------
# These tests override both get_settings (APP_ENV=prod) and
# get_cognito_verifier (mock verifier) so no real AWS calls are made.


def _make_prod_client(mock_service, mock_verifier):
    """Build a TestClient that simulates the production auth path.

    Both the auth service and the Cognito verifier are mocked, so no
    DynamoDB calls and no real JWT verification occur.

    Args:
        mock_service: MagicMock standing in for AbstractAuthService.
        mock_verifier: MagicMock standing in for CognitoJWTVerifier.

    Returns:
        FastAPI TestClient with production settings and mocked dependencies.
    """
    from bookrover.config import Settings
    from bookrover.dependencies import get_settings

    prod_settings = Settings(
        app_env="prod",
        cognito_user_pool_id="ap-south-1_TestPool",
        cognito_region="ap-south-1",
    )
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    app.dependency_overrides[get_settings] = lambda: prod_settings
    app.dependency_overrides[get_cognito_verifier] = lambda: mock_verifier
    return TestClient(app)


def test_get_me_prod_returns_200_when_verifier_succeeds(mock_service):
    """In prod mode, a valid Cognito token is verified and email passed to service."""
    email = "cognito.user@example.com"
    mock_verifier = MagicMock(spec=CognitoJWTVerifier)
    mock_verifier.verify.return_value = email
    mock_service.get_me.return_value = MeResponse(email=email, roles=["seller"])

    prod_client = _make_prod_client(mock_service, mock_verifier)
    response = prod_client.get(
        "/me", headers={"Authorization": "Bearer some.cognito.jwt"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == email
    mock_verifier.verify.assert_called_once_with("some.cognito.jwt")
    mock_service.get_me.assert_called_once_with(email)


def test_get_me_prod_passes_raw_token_to_verifier(mock_service):
    """The raw Bearer token string (without 'Bearer ' prefix) is passed to verify()."""
    mock_verifier = MagicMock(spec=CognitoJWTVerifier)
    mock_verifier.verify.return_value = "user@example.com"
    mock_service.get_me.return_value = MeResponse(email="user@example.com", roles=[])

    prod_client = _make_prod_client(mock_service, mock_verifier)
    prod_client.get("/me", headers={"Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9"})

    mock_verifier.verify.assert_called_once_with("eyJhbGciOiJSUzI1NiJ9")


def test_get_me_prod_returns_401_when_verifier_raises_value_error(mock_service):
    """If CognitoJWTVerifier.verify() raises ValueError, GET /me returns 401."""
    mock_verifier = MagicMock(spec=CognitoJWTVerifier)
    mock_verifier.verify.side_effect = ValueError("Token expired")

    prod_client = _make_prod_client(mock_service, mock_verifier)
    response = prod_client.get(
        "/me", headers={"Authorization": "Bearer expired.token.here"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token."


def test_get_me_prod_returns_401_when_no_authorization_header(mock_service):
    """In prod mode, a missing Authorization header still returns 401."""
    mock_verifier = MagicMock(spec=CognitoJWTVerifier)
    prod_client = _make_prod_client(mock_service, mock_verifier)

    response = prod_client.get("/me")

    assert response.status_code == 401
    mock_verifier.verify.assert_not_called()


def test_get_me_prod_does_not_call_dev_token_decoder(mock_service):
    """In prod mode, the base64url dev-token decoder is not used even for a valid base64 string."""
    import base64

    mock_verifier = MagicMock(spec=CognitoJWTVerifier)
    mock_verifier.verify.return_value = "user@example.com"
    mock_service.get_me.return_value = MeResponse(email="user@example.com", roles=[])

    # A valid dev token (base64url of email).  In prod mode this must go
    # through the verifier, not the dev decoder.
    dev_token = base64.urlsafe_b64encode(b"user@example.com").decode()
    prod_client = _make_prod_client(mock_service, mock_verifier)
    prod_client.get("/me", headers={"Authorization": f"Bearer {dev_token}"})

    # The verifier must have been called — not bypassed by the dev decoder.
    mock_verifier.verify.assert_called_once_with(dev_token)


# ---------------------------------------------------------------------------
# get_cognito_verifier — client_id wiring
# ---------------------------------------------------------------------------


def test_get_cognito_verifier_passes_client_id_from_settings():
    """get_cognito_verifier() must pass settings.cognito_client_id to CognitoJWTVerifier.

    This ensures the 'aud' claim is validated in production so tokens issued
    for a different Cognito app client are rejected.
    """
    from bookrover.config import Settings
    from bookrover.dependencies import get_settings
    from bookrover.routers.auth import get_cognito_verifier

    client_id = "my-app-client-id-12345"
    settings_with_client_id = Settings(
        app_env="prod",
        cognito_user_pool_id="ap-south-1_TestPool",
        cognito_region="ap-south-1",
        cognito_client_id=client_id,
    )

    # Call the dependency function directly (bypassing FastAPI DI) with the
    # settings object that has a non-empty client_id.
    verifier = get_cognito_verifier(settings=settings_with_client_id)

    # The internal _client_id attribute must match what was passed in settings.
    assert verifier._client_id == client_id


def test_get_cognito_verifier_uses_empty_client_id_by_default():
    """get_cognito_verifier() must leave client_id empty when COGNITO_CLIENT_ID is not set.

    This documents the current behaviour for dev/non-prod environments where
    audience validation is intentionally skipped.
    """
    from bookrover.config import Settings
    from bookrover.routers.auth import get_cognito_verifier

    settings_no_client_id = Settings(
        app_env="dev",
        cognito_user_pool_id="",
        cognito_region="ap-south-1",
        # cognito_client_id defaults to ""
    )

    verifier = get_cognito_verifier(settings=settings_no_client_id)

    assert verifier._client_id == ""

