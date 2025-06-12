from cachetools import TTLCache

from app.modules.news_archieve.constants import (
    ARCHIVE_COUNTS_CACHE_MAXSIZE,
    ARCHIVE_COUNTS_CACHE_TTL_SECONDS,
)

# Keyed by (month, locale)
archive_counts_cache: TTLCache = TTLCache(
    maxsize=ARCHIVE_COUNTS_CACHE_MAXSIZE,
    ttl=ARCHIVE_COUNTS_CACHE_TTL_SECONDS,
)