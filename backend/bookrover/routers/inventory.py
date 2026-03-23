"""Inventory router — HTTP endpoints for seller book inventory management.

Handles all HTTP concerns for the /sellers/{seller_id}/inventory prefix:
- Parses and validates incoming requests via Pydantic models.
- Delegates all business logic to the injected AbstractInventoryService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → InventoryService → this router
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.conflict import BookPartiallySoldError
from bookrover.exceptions.not_found import BookNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_inventory_service import AbstractInventoryService
from bookrover.models.auth import MeResponse
from bookrover.models.inventory import (
    BookCreate,
    BookResponse,
    BookUpdate,
    InventoryListResponse,
)
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import require_seller
from bookrover.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["Inventory"])


# ------------------------------------------------------------------
# Dependency provider
# ------------------------------------------------------------------


def get_inventory_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractInventoryService:
    """Build and return an InventoryService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete InventoryService with DynamoDB repositories injected.
    """
    inventory_table = dynamodb.Table(settings.get_table_name("inventory"))
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))

    inventory_repo = DynamoDBInventoryRepository(table=inventory_table)
    seller_repo = DynamoDBSellerRepository(table=sellers_table)

    return InventoryService(
        inventory_repository=inventory_repo,
        seller_repository=seller_repo,
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/{seller_id}/inventory",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a book to seller inventory",
    description=(
        "Adds a new book to the seller's inventory. The bookstore_id is derived "
        "automatically from the seller's profile. current_count is set equal to "
        "initial_count on creation. Returns 404 if the seller does not exist."
    ),
)
async def add_book(
    seller_id: str,
    payload: BookCreate,
    service: AbstractInventoryService = Depends(get_inventory_service),
    current_user: MeResponse = Depends(require_seller),
) -> BookResponse:
    """Add a book to a seller's inventory.

    Args:
        seller_id: UUID of the seller from the path parameter.
        payload: Validated BookCreate request body.
        service: Injected InventoryService.
        current_user: Resolved seller identity.

    Returns:
        BookResponse for the created book.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If seller does not exist.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.add_book(seller_id, payload)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{seller_id}/inventory",
    response_model=InventoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List seller inventory",
    description=(
        "Returns all books in a seller's inventory with an aggregate summary "
        "(total books in hand, total cost balance). Returns 404 if seller not found."
    ),
)
async def get_inventory(
    seller_id: str,
    service: AbstractInventoryService = Depends(get_inventory_service),
    current_user: MeResponse = Depends(require_seller),
) -> InventoryListResponse:
    """List all inventory books for a seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        service: Injected InventoryService.
        current_user: Resolved seller identity.

    Returns:
        InventoryListResponse with books list and summary.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If seller does not exist.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.get_inventory(seller_id)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/{seller_id}/inventory/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a book in seller inventory",
    description=(
        "Updates book_name, language, cost_per_book, and/or selling_price. "
        "current_count is managed exclusively by the sales flow. "
        "Returns 404 if the book does not exist or does not belong to this seller."
    ),
)
async def update_book(
    seller_id: str,
    book_id: str,
    payload: BookUpdate,
    service: AbstractInventoryService = Depends(get_inventory_service),
    current_user: MeResponse = Depends(require_seller),
) -> BookResponse:
    """Update a book in a seller's inventory.

    Args:
        seller_id: UUID of the seller from the path parameter.
        book_id: UUID of the book from the path parameter.
        payload: Validated BookUpdate request body.
        service: Injected InventoryService.
        current_user: Resolved seller identity.

    Returns:
        Updated BookResponse.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If book not found or does not belong to seller.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.update_book(seller_id, book_id, payload)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{seller_id}/inventory/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a book from seller inventory",
    description=(
        "Removes a book from inventory. Only permitted if the book has not been "
        "partially sold (current_count must equal initial_count). "
        "Returns 409 if the book has been partially sold."
    ),
)
async def remove_book(
    seller_id: str,
    book_id: str,
    service: AbstractInventoryService = Depends(get_inventory_service),
    current_user: MeResponse = Depends(require_seller),
) -> None:
    """Remove a book from a seller's inventory.

    Args:
        seller_id: UUID of the seller from the path parameter.
        book_id: UUID of the book from the path parameter.
        service: Injected InventoryService.
        current_user: Resolved seller identity.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If book not found or does not belong to seller.
        HTTPException 409: If book has been partially sold.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        service.remove_book(seller_id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookPartiallySoldError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
