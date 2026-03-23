"""Exception raised when an email verification code is invalid or expired."""


class InvalidVerificationCodeError(Exception):
    """Raised by the router when a submitted verification code does not match
    the stored code, or when the stored code has passed its 10-minute TTL."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid or expired verification code for {email}.")
        self.email = email
