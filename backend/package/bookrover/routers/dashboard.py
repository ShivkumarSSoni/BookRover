"""Dashboard router — HTTP endpoint for the Group Leader performance dashboard.

Handles the GET /group-leaders/{group_leader_id}/dashboard endpoint:
- Parses query parameters (bookstore_id, sort_by, sort_order).
- Delegates all business logic to the injected AbstractDashboardService.
- Translates domain exceptions to appropriate HTTP responses.
- Never calls repositories directly.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → DashboardService → this router
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.exceptions.not_found import BookStoreNotFoundError, GroupLeaderNotFoundError
from bookrover.interfaces.abstract_dashboard_service import AbstractDashboardService
from bookrover.models.dashboard import (
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    DashboardResponse,
    SortByField,
    SortOrder,
)
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group-leaders", tags=["Dashboard"])


# ------------------------------------------------------------------
# Dependency provider
# ------------------------------------------------------------------


def get_dashboard_service(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
) -> AbstractDashboardService:
    """Build and return a DashboardService with fully wired repositories.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Concrete DashboardService with all four DynamoDB repositories injected.
    """
    group_leaders_table = dynamodb.Table(settings.get_table_name("group-leaders"))
    bookstores_table = dynamodb.Table(settings.get_table_name("bookstores"))
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))
    sales_table = dynamodb.Table(settings.get_table_name("sales"))

    return DashboardService(
        group_leader_repository=DynamoDBGroupLeaderRepository(
            table=group_leaders_table,
            sellers_table=sellers_table,
        ),
        bookstore_repository=DynamoDBBookstoreRepository(table=bookstores_table),
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
        sale_repository=DynamoDBSaleRepository(table=sales_table),
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "/{group_leader_id}/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Group Leader performance dashboard",
    description=(
        "Returns a performance summary for all sellers registered under the group leader "
        "for the specified bookstore. Each seller row shows total books sold and total amount "
        "collected across all recorded sales. Rows are sorted by the chosen field and direction. "
        "Returns 404 if the group leader or bookstore is not found, or if the bookstore "
        "is not linked to this group leader."
    ),
)
async def get_dashboard(
    group_leader_id: str,
    bookstore_id: str,
    sort_by: SortByField = DEFAULT_SORT_BY,
    sort_order: SortOrder = DEFAULT_SORT_ORDER,
    service: AbstractDashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    """Retrieve the group leader dashboard for a bookstore.

    Args:
        group_leader_id: UUID of the group leader from the path parameter.
        bookstore_id: UUID of the bookstore (required query parameter).
        sort_by: Field to sort sellers by (default: 'total_amount_collected').
        sort_order: Sort direction (default: 'desc').
        service: Injected DashboardService.

    Returns:
        DashboardResponse with per-seller rows and aggregate totals.

    Raises:
        HTTPException 404: If group leader or bookstore is not found, or
            the bookstore is not linked to this group leader.
    """
    try:
        return service.get_dashboard(group_leader_id, bookstore_id, sort_by, sort_order)
    except GroupLeaderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookStoreNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
