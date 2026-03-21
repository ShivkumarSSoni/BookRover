"""Pydantic DTOs for the BookStore entity.

Contains request and response models used by the Admin router
for BookStore create, update, and read operations.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BookStoreCreate(BaseModel):
    """Request body for creating a new BookStore."""

    store_name: str = Field(..., min_length=1, max_length=100, description="Name of the bookstore")
    owner_name: str = Field(..., min_length=1, max_length=100, description="Name of the bookstore owner")
    address: str = Field(..., min_length=1, max_length=500, description="Full street address")
    phone_number: str = Field(..., min_length=1, max_length=20, description="Contact phone number")


class BookStoreUpdate(BaseModel):
    """Request body for updating an existing BookStore.

    All fields are optional — only supplied fields are updated.
    """

    store_name: Optional[str] = Field(None, min_length=1, max_length=100)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    phone_number: Optional[str] = Field(None, min_length=1, max_length=20)


class BookStoreResponse(BaseModel):
    """Response model for a BookStore — returned by all read and write operations."""

    bookstore_id: str
    store_name: str
    owner_name: str
    address: str
    phone_number: str
    created_at: str
    updated_at: str
