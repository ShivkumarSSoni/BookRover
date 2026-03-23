"""Seller router — handles HTTP for seller registration and profile retrieval.

Handles all HTTP concerns for the /sellers prefix:
- Parses and validates incoming requests via Pydantic models.
- Delegates all business logic to the injected AbstractSellerService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → SellerService → this router
"""

import logging

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
from bookrover.models.auth import MeResponse
from bookrover.models.seller import SellerCreate, SellerResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import get_current_user
from bookrover.services.seller_service import SellerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["Sellers"])


# ------------------------------------------------------------------
# Dependency provider
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


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new seller",
    description=(
        "Registers a new seller with the given personal details and assignment. "
        "Returns 409 if the email is already registered, 404 if the group_leader_id "
        "or bookstore_id does not exist."
    ),
)
async def register_seller(
    payload: SellerCreate,
    service: AbstractSellerService = Depends(get_seller_service),
    current_user: MeResponse = Depends(get_current_user),
) -> SellerResponse:
    """Register a new seller.

    Requires authentication. The email in the payload must match the caller's
    authenticated email — a user cannot register a seller profile for someone else.

    Args:
        payload: Validated SellerCreate request body.
        service: Injected SellerService.
        current_user: Resolved caller identity.

    Returns:
        SellerResponse for the created seller.

    Raises:
        HTTPException 403: If payload email does not match the caller's email.
        HTTPException 409: If email is already registered.
        HTTPException 404: If group_leader_id or bookstore_id not found.
    """
    if str(payload.email).lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: email must match your authenticated identity.",
        )
    try:
        return service.register_seller(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GroupLeaderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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
