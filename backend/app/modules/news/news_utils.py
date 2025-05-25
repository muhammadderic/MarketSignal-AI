from datetime import datetime, timezone
from typing import Optional, Union
from urllib.parse import parse_qs, urlparse

from app.modules.news.news_constants import SQLITE_FORMAT

def parse_input_date(
    val: Optional[Union[str, datetime]], 
    default_val: datetime
) -> datetime:
    """
    Parse input date string/datetime to naive UTC datetime.
    
    Args:
        val: Input value (string, datetime, or None)
        default_val: Default datetime if val is None
        
    Returns:
        Naive UTC datetime
    """
    if val is None:
        return default_val
    if isinstance(val, str):
        return datetime.strptime(val, SQLITE_FORMAT)
    if isinstance(val, datetime) and val.tzinfo is not None:
        return val.astimezone(timezone.utc).replace(tzinfo=None)
    return val


def extract_original_url(google_news_link: str) -> str:
    """
    Extract the original article URL from Google News redirect link.
    """
    parsed = urlparse(google_news_link)
    params = parse_qs(parsed.query)
    return params.get('url', [google_news_link])[0]
    