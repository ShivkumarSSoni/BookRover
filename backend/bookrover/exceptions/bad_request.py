"""Bad-request domain exceptions for BookRover.

Raised by services when an operation cannot proceed due to invalid
business state (e.g. insufficient inventory). Routers catch these
and return a 400 response.
"""


class BookRoverBadRequestError(Exception):
    """Base class for all BookRover bad-request exceptions."""


class InsufficientInventoryError(BookRoverBadRequestError):
    """Raised when a sale requests more copies of a book than are available."""

    def __init__(self, book_id: str, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient inventory for book '{book_id}': "
            f"requested {requested}, available {available}."
        )
        self.book_id = book_id
        self.requested = requested
        self.available = available
