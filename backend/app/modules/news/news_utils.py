from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from urllib.parse import parse_qs, urlparse

from app.modules.news.news_schemas import ArticleTitleData
from app.modules.news.news_constants import SQLITE_FORMAT, ArticleLocale


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


def is_data_fresh(
    last_published_at: datetime | None,
    max_age_hours: int
) -> bool:
    """
    Determine if stored data is still fresh based on an age threshold.
    
    Args:
        last_published_at: The timestamp of the most recent stored record.
        max_age_hours: Maximum allowable data age in hours before considered stale.

    Returns:
        bool: True if data exists and is within max_age_hours window, False otherwise.
    """
    if last_published_at is None:
        return False
    
    # Establish naive UTC timestamp for comparison
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(hours=max_age_hours)
    
    # Data is fresh if the newest record is STRICTLY AFTER the age cutoff
    return last_published_at > cutoff


def get_max_age_cutoff(max_age_day: int = 1) -> datetime:
    """
    Calculate the cutoff datetime N days before now (exclusive boundary).
    
    Args:
        max_age_day: Number of days to look back. Defaults to 1.
        
    Returns:
        Naive UTC datetime representing the oldest acceptable timestamp.
        Example: now = "2026-08-27 10:00:00", max_age_day = 1 
                 → returns "2026-08-26 09:59:59"
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now - timedelta(days=max_age_day) - timedelta(seconds=1)


def validate_locale(locale: str) -> ArticleLocale | None:
    """
    Validates if the provided locale string matches an allowed ArticleLocale variant.
    
    Args:
        locale: The raw locale string input (e.g., "ID", "US", "invalid").
        
    Returns:
        ArticleLocale: The validated Enum member if allowed.
        None: If the locale is invalid or unsupported.
    """
    try:
        # Convert raw string to Enum (case-insensitive conversion)
        return ArticleLocale[locale.upper()]
    except KeyError:
        return None


def sanitize_article_titles(
    articles: list[ArticleTitleData]
) -> list[ArticleTitleData]:
    """
    Strip trailing source attribution from article titles.
    
    Google News RSS titles are formatted as "<Headline> - <Source>".
    This removes the " - <Source>" suffix so downstream LLM scoring
    focuses on the headline only.
    
    Args:
        articles: List of ArticleTitleData with source-suffixed titles.
        
    Returns:
        New list of ArticleTitleData with sanitized titles.
    """
    sanitized = []
    for article in articles:
        # Split on the last " - " separator; keep only the headline part
        title = article.title
        if " - " in title:
            title = title.rsplit(" - ", 1)[0].strip()
        
        sanitized.append(
            ArticleTitleData(id=article.id, title=title)
        )
    
    return sanitized
