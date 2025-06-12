import re
from datetime import datetime, timezone

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse_month(month: str) -> tuple[datetime, datetime]:
    """
    Parse a `YYYY-MM` string into a UTC-aware [start, end) datetime range.

    Returns (first_day_of_month, first_day_of_next_month) in UTC.
    Raises ValueError if the input is malformed or impossible.
    """
    if not isinstance(month, str) or not _MONTH_PATTERN.match(month):
        raise ValueError(f"Invalid month format: {month!r}. Expected YYYY-MM.")

    year, mon = int(month[:4]), int(month[5:7])

    try:
        start = datetime(year, mon, 1, tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Impossible month: {month!r}") from exc

    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)

    return start, end