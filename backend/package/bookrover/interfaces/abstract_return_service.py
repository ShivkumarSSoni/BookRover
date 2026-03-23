"""Abstract base class for the Return service port.

Routers depend on this ABC — never the concrete ReturnService.
This enables unit testing routers with a mock service (no business logic).
"""

from abc import ABC, abstractmethod
from typing import Optional

from bookrover.models.return_models import ReturnResponse, ReturnSummaryResponse


class AbstractReturnService(ABC):
    """Port definition for all Return business logic operations."""

    @abstractmethod
    def get_return_summary(self, seller_id: str) -> ReturnSummaryResponse:
        """Build the return summary for a seller.

        Computes what books remain in inventory and how much money has been
        collected from sales — the complete picture for the return trip.

        Args:
            seller_id: UUID of the seller.

        Returns:
            ReturnSummaryResponse with bookstore info, books to return, and totals.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
            BookStoreNotFoundError: If the seller's bookstore cannot be found.
        """

    @abstractmethod
    def submit_return(self, seller_id: str, notes: Optional[str]) -> ReturnResponse:
        """Submit a return: persist the record, clear inventory, reset seller status.

        Args:
            seller_id: UUID of the seller submitting the return.
            notes: Optional freeform notes about the return.

        Returns:
            ReturnResponse representing the completed return record.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
