from datetime import UTC, datetime


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert a datetime object to a Unix timestamp (milliseconds since epoch).

    Args:
        dt: A datetime object, preferably with timezone information.
            If timezone is not provided, UTC is assumed.

    Returns:
        str: Unix timestamp in milliseconds.
    """
    if dt.tzinfo is None:
        # If no timezone is provided, assume UTC
        dt = dt.replace(tzinfo=UTC)

    return int(dt.timestamp() * 1000)
