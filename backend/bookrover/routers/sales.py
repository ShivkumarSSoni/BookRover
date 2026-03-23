"""Sales router — HTTP endpoints for recording and retrieving seller sales.

Handles all HTTP concerns for the /sellers/{seller_id}/sales prefix:
- Parses and validates incoming requests via Pydantic models.
- Delegates all business logic to the injected AbstractSaleService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → SaleService → this router
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.bad_request import InsufficientInventoryError
from bookrover.exceptions.conflict import SellerPendingReturnError
from bookrover.exceptions.not_found import BookNotFoundError, SaleNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_sale_service import AbstractSaleService
from bookrover.models.auth import MeResponse
from bookrover.models.sale import SaleCreate, SaleResponse
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import require_seller
from bookrover.services.sale_service import SaleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["Sales"])


# ------------------------------------------------------------------
# Dependency provider
# ------------------------------------------------------------------


def get_sale_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractSaleService:
    """Build and return a SaleService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete SaleService with DynamoDB repositories injected.
    """
    sales_table = dynamodb.Table(settings.get_table_name("sales"))
    inventory_table = dynamodb.Table(settings.get_table_name("inventory"))
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))

    return SaleService(
        sale_repository=DynamoDBSaleRepository(table=sales_table),
        inventory_repository=DynamoDBInventoryRepository(table=inventory_table),
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/{seller_id}/sales",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new sale",
    description=(
        "Records a new sale for the seller. Validates each book's stock level "
        "before writing — if any book has insufficient inventory the request is rejected. "
        "After persisting the sale, current_count is decremented for each sold book. "
        "Returns 404 if seller or any book is not found, 400 if stock is insufficient, "
        "or 409 if the seller's status is 'pending_return'."
    ),
)
async def create_sale(
    seller_id: str,
    payload: SaleCreate,
    service: AbstractSaleService = Depends(get_sale_service),
    current_user: MeResponse = Depends(require_seller),
) -> SaleResponse:
    """Record a new sale for a seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        payload: Validated SaleCreate request body (buyer details + items).
        service: Injected SaleService.
        current_user: Resolved seller identity.

    Returns:
        SaleResponse for the created sale.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If seller or any book_id does not exist.
        HTTPException 400: If quantity_sold exceeds current_count for any book.
        HTTPException 409: If seller status is 'pending_return'.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.create_sale(seller_id, payload)
    except SellerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientInventoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SellerPendingReturnError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/{seller_id}/sales",
    response_model=List[SaleResponse],
    status_code=status.HTTP_200_OK,
    summary="List all sales for a seller",
    description=(
        "Returns a list of all sale records for the seller, ordered by insertion order. "
        "Returns an empty list if no sales have been recorded. "
        "Does not return 404 for unknown sellers — callers are expected to verify "
        "seller existence through the seller endpoint if needed."
    ),
)
async def list_sales(
    seller_id: str,
    service: AbstractSaleService = Depends(get_sale_service),
    current_user: MeResponse = Depends(require_seller),
) -> List[SaleResponse]:
    """List all sales for a seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        service: Injected SaleService.
        current_user: Resolved seller identity.

    Returns:
        List of SaleResponse objects (may be empty).

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    return service.list_sales(seller_id)


@router.get(
    "/{seller_id}/sales/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single sale",
    description=(
        "Returns the full detail of a single sale record. "
        "Returns 404 if the sale does not exist or does not belong to the given seller."
    ),
)
async def get_sale(
    seller_id: str,
    sale_id: str,
    service: AbstractSaleService = Depends(get_sale_service),
    current_user: MeResponse = Depends(require_seller),
) -> SaleResponse:
    """Retrieve a single sale by ID, scoped to the seller.

    Args:
        seller_id: UUID of the seller from the path parameter.
        sale_id: UUID of the sale from the path parameter.
        service: Injected SaleService.
        current_user: Resolved seller identity.

    Returns:
        SaleResponse for the matching sale.

    Raises:
        HTTPException 403: If the caller is not the seller identified by seller_id.
        HTTPException 404: If sale not found or belongs to a different seller.
    """
    if current_user.seller_id != seller_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    try:
        return service.get_sale(seller_id, sale_id)
    except SaleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
