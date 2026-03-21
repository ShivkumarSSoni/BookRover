"""Abstract base class for the Dashboard service port.

Services that depend on the dashboard feature use this abstraction —
never the concrete implementation — keeping layers independently testable.
"""

from abc import ABC, abstractmethod

from bookrover.models.dashboard import DashboardResponse, SortByField, SortOrder


class AbstractDashboardService(ABC):
    """Port definition for the Group Leader Dashboard business logic."""

    @abstractmethod
    def get_dashboard(
        self,
        group_leader_id: str,
        bookstore_id: str,
        sort_by: SortByField,
        sort_order: SortOrder,
    ) -> DashboardResponse:
        """Build and return a dashboard for a group leader + bookstore context.

        Args:
            group_leader_id: UUID of the group leader.
            bookstore_id: UUID of the bookstore whose sellers to aggregate.
            sort_by: Field to sort sellers by ('total_books_sold' or
                     'total_amount_collected').
            sort_order: Direction to sort ('asc' or 'desc').

        Returns:
            DashboardResponse with per-seller rows and aggregate totals.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
            BookStoreNotFoundError: If no bookstore exists with the given ID, or
                the bookstore is not linked to this group leader.
        """
