"""Pydantic DTOs for the Sale entity.

Contains request and response models used by the Sales router for
creating and retrieving sale records.
"""

from typing import List

from pydantic import BaseModel, Field, model_validator


class SaleItemCreate(BaseModel):
    """A single book item within a sale request."""

    book_id: str = Field(..., min_length=1, max_length=36, description="UUID of the book being sold")
    quantity_sold: int = Field(..., ge=1, le=1000, description="Number of copies sold — maximum 1 000 per line item")


class SaleCreate(BaseModel):
    """Request body for recording a new sale."""

    buyer_first_name: str = Field(..., min_length=1, max_length=50)
    buyer_last_name: str = Field(..., min_length=1, max_length=50)
    buyer_country_code: str = Field(
        ...,
        min_length=2,
        max_length=5,
        pattern=r"^\+\d{1,3}$",
        description="E.164 country dialling prefix — e.g. '+91', '+1', '+44'",
    )
    buyer_phone: str = Field(
        ..., min_length=5, max_length=15, pattern=r"^\d+$",
        description="Buyer phone number — digits only, 5–15 characters",
    )
    items: List[SaleItemCreate] = Field(..., min_length=1, max_length=50, description="At least one book item — maximum 50 line items per sale")

    @model_validator(mode="after")
    def no_duplicate_book_ids(self) -> "SaleCreate":
        ids = [item.book_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("items must not contain duplicate book_id values")
        return self


class SaleItemResponse(BaseModel):
    """A single book item within a sale response.

    book_name, language, and selling_price are snapshots taken at sale time
    so historical records remain accurate even if the book's details change later.
    """

    book_id: str
    book_name: str
    language: str
    quantity_sold: int
    selling_price: float
    subtotal: float


class SaleResponse(BaseModel):
    """Response model for a single sale record."""

    sale_id: str
    seller_id: str
    bookstore_id: str
    buyer_first_name: str
    buyer_last_name: str
    buyer_country_code: str
    buyer_phone: str
    sale_items: List[SaleItemResponse]
    total_books_sold: int
    total_amount_collected: float
    sale_date: str
    created_at: str
