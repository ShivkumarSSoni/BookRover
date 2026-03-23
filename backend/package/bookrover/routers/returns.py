"""Returns router — HTTP endpoints for the Seller Return Books feature.

Handles:
  - GET /sellers/{seller_id}/return-summary — what to bring back to the bookstore.
  - POST /sellers/{seller_id}/returns — submit the return, clear inventory, reset status.

Delegates all business logic to the injected AbstractReturnService.
Translates domain exceptions to appropriate HTTP responses.
Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → ReturnService → this router
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.not_found import BookStoreNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_return_service import AbstractReturnService
from bookrover.models.return_models import ReturnCreate, ReturnResponse, ReturnSummaryResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.return_repository import DynamoDBReturnRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.services.return_service import ReturnService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["Returns"])


# ------------------------------------------------------------------
# Dependency provider
# ------------------------------------------------------------------


def get_return_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractReturnService:
    """Build and return a ReturnService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete ReturnService with all five DynamoDB repositories injected.
    """
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))
    bookstores_table = dynamodb.Table(settings.get_table_name("bookstores"))
    inventory_table = dynamodb.Table(settings.get_table_name("inventory"))
    sales_table = dynamodb.Table(settings.get_table_name("sales"))
    returns_table = dynamodb.Table(settings.get_table_name("returns"))

    return ReturnService(
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
        bookstore_repository=DynamoDBBookstoreRepository(table=bookstores_table),
        inventory_repository=DynamoDBInventoryRepository(table=inventory_table),
        sale_repository=DynamoDBSaleRepository(table=sales_table),
        return_repository=DynamoDBReturnRepository(table=returns_table),
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{seller_id}/return-summary",
    response_model=ReturnSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get return summary for a seller",
    description=(
        "Returns what the seller needs to physically bring back to the bookstore: "
        "the bookstore contact details, the list of unsold books (current_count > 0), "
        "total cost of unsold stock, and total money collected from all sales. "
        "Returns 404 if the seller or their bookstore cannot be found."
    ),
)
async def get_return_summary(
    seller_id: str,
    service: AbstractReturnService = Depends(get_return_service),
) -> ReturnSummaryResponse:
    """Retrieve the return summary for a seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        service: Injected ReturnService.

    Returns:
        ReturnSummaryResponse with bookstore info, books to return, and totals.

    Raises:
        HTTPException 404: If the seller or their bookstore is not found.
    """
    try:
        return service.get_return_summary(seller_id)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{seller_id}/returns",
    response_model=ReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a book return",
    description=(
        "Records the physical return of unsold books and collected money to the bookstore. "
        "Side effects: clears all inventory for the seller and resets their status to 'active'. "
        "Returns 404 if the seller cannot be found."
    ),
)
async def submit_return(
    seller_id: str,
    payload: ReturnCreate,
    service: AbstractReturnService = Depends(get_return_service),
) -> ReturnResponse:
    """Submit a return for a seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        payload: ReturnCreate with optional notes.
        service: Injected ReturnService.

    Returns:
        ReturnResponse representing the completed return record.

    Raises:
        HTTPException 404: If the seller is not found.
    """
    try:
        return service.submit_return(seller_id, payload.notes)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
