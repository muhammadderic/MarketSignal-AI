from enum import Enum


MONTH_QUERY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

# Cache
ARCHIVE_COUNTS_CACHE_MAXSIZE = 256
ARCHIVE_COUNTS_CACHE_TTL_SECONDS = 300  # 5 minutes

# === News ===
# Freshness
ARCHIVE_FRESHNESS_THRESHOLD_HOURS = 5

# Locale
class ArticleLocale(str, Enum):
    ID = "ID"
    US = "US"
    GLOBAL = "GLOBAL"        # For international/cross-border market news
    UNASSIGNED = "UNASSIGNED"# For scraped news that hasn't passed locale validation