from datetime import date
from fastapi import HTTPException, status

from app.modules.news_scoring.ns_schemas import BatchScoringResponse
from app.modules.news_scoring.ns_utils import validate_batch_size, validate_title_pairs_count
from app.modules.news_scoring.ns_service import NewsScoringService
from app.modules.news_scoring.constants import NEWS_SCORING_MIN_TITLE_PAIRS, NEWS_SCORING_MAX_TITLE_PAIRS
from app.modules.news.news_services import NewsService
from app.modules.news.news_utils import sanitize_article_titles


class NewsScoringOrchestrator:
    def __init__(
        self,
        news: NewsService,
        news_scoring: NewsScoringService
    ):
        self.news = news
        self.news_scoring = news_scoring

    def sync_and_get_news_scores(
        self, 
        article_ids: list[int]
    ) -> BatchScoringResponse:
        # 1. Check total data retrieved (min: 10 and max: 20)
        validate_batch_size(article_ids)

        # 2. Get all news titles from database
        news_titles_and_id = self.news.get_titles_by_ids(article_ids)

        # 3. Sanitize titles by removing source suffix
        news_titles_and_id = sanitize_article_titles(news_titles_and_id)

        # 4. Scoring titles
        scoring_response = self.news_scoring.score_titles(news_titles_and_id)

        return scoring_response

    async def get_titles_for_scoring(
        self,
        date: date | None,
    ) -> BatchScoringResponse:
        """
        Orchestrate the retrieval and validation of article titles
        awaiting LLM scoring for a given published date.

        Args:
            date: The published date to retrieve titles for.

        Returns:
            A list of ArticleTitleData ready for downstream scoring.
        """
        # 1. Validate input date
        validated_date = self._validate_date(date)

        # 2. Get all titles with id based on the published date
        pairs = self.news.get_titles_by_published_date(validated_date)
        if not validate_title_pairs_count(pairs):
            # Distinguish the two failure modes for clearer API semantics.
            if len(pairs) < NEWS_SCORING_MIN_TITLE_PAIRS:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Not enough article titles found for {validated_date} "
                        f"(got {len(pairs)}, need at least "
                        f"{NEWS_SCORING_MIN_TITLE_PAIRS})."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"Too many article titles found for {validated_date} "
                    f"(got {len(pairs)}, max allowed is "
                    f"{NEWS_SCORING_MAX_TITLE_PAIRS}). "
                    "Narrow the date range or raise the batch ceiling."
                ),
            )

        # 3. Sanitize titles by removing source suffix
        pairs = sanitize_article_titles(pairs)

        # 4. Scoring titles
        scoring_response = await self.news_scoring.score_titles(pairs)
        return scoring_response

    def _validate_date(self, date: date | None) -> date:
        """
        Validate the incoming date payload.

        Args:
            date: The raw date value from the payload.

        Returns:
            The validated date.

        Raises:
            HTTPException: 422 if the date is missing or invalid.
        """
        if not date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A valid `date` is required.",
            )
        return date
