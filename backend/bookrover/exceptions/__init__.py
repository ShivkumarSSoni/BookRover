"""Domain exception classes for BookRover.

These are the only things permitted to cross layer boundaries:
  - Repositories raise domain exceptions (never boto3 ClientError).
  - Services may raise additional domain exceptions for business rule violations.
  - Routers catch domain exceptions and translate them to HTTP responses.

Import exceptions from this package directly:
    from bookrover.exceptions import BookNotFoundError, DuplicateEmailError
"""

from bookrover.exceptions.not_found import (
    BookRoverNotFoundError,
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    SellerNotFoundError,
    BookNotFoundError,
    SaleNotFoundError,
    ReturnNotFoundError,
)
from bookrover.exceptions.conflict import (
    BookRoverConflictError,
    DuplicateEmailError,
    ActiveSellersExistError,
    InventoryAssociatedError,
    BookPartiallySoldError,
)
from bookrover.exceptions.business_rule import (
    BookRoverBusinessRuleError,
    InsufficientStockError,
    SellerPendingReturnError,
    GroupLeaderSwitchNotAllowedError,
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
