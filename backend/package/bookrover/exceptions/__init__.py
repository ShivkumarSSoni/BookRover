"""Domain exception classes for BookRover.

These are the only things permitted to cross layer boundaries:
  - Repositories raise domain exceptions (never boto3 ClientError).
  - Services may raise additional domain exceptions for business rule violations.
  - Routers catch domain exceptions and translate them to HTTP responses.

Import exceptions from this package directly:
    from bookrover.exceptions import BookNotFoundError, DuplicateEmailError
"""

from bookrover.exceptions.business_rule import (
    BookRoverBusinessRuleError,
    GroupLeaderSwitchNotAllowedError,
    InsufficientStockError,
    SellerPendingReturnError,
)
from bookrover.exceptions.conflict import (
    ActiveSellersExistError,
    BookPartiallySoldError,
    BookRoverConflictError,
    DuplicateEmailError,
    InventoryAssociatedError,
)
from bookrover.exceptions.not_found import (
    BookNotFoundError,
    BookRoverNotFoundError,
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    ReturnNotFoundError,
    SaleNotFoundError,
    SellerNotFoundError,
)

__all__ = [
    "BookRoverNotFoundError",
    "BookStoreNotFoundError",
    "GroupLeaderNotFoundError",
    "SellerNotFoundError",
    "BookNotFoundError",
    "SaleNotFoundError",
    "ReturnNotFoundError",
    "BookRoverConflictError",
    "DuplicateEmailError",
    "ActiveSellersExistError",
    "InventoryAssociatedError",
    "BookPartiallySoldError",
    "BookRoverBusinessRuleError",
    "InsufficientStockError",
    "SellerPendingReturnError",
    "GroupLeaderSwitchNotAllowedError",
]
