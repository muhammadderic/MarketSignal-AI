from datetime import date

from app.modules.news_scoring.ns_utils import validate_batch_size
from app.modules.news_scoring.ns_service import NewsScoringService

from app.modules.news_archieve.constants import ArticleLocale
from app.modules.news_archieve.schemas import DailyNewsResponse
from app.modules.news_archieve.utils import sanitize_article_titles
from app.modules.news_archieve.services import NewsArchieveService


class NewsScoringOrchestrator:
    def __init__(
        self,
        news: NewsArchieveService,
        news_scoring: NewsScoringService
    ):
        self.news = news
        self.news_scoring = news_scoring

    async def sync_and_get_news_scores(
        self, 
        article_ids: list[int],
        published_date: date,
        locale: ArticleLocale = ArticleLocale.ID,
    ) -> DailyNewsResponse:
        """
        Score a batch of articles, persist the results, and return the
        refreshed daily news payload for the given date and locale.

        Args:
            article_ids: Article IDs to score (10-20 unique).
            published_date: The UTC calendar date whose news should be
                returned after scoring.
            locale: Target locale for the returned news. Defaults to
                ArticleLocale.ID.

        Returns:
            A DailyNewsResponse containing all articles for the given
            date and locale, with the freshly persisted scores.
        """
        # 1. Check total data retrieved
        validate_batch_size(article_ids)

        # 2. Get all news titles from database
        news_titles_and_id = self.news.get_titles_by_ids(article_ids)

        # 3. Sanitize titles by removing source suffix
        news_titles_and_id = sanitize_article_titles(news_titles_and_id)

        # 4. Scoring titles
        scoring_response = await self.news_scoring.score_titles(news_titles_and_id)

        # 5. Persist scores back onto the existing news rows
        self.news.update_news_scores(scoring_response)

        # 6. Return the refreshed daily payload for the requested date
        return self.news.get_news_by_published_date(
            published_date=published_date,
            locale=locale,
        )
