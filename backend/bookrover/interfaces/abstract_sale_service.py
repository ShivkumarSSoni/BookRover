"""Abstract base class for the Sale service port.

Routers depend on this ABC — never on the concrete SaleService.
This enables unit testing of routers with a mock service (no DynamoDB).
"""

from abc import ABC, abstractmethod
from typing import List

from bookrover.models.sale import SaleCreate, SaleResponse


class AbstractSaleService(ABC):
    """Port definition for all Sale business-logic operations."""

    @abstractmethod
    def create_sale(self, seller_id: str, payload: SaleCreate) -> SaleResponse:
        """Record a new sale and decrement inventory counts.

        Args:
            seller_id: UUID of the seller recording the sale.
            payload: Validated SaleCreate DTO (buyer details + items).

        Returns:
            SaleResponse for the created sale.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
            SellerPendingReturnError: If seller status is 'pending_return'.
            BookNotFoundError: If any book_id in items does not exist.
            InsufficientInventoryError: If quantity_sold exceeds current_count.
        """

    @abstractmethod
    def list_sales(self, seller_id: str) -> List[SaleResponse]:
        """Return all sales for a seller.

        Args:
            seller_id: UUID of the seller.

        Returns:
            List of SaleResponse objects, may be empty.
        """

    @abstractmethod
    def get_sale(self, seller_id: str, sale_id: str) -> SaleResponse:
        """Return a single sale by ID, scoped to the seller.

        Args:
            seller_id: UUID of the seller.
            sale_id: UUID of the sale.

        Returns:
            SaleResponse for the matching sale.

        Raises:
            SaleNotFoundError: If sale is not found or belongs to a different seller.
        """
