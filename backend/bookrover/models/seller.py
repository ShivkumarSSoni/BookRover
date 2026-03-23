"""Pydantic DTOs for the Seller entity.

Contains request and response models used by the Seller router
for registration and profile operations.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SellerCreate(BaseModel):
    """Request body for registering a new Seller.

    ``verification_code`` must be obtained first by calling
    ``POST /sellers/request-verification``.  The code is validated and
    consumed atomically during registration — it cannot be reused.
    """

    first_name: str = Field(..., min_length=1, max_length=50, description="Seller's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Seller's last name")
    email: EmailStr = Field(..., description="Gmail address — must be unique across all sellers")
    group_leader_id: str = Field(..., min_length=1, description="UUID of the assigned group leader")
    bookstore_id: str = Field(..., min_length=1, description="UUID of the assigned bookstore")
    verification_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit email verification code issued by POST /sellers/request-verification",
    )


class SellerUpdate(BaseModel):
    """Request body for updating a Seller's name fields.

    Email and group leader assignment are not updatable here.
    """

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)


class SellerResponse(BaseModel):
    """Response model for a Seller — returned by all read and write operations."""

    seller_id: str
    first_name: str
    last_name: str
    email: str
    group_leader_id: str
    bookstore_id: str
    status: str
    created_at: str
    updated_at: str
