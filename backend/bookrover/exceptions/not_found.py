"""Not-found domain exceptions for BookRover.

Raised by repositories when a requested resource does not exist in DynamoDB.
Routers catch these and return a 404 response.
"""


class BookRoverNotFoundError(Exception):
    """Base class for all BookRover not-found exceptions."""


class BookStoreNotFoundError(BookRoverNotFoundError):
    """Raised when a bookstore cannot be found by its ID."""


class GroupLeaderNotFoundError(BookRoverNotFoundError):
    """Raised when a group leader cannot be found by its ID."""


class SellerNotFoundError(BookRoverNotFoundError):
    """Raised when a seller cannot be found by their ID."""


class BookNotFoundError(BookRoverNotFoundError):
    """Raised when an inventory book cannot be found by its ID."""


class SaleNotFoundError(BookRoverNotFoundError):
    """Raised when a sale record cannot be found by its ID."""


class ReturnNotFoundError(BookRoverNotFoundError):
    """Raised when a return record cannot be found by its ID."""
