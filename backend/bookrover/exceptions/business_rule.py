"""Business rule violation exceptions for BookRover.

Raised by services when an operation violates a domain business rule.
Routers catch these and return a 400 or 409 response depending on context.
"""


class BookRoverBusinessRuleError(Exception):
    """Base class for all BookRover business rule exceptions."""


class InsufficientStockError(BookRoverBusinessRuleError):
    """Raised when a requested sale quantity exceeds the book's current_count."""

    def __init__(self, book_id: str, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient stock for book '{book_id}': requested {requested}, available {available}."
        )
        self.book_id = book_id
        self.requested = requested
        self.available = available




class GroupLeaderSwitchNotAllowedError(BookRoverBusinessRuleError):
    """Raised when a seller attempts to switch group leaders without first completing a return."""

    def __init__(self, seller_id: str) -> None:
        super().__init__(
            f"Seller '{seller_id}' must complete their pending return before switching group leaders."
        )
        self.seller_id = seller_id

