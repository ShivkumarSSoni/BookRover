"""Pydantic DTOs for the email verification flow.

Used by the seller registration pre-flight step:
  POST /sellers/request-verification  →  issues a 6-digit code
  POST /sellers                        →  consumes the code via SellerCreate.verification_code
"""

from pydantic import BaseModel, EmailStr


class VerificationRequest(BaseModel):
    """Request body for POST /sellers/request-verification."""

    email: EmailStr


class VerificationResponse(BaseModel):
    """Response for POST /sellers/request-verification.

    Attributes:
        message: Human-readable confirmation.
        code: The 6-digit code — only populated in dev/test mode.
                  Never returned in production (code is sent via email instead).
    """

    message: str
    code: str | None = None
