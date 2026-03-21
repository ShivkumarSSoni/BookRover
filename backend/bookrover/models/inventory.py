"""Pydantic DTOs for the Inventory (Book) entity.

Contains request and response models used by the Inventory router
for add, list, update, and remove book operations.
"""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class BookCreate(BaseModel):
    """Request body for adding a new book to a seller's inventory."""

    book_name: str = Field(..., min_length=1, max_length=200, description="Title of the book")
    language: str = Field(..., min_length=1, max_length=50, description="Language of the book")
    initial_count: int = Field(..., ge=1, description="Number of books collected from bookstore")
    cost_per_book: Decimal = Field(..., gt=Decimal("0"), description="Cost price per book in ₹")
    selling_price: Decimal = Field(
        ..., gt=Decimal("0"), description="Selling price per book in ₹ — must exceed cost"
    )

    @model_validator(mode="after")
    def validate_selling_price_above_cost(self) -> "BookCreate":
        """Ensure selling_price is strictly greater than cost_per_book."""
        if self.selling_price <= self.cost_per_book:
            raise ValueError("selling_price must be greater than cost_per_book")
        return self


class BookUpdate(BaseModel):
    """Request body for updating a book in inventory.

    Only book_name, language, cost_per_book, and selling_price are updatable.
    current_count is managed exclusively by sales. initial_count is immutable.
    """

    book_name: Optional[str] = Field(None, min_length=1, max_length=200)
    language: Optional[str] = Field(None, min_length=1, max_length=50)
    cost_per_book: Optional[Decimal] = Field(None, gt=Decimal("0"))
    selling_price: Optional[Decimal] = Field(None, gt=Decimal("0"))


class BookResponse(BaseModel):
    """Response model for a single inventory book with computed balance fields."""

    book_id: str
    seller_id: str
    bookstore_id: str
    book_name: str
    language: str
    initial_count: int
    current_count: int
    cost_per_book: float
    selling_price: float
    current_books_cost_balance: float
    total_books_cost_balance: float
    created_at: str
    updated_at: str


class InventorySummary(BaseModel):
    """Aggregate summary of a seller's entire inventory."""

    total_books_in_hand: int
    total_cost_balance: float
    total_initial_cost: float


class InventoryListResponse(BaseModel):
    """Full inventory response for a seller — books list plus aggregate summary."""

    seller_id: str
    bookstore_id: str
    books: List[BookResponse]
    summary: InventorySummary
