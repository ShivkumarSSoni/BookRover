"""Pydantic DTOs for the Group Leader Dashboard feature.

These models define the request query parameters and response shapes
for the GET /group-leaders/{group_leader_id}/dashboard endpoint.
"""

from typing import List, Literal

from pydantic import BaseModel


class DashboardGroupLeader(BaseModel):
    """Snapshot of the group leader identity embedded in the dashboard response."""

    group_leader_id: str
    name: str


class DashboardBookstore(BaseModel):
    """Snapshot of the bookstore context embedded in the dashboard response."""

    bookstore_id: str
    store_name: str


class DashboardSellerRow(BaseModel):
    """Performance summary for a single seller on the dashboard."""

    seller_id: str
    full_name: str
    total_books_sold: int
    total_amount_collected: float


class DashboardTotals(BaseModel):
    """Aggregate totals across all sellers in the dashboard."""

    total_books_sold: int
    total_amount_collected: float


class DashboardResponse(BaseModel):
    """Full dashboard response for a group leader + bookstore combination.

    Contains the group leader identity, selected bookstore, per-seller rows
    (sorted), and aggregate totals.
    """

    group_leader: DashboardGroupLeader
    bookstore: DashboardBookstore
    sellers: List[DashboardSellerRow]
    totals: DashboardTotals


# Allowed values for the sort_by and sort_order query parameters.
SortByField = Literal["total_books_sold", "total_amount_collected"]
SortOrder = Literal["asc", "desc"]

DEFAULT_SORT_BY: SortByField = "total_amount_collected"
DEFAULT_SORT_ORDER: SortOrder = "desc"
