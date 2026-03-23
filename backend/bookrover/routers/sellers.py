"""Seller router — handles HTTP for seller registration and profile retrieval.

Handles all HTTP concerns for the /sellers prefix:
- Parses and validates incoming requests via Pydantic models.
- Delegates all business logic to the injected AbstractSellerService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → SellerService → this router

Email verification flow (Gap 6 fix):
  1. POST /sellers/request-verification  — issues a 6-digit code, stores it
     with a 10-minute TTL.  In dev/test the code is returned in the response;
     in prod it would be delivered via SES (stubbed here with a log entry).
  2. POST /sellers                        — requires the code in the request
     body.  On success the code record is deleted (one-time use).
"""

import logging
import secrets

import boto3
from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.conflict import DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    SellerNotFoundError,
)
from bookrover.interfaces.abstract_seller_service import AbstractSellerService
from bookrover.interfaces.abstract_verification_repository import (
    AbstractVerificationRepository,
)
from bookrover.models.auth import MeResponse
from bookrover.models.seller import SellerCreate, SellerResponse
from bookrover.models.verification import VerificationRequest, VerificationResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.repositories.verification_repository import DynamoDBVerificationRepository
from bookrover.routers.auth import get_current_user
from bookrover.services.seller_service import SellerService
from bookrover.utils.timestamp import utc_now_iso, utc_plus_minutes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["Sellers"])

_VERIFICATION_CODE_TTL_MINUTES = 10
_SES_SUBJECT = "BookRover — Your seller registration code"
_SES_BODY_TEMPLATE = (
    "Your BookRover email verification code is: {code}\n\n"
    "This code expires in 10 minutes. Do not share it with anyone.\n\n"
    "If you did not request this code, ignore this email."
)


# ------------------------------------------------------------------
# Dependency providers
# ------------------------------------------------------------------


def get_seller_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractSellerService:
    """Build and return a SellerService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete SellerService instance with all DynamoDB repositories injected.
    """
    seller_table = dynamodb.Table(settings.get_table_name("sellers"))
    group_leaders_table = dynamodb.Table(settings.get_table_name("group-leaders"))
    sellers_table_for_gl = dynamodb.Table(settings.get_table_name("sellers"))
    bookstores_table = dynamodb.Table(settings.get_table_name("bookstores"))

    seller_repo = DynamoDBSellerRepository(table=seller_table)
    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=sellers_table_for_gl,
    )
    bookstore_repo = DynamoDBBookstoreRepository(table=bookstores_table)

    return SellerService(
        seller_repository=seller_repo,
        group_leader_repository=group_leader_repo,
        bookstore_repository=bookstore_repo,
    )


def get_verification_repo(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractVerificationRepository:
    """Build and return a DynamoDBVerificationRepository.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete DynamoDBVerificationRepository instance.
    """
    table = dynamodb.Table(settings.get_table_name("email-verifications"))
    return DynamoDBVerificationRepository(table=table)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _generate_verification_code() -> str:
    """Generate a cryptographically secure 6-digit numeric code.

    Returns:
        Six-character string of digits, zero-padded (e.g. '047392').
    """
    return str(secrets.randbelow(1_000_000)).zfill(6)


def _validate_and_consume_code(
    verification_repo: AbstractVerificationRepository,
    email: str,
    submitted_code: str,
) -> None:
    """Check that the submitted code matches the stored record and is not expired.

    Raises HTTP 422 (not 401/403) because the token is already valid — the
    caller is who they claim to be; the code is simply wrong or stale.

    Args:
        verification_repo: Injected verification repository.
        email: Normalised (lowercase) email address.
        submitted_code: Code from the SellerCreate payload.

    Raises:
        HTTPException 422: If no record exists, code does not match, or record
            has passed its expiry timestamp.
    """
    record = verification_repo.get(email)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No verification code found for this email. Call POST /sellers/request-verification first.",
        )
    if record["code"] != submitted_code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid verification code.",
        )
    if utc_now_iso() > record["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verification code has expired. Request a new one via POST /sellers/request-verification.",
        )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/request-verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Request an email verification code before seller registration",
    description=(
        "Generates a 6-digit one-time code and associates it with the caller's "
        "email address for 10 minutes.  The code must be included in the subsequent "
        "POST /sellers call as ``verification_code``.\n\n"
        "**Dev/test mode:** the code is returned directly in the response body.\n\n"
        "**Production:** the code is sent to the caller's email address via SES "
        "and is NOT included in the response.\n\n"
        "The caller's email must match the email in the request body."
    ),
)
async def request_verification(
    payload: VerificationRequest,
    settings: Settings = Depends(get_settings),
    verification_repo: AbstractVerificationRepository = Depends(get_verification_repo),
    current_user: MeResponse = Depends(get_current_user),
) -> VerificationResponse:
    """Issue a short-lived verification code for the caller's email.

    Args:
        payload: VerificationRequest with the email to verify.
        settings: Injected application settings.
        verification_repo: Injected verification repository.
        current_user: Resolved caller identity.

    Returns:
        VerificationResponse with the code (dev/test) or a generic message (prod).

    Raises:
        HTTPException 403: If payload email does not match the caller's email.
    """
    email = str(payload.email).lower()
    if email != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: email must match your authenticated identity.",
        )

    code = _generate_verification_code()
    expires_at = utc_plus_minutes(_VERIFICATION_CODE_TTL_MINUTES)
    verification_repo.save(email, code, expires_at)

    if settings.app_env == "prod":
        boto3.client("ses", region_name=settings.dynamodb_region).send_email(
            Source=settings.ses_sender_email,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": _SES_SUBJECT, "Charset": "UTF-8"},
                "Body": {
                    "Text": {
                        "Data": _SES_BODY_TEMPLATE.format(code=code),
                        "Charset": "UTF-8",
                    }
                },
            },
        )
        logger.info("Verification code sent via SES for seller registration")
        return VerificationResponse(message="Verification code sent to your email address.")

    # Dev / test: return code directly so callers don't need a real inbox.
    return VerificationResponse(
        message="Verification code issued (dev mode — code included in response).",
        code=code,
    )


@router.post(
    "",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new seller",
    description=(
        "Registers a new seller with the given personal details and assignment. "
        "Requires a valid ``verification_code`` previously issued by "
        "POST /sellers/request-verification — the code is consumed on success "
        "and cannot be reused.\n\n"
        "Returns 409 if the email is already registered, 404 if the "
        "group_leader_id or bookstore_id does not exist, 422 if the "
        "verification code is missing, invalid, or expired."
    ),
)
async def register_seller(
    payload: SellerCreate,
    service: AbstractSellerService = Depends(get_seller_service),
    verification_repo: AbstractVerificationRepository = Depends(get_verification_repo),
    current_user: MeResponse = Depends(get_current_user),
) -> SellerResponse:
    """Register a new seller.

    Requires authentication. The email in the payload must match the caller's
    authenticated email — a user cannot register a seller profile for someone
    else.  The verification_code must have been obtained via
    POST /sellers/request-verification and must not be expired.

    Args:
        payload: Validated SellerCreate request body (includes verification_code).
        service: Injected SellerService.
        verification_repo: Injected verification repository.
        current_user: Resolved caller identity.

    Returns:
        SellerResponse for the created seller.

    Raises:
        HTTPException 403: If payload email does not match the caller's email.
        HTTPException 422: If the verification code is missing, wrong, or expired.
        HTTPException 409: If email is already registered.
        HTTPException 404: If group_leader_id or bookstore_id not found.
    """
    email = str(payload.email).lower()
    if email != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: email must match your authenticated identity.",
        )

    _validate_and_consume_code(verification_repo, email, payload.verification_code)

    try:
        result = service.register_seller(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GroupLeaderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Code was valid — delete it so it cannot be reused.
    verification_repo.delete(email)
    return result


@router.get(
    "/{seller_id}",
    response_model=SellerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get seller by ID",
    description="Returns the seller profile for the given seller_id. Returns 404 if not found.",
)
async def get_seller(
    seller_id: str,
    service: AbstractSellerService = Depends(get_seller_service),
    current_user: MeResponse = Depends(get_current_user),
) -> SellerResponse:
    """Retrieve a seller profile by ID.

    Accessible by the seller themselves (own profile only) or by admin.

    Args:
        seller_id: UUID of the seller from the path parameter.
        service: Injected SellerService.
        current_user: Resolved caller identity.

    Returns:
        SellerResponse for the seller.

    Raises:
        HTTPException 403: If the caller is not admin and not the seller themselves.
        HTTPException 404: If no seller exists with the given ID.
    """
    is_admin = "admin" in current_user.roles
    is_own_profile = (
        "seller" in current_user.roles and current_user.seller_id == seller_id
    )
    if not (is_admin or is_own_profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.get_seller(seller_id)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
