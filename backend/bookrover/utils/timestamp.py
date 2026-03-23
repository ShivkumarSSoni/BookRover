"""UTC timestamp utility for BookRover.

All timestamps stored in DynamoDB use ISO 8601 UTC format with a Z suffix,
as specified in the data models: '2026-03-21T10:30:00Z'.
"""

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with Z suffix.

    Returns:
        Timestamp string in the format 'YYYY-MM-DDTHH:MM:SSZ'.
        Example: '2026-03-21T10:30:00Z'
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

