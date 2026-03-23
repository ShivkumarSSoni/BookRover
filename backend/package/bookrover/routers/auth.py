"""Auth router — provides identity resolution and dev login endpoints.

Handles:
- GET /me         — decode the caller's token, resolve their BookRover roles.
- POST /dev/mock-token — (dev only) issue a token for any email address.

In development (APP_ENV=dev) the token is base64url(email). There is no
cryptographic security — this is a local dev shortcut only.

In production (APP_ENV=prod) the /dev/mock-token endpoint returns 404 and
GET /me would validate a real Cognito JWT (deferred to Phase 6).
"""

import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.interfaces.abstract_auth_service import AbstractAuthService
from bookrover.models.auth import MeResponse, MockTokenRequest, MockTokenResponse
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])

_TOKEN_ENCODING = "utf-8"


# ---------------------------------------------------------------------------
# Dependency provider
# ---------------------------------------------------------------------------


def get_auth_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractAuthService:
    """Build and return an AuthService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete AuthService instance.
    """
    seller_table = dynamodb.Table(settings.get_table_name("sellers"))
    group_leaders_table = dynamodb.Table(settings.get_table_name("group-leaders"))

    seller_repo = DynamoDBSellerRepository(table=seller_table)
    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=seller_table,
    )

    return AuthService(
        seller_repository=seller_repo,
        group_leader_repository=group_leader_repo,
        admin_emails=settings.admin_emails,
    )


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _encode_dev_token(email: str) -> str:
    """Encode an email address as a base64url dev token.

    Args:
        email: Email address to encode.

    Returns:
        URL-safe base64 string representing the email.
    """
    return base64.urlsafe_b64encode(email.encode(_TOKEN_ENCODING)).decode(_TOKEN_ENCODING)


def _decode_dev_token(token: str) -> str | None:
    """Decode a base64url dev token back to an email address.

    Args:
        token: base64url-encoded string from the Authorization header.

    Returns:
        Decoded email string, or None if decoding fails.
    """
    try:
        padding = 4 - len(token) % 4
        if padding != 4:
            token += "=" * padding
        decoded = base64.urlsafe_b64decode(token.encode(_TOKEN_ENCODING)).decode(_TOKEN_ENCODING)
        if "@" not in decoded:
            return None
        return decoded
    except Exception:
        return None


def _extract_bearer_token(request: Request) -> str | None:
    """Extract the Bearer token from the Authorization header.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Raw token string, or None if the header is absent or malformed.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user identity",
    description=(
        "Decodes the Bearer token from the Authorization header, resolves the "
        "caller's BookRover roles, and returns their identity. "
        "In dev mode the token is base64url(email). "
        "In production a Cognito JWT would be verified here (deferred)."
    ),
)
async def get_me(
    request: Request,
    settings: Settings = Depends(get_settings),
    auth_service: AbstractAuthService = Depends(get_auth_service),
) -> MeResponse:
    """Resolve the caller's BookRover identity from their Bearer token.

    Args:
        request: Incoming HTTP request (Authorization header is read here).
        settings: Injected application settings.
        auth_service: Injected AbstractAuthService.

    Returns:
        MeResponse with roles, seller_id, and group_leader_id.

    Raises:
        HTTPException 401: If no valid token is provided.
    """
    raw_token = _extract_bearer_token(request)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    email = _decode_dev_token(raw_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    return auth_service.get_me(email)


@router.post(
    "/dev/mock-token",
    response_model=MockTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue a dev login token (dev only)",
    description=(
        "Issues a base64url(email) dev token for any email address. "
        "Only available when APP_ENV is not 'prod'. Returns 404 in production. "
        "Pass the returned token as Authorization: Bearer <token> on all subsequent requests."
    ),
)
async def mock_token(
    payload: MockTokenRequest,
    settings: Settings = Depends(get_settings),
) -> MockTokenResponse:
    """Issue a dev token for any email address (development only).

    Args:
        payload: MockTokenRequest with the desired email address.
        settings: Injected application settings.

    Returns:
        MockTokenResponse with the token and email.

    Raises:
        HTTPException 404: If APP_ENV is not 'dev'.
    """
    if settings.app_env == "prod":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )

    token = _encode_dev_token(str(payload.email))
    logger.debug("mock_token issued", extra={"email": str(payload.email)})
    return MockTokenResponse(token=token, email=str(payload.email))
