from enum import Enum


SQLITE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ArticleLocale(str, Enum):
    ID = "ID"
    US = "US"
    GLOBAL = "GLOBAL"        # For international/cross-border market news
    UNASSIGNED = "UNASSIGNED"# For scraped news that hasn't passed locale validation