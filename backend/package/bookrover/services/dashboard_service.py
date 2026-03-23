"""Business logic layer for the Group Leader Dashboard feature.

Aggregates per-seller sales data to produce the dashboard view.
Has zero knowledge of DynamoDB, HTTP, or Lambda — all external concerns
are injected through repository abstractions.
"""

import logging
from typing import List

from bookrover.exceptions.not_found import BookStoreNotFoundError, GroupLeaderNotFoundError
from bookrover.interfaces.abstract_bookstore_repository import AbstractBookstoreRepository
from bookrover.interfaces.abstract_dashboard_service import AbstractDashboardService
from bookrover.interfaces.abstract_group_leader_repository import AbstractGroupLeaderRepository
from bookrover.interfaces.abstract_sale_repository import AbstractSaleRepository
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.models.dashboard import (
    DashboardBookstore,
    DashboardGroupLeader,
    DashboardResponse,
    DashboardSellerRow,
    DashboardTotals,
    SortByField,
    SortOrder,
)

logger = logging.getLogger(__name__)


class DashboardService(AbstractDashboardService):
    """Concrete implementation of AbstractDashboardService.

    Aggregates sales data across all sellers for a group leader's bookstore
    context to produce a sortable performance dashboard.

    Args:
        group_leader_repository: Injected AbstractGroupLeaderRepository.
        bookstore_repository: Injected AbstractBookstoreRepository.
        seller_repository: Injected AbstractSellerRepository.
        sale_repository: Injected AbstractSaleRepository.
    """

    def __init__(
        self,
        group_leader_repository: AbstractGroupLeaderRepository,
        bookstore_repository: AbstractBookstoreRepository,
        seller_repository: AbstractSellerRepository,
        sale_repository: AbstractSaleRepository,
    ) -> None:
        self._group_leader_repository = group_leader_repository
        self._bookstore_repository = bookstore_repository
        self._seller_repository = seller_repository
        self._sale_repository = sale_repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dashboard(
        self,
        group_leader_id: str,
        bookstore_id: str,
        sort_by: SortByField,
        sort_order: SortOrder,
    ) -> DashboardResponse:
        """Build and return a dashboard for a group leader + bookstore context.

        Validates the group leader and bookstore, gathers all sellers for the
        combination, aggregates their sales totals, sorts the rows, and returns
        a complete DashboardResponse.

        Args:
            group_leader_id: UUID of the group leader.
            bookstore_id: UUID of the bookstore whose sellers to aggregate.
            sort_by: Field to sort sellers by.
            sort_order: Direction to sort.

        Returns:
            DashboardResponse with per-seller rows and aggregate totals.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
            BookStoreNotFoundError: If the bookstore does not exist or is not
                linked to this group leader.
        """
        group_leader = self._group_leader_repository.get_by_id(group_leader_id)
        if group_leader is None:
            raise GroupLeaderNotFoundError(group_leader_id)

        if bookstore_id not in group_leader.get("bookstore_ids", []):
            raise BookStoreNotFoundError(bookstore_id)

        bookstore = self._bookstore_repository.get_by_id(bookstore_id)
        if bookstore is None:
            raise BookStoreNotFoundError(bookstore_id)

        sellers = self._seller_repository.list_by_group_leader(group_leader_id)
        bookstore_sellers = [s for s in sellers if s.get("bookstore_id") == bookstore_id]

        seller_rows = self._build_seller_rows(bookstore_sellers)
        seller_rows = self._sort_rows(seller_rows, sort_by, sort_order)

        totals = DashboardTotals(
            total_books_sold=sum(r.total_books_sold for r in seller_rows),
            total_amount_collected=sum(r.total_amount_collected for r in seller_rows),
        )

        return DashboardResponse(
            group_leader=DashboardGroupLeader(
                group_leader_id=group_leader_id,
                name=group_leader["name"],
            ),
            bookstore=DashboardBookstore(
                bookstore_id=bookstore_id,
                store_name=bookstore["store_name"],
            ),
            sellers=seller_rows,
            totals=totals,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_seller_rows(self, sellers: list) -> List[DashboardSellerRow]:
        """Aggregate sales totals for each seller.

        Args:
            sellers: List of Seller dicts for the selected bookstore.

        Returns:
            List of DashboardSellerRow with aggregated totals.
        """
        rows: List[DashboardSellerRow] = []
        for seller in sellers:
            seller_id = seller["seller_id"]
            sales = self._sale_repository.list_by_seller(seller_id)
            total_books_sold = sum(int(s.get("total_books_sold", 0)) for s in sales)
            total_amount_collected = sum(float(s.get("total_amount_collected", 0)) for s in sales)
            rows.append(
                DashboardSellerRow(
                    seller_id=seller_id,
                    full_name=f"{seller['first_name']} {seller['last_name']}",
                    total_books_sold=total_books_sold,
                    total_amount_collected=total_amount_collected,
                )
            )
        return rows

    @staticmethod
    def _sort_rows(
        rows: List[DashboardSellerRow],
        sort_by: SortByField,
        sort_order: SortOrder,
    ) -> List[DashboardSellerRow]:
        """Sort seller rows by the given field and order.

        Args:
            rows: Unsorted list of DashboardSellerRow.
            sort_by: Field name to sort on.
            sort_order: 'asc' or 'desc'.

        Returns:
            New sorted list of DashboardSellerRow.
        """
        reverse = sort_order == "desc"
        return sorted(rows, key=lambda r: getattr(r, sort_by), reverse=reverse)
