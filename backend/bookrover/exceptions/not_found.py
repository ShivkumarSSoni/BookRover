"""Not-found domain exceptions for BookRover.

Raised by repositories when a requested resource does not exist in DynamoDB.
Routers catch these and return a 404 response.
"""


class BookRoverNotFoundError(Exception):
    """Base class for all BookRover not-found exceptions."""


class BookStoreNotFoundError(BookRoverNotFoundError):
    """Raised when a bookstore cannot be found by its ID."""

    def __init__(self, bookstore_id: str) -> None:
        super().__init__(f"Bookstore '{bookstore_id}' not found.")
        self.bookstore_id = bookstore_id


class GroupLeaderNotFoundError(BookRoverNotFoundError):
    """Raised when a group leader cannot be found by its ID."""

    def __init__(self, group_leader_id: str) -> None:
        super().__init__(f"Group leader '{group_leader_id}' not found.")
        self.group_leader_id = group_leader_id


class SellerNotFoundError(BookRoverNotFoundError):
    """Raised when a seller cannot be found by their ID."""

    def __init__(self, seller_id: str) -> None:
        super().__init__(f"Seller '{seller_id}' not found.")
        self.seller_id = seller_id


class BookNotFoundError(BookRoverNotFoundError):
    """Raised when an inventory book cannot be found by its ID."""

    def __init__(self, book_id: str) -> None:
        super().__init__(f"Book '{book_id}' not found.")
        self.book_id = book_id


class SaleNotFoundError(BookRoverNotFoundError):
    """Raised when a sale record cannot be found by its ID."""

    def __init__(self, sale_id: str) -> None:
        super().__init__(f"Sale '{sale_id}' not found.")
        self.sale_id = sale_id


class ReturnNotFoundError(BookRoverNotFoundError):
    """Raised when a return record cannot be found by its ID."""

    def __init__(self, return_id: str) -> None:
        super().__init__(f"Return '{return_id}' not found.")
        self.return_id = return_id

