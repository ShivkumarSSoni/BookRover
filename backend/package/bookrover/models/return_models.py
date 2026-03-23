"""Pydantic DTOs for the Return feature.

Covers:
  - ReturnSummaryBookstoreInfo: bookstore details shown on the return page.
  - ReturnSummaryBook: one row in the "books to return" table.
  - ReturnSummaryResponse: full payload for GET /sellers/{id}/return-summary.
  - ReturnCreate: request body for POST /sellers/{id}/returns.
  - ReturnItemResponse: one item within a submitted return record.
  - ReturnResponse: full payload for POST /sellers/{id}/returns 201 response.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ReturnSummaryBookstoreInfo(BaseModel):
    """Bookstore details embedded in the return summary response."""

    bookstore_id: str
    store_name: str
    owner_name: str
    address: str
    phone_number: str


class ReturnSummaryBook(BaseModel):
    """One book row in the return summary — shows what to carry back."""

    book_id: str
    book_name: str
    language: str
    quantity_to_return: int
    cost_per_book: float
    total_cost: float


class ReturnSummaryResponse(BaseModel):
    """Response model for GET /sellers/{seller_id}/return-summary.

    Contains the bookstore to return to, all books still in hand,
    and the total money collected from sales that must be handed over.
    """

    seller_id: str
    bookstore: ReturnSummaryBookstoreInfo
    books_to_return: List[ReturnSummaryBook]
    total_books_to_return: int
    total_cost_of_unsold_books: float
    total_money_collected_from_sales: float


class ReturnCreate(BaseModel):
    """Request body for POST /sellers/{seller_id}/returns."""

    notes: Optional[str] = Field(default=None, max_length=500)


class ReturnItemResponse(BaseModel):
    """One returned book embedded inside a ReturnResponse."""

    book_id: str
    book_name: str
    language: str
    quantity_returned: int
    cost_per_book: float
    total_cost: float


class ReturnResponse(BaseModel):
    """Response model for POST /sellers/{seller_id}/returns.

    Represents the completed return record persisted in DynamoDB.
    """

    return_id: str
    seller_id: str
    bookstore_id: str
    return_items: List[ReturnItemResponse]
    total_books_returned: int
    total_money_returned: float
    status: str
    return_date: str
