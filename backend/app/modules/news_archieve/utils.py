import re
from datetime import datetime, timezone, date, time

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


def build_utc_day_bounds(
    published_date: date,
) -> tuple[datetime, datetime]:
    """
    Build a half-open UTC datetime range covering a full calendar day.

    Args:
        published_date: The UTC calendar date to bound.

    Returns:
        A tuple (start, end) where:
            - start = published_date at 00:00:00 UTC (inclusive)
            - end   = published_date at 23:59:59 UTC (inclusive)
    """
    start = datetime.combine(published_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(published_date, time.max, tzinfo=timezone.utc)
    return start, end
