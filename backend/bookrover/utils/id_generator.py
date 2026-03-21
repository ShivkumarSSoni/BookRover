"""UUID-based unique ID generator for BookRover entities."""

import uuid


def generate_id() -> str:
    """Generate a new UUID v4 string suitable for use as a DynamoDB primary key.

    Returns:
        Lowercase hyphenated UUID v4 string, e.g. '550e8400-e29b-41d4-a716-446655440000'.
    """
    return str(uuid.uuid4())
