from app.modules.news.news_schemas import ArticleTitleData

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
