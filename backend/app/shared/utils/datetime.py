from datetime import datetime, timezone


def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc_aware(value: datetime) -> datetime:
    """
    Ensure a datetime value is UTC-aware.

    Assumes naive datetime values already represent UTC; their timezone
    information is attached without changing the clock time. Timezone-aware
    values are converted to UTC.

    Usage: utc_datetime = to_utc_aware(value)
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)