"""Business rule violation exceptions for BookRover.

Raised by services when an operation violates a domain business rule.
Routers catch these and return a 400 or 409 response depending on context.
"""


class BookRoverBusinessRuleError(Exception):
    """Base class for all BookRover business rule exceptions."""


class InsufficientStockError(BookRoverBusinessRuleError):
    """Raised when a requested sale quantity exceeds the book's current_count."""


class SellerPendingReturnError(BookRoverBusinessRuleError):
    """Raised when a seller with status 'pending_return' attempts to create a new sale."""


class GroupLeaderSwitchNotAllowedError(BookRoverBusinessRuleError):
    """Raised when a seller attempts to switch group leaders without first completing a return."""
