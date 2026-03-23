"""Conflict domain exceptions for BookRover.

Raised by repositories or services when an operation would create a duplicate
or violate a referential integrity rule. Routers catch these and return 409.
"""


class BookRoverConflictError(Exception):
    """Base class for all BookRover conflict exceptions."""


class DuplicateEmailError(BookRoverConflictError):
    """Raised when an email address is already registered in the system."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email '{email}' is already registered.")
        self.email = email


class ActiveSellersExistError(BookRoverConflictError):
    """Raised when attempting to delete a group leader who has active sellers assigned."""

    def __init__(self, group_leader_id: str, seller_count: int) -> None:
        super().__init__(
            f"Cannot delete group leader '{group_leader_id}': "
            f"{seller_count} active seller(s) are still assigned."
        )
        self.group_leader_id = group_leader_id
        self.seller_count = seller_count


class InventoryAssociatedError(BookRoverConflictError):
    """Raised when attempting to delete a bookstore that has associated inventory or pending returns."""

    def __init__(self, bookstore_id: str) -> None:
        super().__init__(
            f"Cannot delete bookstore '{bookstore_id}': it has associated inventory or pending returns."
        )
        self.bookstore_id = bookstore_id


class BookPartiallySoldError(BookRoverConflictError):
    """Raised when attempting to delete an inventory book that has been partially sold
    (i.e., current_count < initial_count)."""

    def __init__(self, book_id: str) -> None:
        super().__init__(
            f"Cannot delete book '{book_id}': it has been partially sold and cannot be removed."
        )
        self.book_id = book_id


class SellerPendingReturnError(BookRoverConflictError):
    """Raised when a seller's status is 'pending_return' and cannot record new sales."""

    def __init__(self, seller_id: str) -> None:
        super().__init__(
            f"Seller '{seller_id}' is pending return and cannot record new sales."
        )
        self.seller_id = seller_id

