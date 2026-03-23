"""Admin router for BookStore and GroupLeader CRUD endpoints.

Handles all HTTP concerns for the /admin prefix:
- Parses and validates incoming requests via Pydantic models.
- Delegates all business logic to the injected AbstractAdminService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → AdminService → this router
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.conflict import ActiveSellersExistError, DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
)
from bookrover.interfaces.abstract_admin_service import AbstractAdminService
from bookrover.models.auth import MeResponse
from bookrover.models.bookstore import (
    BookStoreCreate,
    BookStoreResponse,
    BookStoreUpdate,
)
from bookrover.models.group_leader import (
    GroupLeaderCreate,
    GroupLeaderResponse,
    GroupLeaderUpdate,
)
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.routers.auth import require_admin
from bookrover.services.admin_service import AdminService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ------------------------------------------------------------------
# Dependency providers for this router
# ------------------------------------------------------------------


def get_admin_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractAdminService:
    """Build and return an AdminService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete AdminService instance with DynamoDB repositories injected.
    """
    bookstore_table = dynamodb.Table(settings.get_table_name("bookstores"))
    group_leaders_table = dynamodb.Table(settings.get_table_name("group-leaders"))
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))

    bookstore_repo = DynamoDBBookstoreRepository(table=bookstore_table)
    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=sellers_table,
    )
    return AdminService(
        bookstore_repository=bookstore_repo,
        group_leader_repository=group_leader_repo,
    )


# ------------------------------------------------------------------
# BookStore endpoints
# ------------------------------------------------------------------


@router.post(
    "/bookstores",
    response_model=BookStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a BookStore",
    description="Create a new bookstore record. Returns the created bookstore with its generated ID and timestamps.",
)
async def create_bookstore(
    payload: BookStoreCreate,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> BookStoreResponse:
    """Create a new BookStore."""
    return service.create_bookstore(payload)


@router.get(
    "/bookstores",
    response_model=List[BookStoreResponse],
    status_code=status.HTTP_200_OK,
    summary="List all BookStores",
    description="Return all bookstores registered in the system.",
)
async def list_bookstores(
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> List[BookStoreResponse]:
    """List all BookStores."""
    return service.list_bookstores()


@router.put(
    "/bookstores/{bookstore_id}",
    response_model=BookStoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a BookStore",
    description="Partially update an existing bookstore. Only supplied fields are changed.",
)
async def update_bookstore(
    bookstore_id: str,
    payload: BookStoreUpdate,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> BookStoreResponse:
    """Update a BookStore by ID."""
    try:
        return service.update_bookstore(bookstore_id, payload)
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/bookstores/{bookstore_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a BookStore",
    description="Delete a bookstore by ID. Returns 409 if the bookstore has associated inventory.",
)
async def delete_bookstore(
    bookstore_id: str,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> None:
    """Delete a BookStore by ID."""
    try:
        service.delete_bookstore(bookstore_id)
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ------------------------------------------------------------------
# GroupLeader endpoints
# ------------------------------------------------------------------


@router.post(
    "/group-leaders",
    response_model=GroupLeaderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Group Leader",
    description="Create a new group leader. Email must be unique across all group leaders.",
)
async def create_group_leader(
    payload: GroupLeaderCreate,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> GroupLeaderResponse:
    """Create a new GroupLeader."""
    try:
        return service.create_group_leader(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/group-leaders",
    response_model=List[GroupLeaderResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Group Leaders",
    description="Return all group leaders registered in the system.",
)
async def list_group_leaders(
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> List[GroupLeaderResponse]:
    """List all GroupLeaders."""
    return service.list_group_leaders()


@router.put(
    "/group-leaders/{group_leader_id}",
    response_model=GroupLeaderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a Group Leader",
    description="Partially update an existing group leader. Email cannot be changed after creation.",
)
async def update_group_leader(
    group_leader_id: str,
    payload: GroupLeaderUpdate,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> GroupLeaderResponse:
    """Update a GroupLeader by ID."""
    try:
        return service.update_group_leader(group_leader_id, payload)
    except GroupLeaderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/group-leaders/{group_leader_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Group Leader",
    description="Delete a group leader by ID. Returns 409 if any sellers are still assigned.",
)
async def delete_group_leader(
    group_leader_id: str,
    service: AbstractAdminService = Depends(get_admin_service),
    current_user: MeResponse = Depends(require_admin),
) -> None:
    """Delete a GroupLeader by ID."""
    try:
        service.delete_group_leader(group_leader_id)
    except GroupLeaderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ActiveSellersExistError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
