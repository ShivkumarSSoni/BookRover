"""Conflict domain exceptions for BookRover.

Raised by repositories or services when an operation would create a duplicate
or violate a referential integrity rule. Routers catch these and return 409.
"""


class BookRoverConflictError(Exception):
    """Base class for all BookRover conflict exceptions."""


class DuplicateEmailError(BookRoverConflictError):
    """Raised when an email address is already registered in the system."""


class ActiveSellersExistError(BookRoverConflictError):
    """Raised when attempting to delete a group leader who has active sellers assigned."""


class InventoryAssociatedError(BookRoverConflictError):
    """Raised when attempting to delete a bookstore that has associated inventory or pending returns."""


class BookPartiallySoldError(BookRoverConflictError):
    """Raised when attempting to delete an inventory book that has been partially sold
    (i.e., current_count < initial_count)."""
