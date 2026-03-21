"""Pydantic DTOs for the BookStore entity.

Contains request and response models used by the Admin router
for BookStore create, update, and read operations.
"""

from typing import Optional

import phonenumbers
from pydantic import BaseModel, Field, field_validator


def _validate_phone(value: str) -> str:
    """Validate that the phone number is a valid international number using libphonenumber.

    Args:
        value: Phone number string, expected in E.164 format (e.g. +914423456789).

    Returns:
        The original value if valid.

    Raises:
        ValueError: If the number is not a valid international phone number.
    """
    try:
        parsed = phonenumbers.parse(value)
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid phone number. Use international format, e.g. +914423456789")
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("Invalid phone number. Use international format, e.g. +914423456789")
    return value


class BookStoreCreate(BaseModel):
    """Request body for creating a new BookStore."""

    store_name: str = Field(..., min_length=1, max_length=100, description="Name of the bookstore")
    owner_name: str = Field(..., min_length=1, max_length=100, description="Name of the bookstore owner")
    address: str = Field(..., min_length=1, max_length=500, description="Full street address")
    phone_number: str = Field(
        ...,
        description="Contact phone number in international format, e.g. +914423456789",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """Validate phone number using libphonenumber."""
        return _validate_phone(value)


class BookStoreUpdate(BaseModel):
    """Request body for updating an existing BookStore.

    All fields are optional — only supplied fields are updated.
    """

    store_name: Optional[str] = Field(None, min_length=1, max_length=100)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    phone_number: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        """Validate phone number using libphonenumber if provided."""
        if value is None:
            return value
        return _validate_phone(value)


class BookStoreResponse(BaseModel):
    """Response model for a BookStore — returned by all read and write operations."""

    bookstore_id: str
    store_name: str
    owner_name: str
    address: str
    phone_number: str
    created_at: str
    updated_at: str
