from datetime import datetime, timezone


def epoch_to_utc_datetime(epoch_seconds: int | None) -> datetime | None:
    """
    Convert a Unix epoch timestamp (seconds) into a timezone-aware UTC
    datetime suitable for storage in a `DateTime(timezone=True)` column.

    Args:
        epoch_seconds: Unix epoch timestamp in seconds (as returned by
            the external LLM API's `created` field). May be None.

    Returns:
        A UTC-aware `datetime` if `epoch_seconds` is provided, else None.
    """
    if epoch_seconds is None:
        return None
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    