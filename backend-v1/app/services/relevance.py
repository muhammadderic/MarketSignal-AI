"""Batch title relevance scoring service backed by the Groq LLM API.

Implements FEAT-004:
- Sub-batching of at most 20 titles per Groq prompt (INTEGRATIONS.md).
- ``asyncio.Semaphore(3)`` cap around Groq inference calls (OQ-008).
- 30 s timeout, max 3 retries with 1 s / 2 s / 4 s backoff on HTTP 429/503.
- Per-item fault isolation and score preservation on re-scoring failure
  (ARC-006, BR-014, BR-015).
- Forward-only ``workflow_state`` transitions to ``Relevance Scored``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.groq_client import get_groq_client
from app.core.config import settings
from app.core.error_handlers import ServiceUnavailableError
from app.db.models import Article
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.relevance import (
    ArticleBatchScoreResponse,
    ScoreItemResult,
)

logger = logging.getLogger(__name__)

_SUB_BATCH_SIZE = 20
_MAX_REASONING_WORDS = 50
_CONCURRENCY_LIMIT = 3
_RETRYABLE_STATUS = {429, 503}
_BACKOFF_DELAYS = (1.0, 2.0, 4.0)

_SYSTEM_PROMPT = (
    "You are a financial-news relevance classifier. For each article title, "
    "assign an integer relevance score from 1 to 5 for a financial market "
    "research operator, where 1 = irrelevant and 5 = critical market impact. "
    "Also return a concise reasoning string of at most 50 words. "
    "Respond ONLY with a JSON array of objects with keys "
    '"article_id" (int), "score" (int), "reasoning" (string). '
    "Do not include markdown fences or prose outside the JSON array."
)


class RelevanceScoringService:
    """Orchestrates Groq-backed batch title scoring with fault isolation."""

    def __init__(self, article_repo: ArticleRepository) -> None:
        self.article_repo = article_repo
        self._semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)

    async def score_article_batch(
        self,
        db: AsyncSession,
        article_ids: list[int],
    ) -> ArticleBatchScoreResponse:
        """Score a batch of articles and persist successful results.

        Args:
            db: Active async session.
            article_ids: Requested article IDs (deduplicated inside).

        Returns:
            Aggregated :class:`ArticleBatchScoreResponse`.

        Raises:
            ServiceUnavailableError: If the Groq client is not configured.
        """
        unique_ids = list(dict.fromkeys(article_ids))
        articles = await self.article_repo.get_by_ids(db, unique_ids)
        articles_by_id = {a.id: a for a in articles}

        results: list[ScoreItemResult] = []
        scoreable: list[Article] = []

        for article_id in unique_ids:
            article = articles_by_id.get(article_id)
            if article is None:
                results.append(
                    ScoreItemResult(
                        article_id=article_id,
                        status="FAILED",
                        error=f"Article ID {article_id} not found.",
                    )
                )
            else:
                scoreable.append(article)

        if not scoreable:
            return self._aggregate(results)

        # --- Sub-batch and dispatch ---
        try:
            client = get_groq_client()
        except ServiceUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to obtain Groq client")
            raise ServiceUnavailableError(
                "Groq client unavailable.",
                context={"component": "relevance_service"},
            ) from exc

        sub_batches = [
            scoreable[i : i + _SUB_BATCH_SIZE]
            for i in range(0, len(scoreable), _SUB_BATCH_SIZE)
        ]

        gathered = await asyncio.gather(
            *(
                self._score_sub_batch(client, batch)
                for batch in sub_batches
            ),
            return_exceptions=True,
        )

        for batch, outcome in zip(sub_batches, gathered):
            if isinstance(outcome, Exception):
                logger.error(
                    "Sub-batch scoring failed",
                    extra={"context": {"error": str(outcome)}},
                )
                for article in batch:
                    results.append(
                        ScoreItemResult(
                            article_id=article.id,
                            status="FAILED",
                            error=f"Groq API error: {outcome}",
                        )
                    )
            else:
                results.extend(outcome)

        # --- Persist successes ---
        persisted_updates: list[dict[str, Any]] = [
            {
                "id": item.article_id,
                "relevance_score": item.relevance_score,
                "relevance_reasoning": item.relevance_reasoning,
            }
            for item in results
            if item.status == "SUCCESS" and item.relevance_score is not None
        ]
        if persisted_updates:
            try:
                await self.article_repo.update_relevance_scores(
                    db, persisted_updates
                )
            except Exception as exc:
                logger.exception("Failed to persist relevance scores")
                raise ServiceUnavailableError(
                    "Failed to persist relevance scores.",
                    context={"component": "relevance_service"},
                ) from exc

        return self._aggregate(results)

    # ---------------
    # --- HELPERS ---
    # ---------------

    async def _score_sub_batch(
        self,
        client: AsyncGroq,
        articles: list[Article],
    ) -> list[ScoreItemResult]:
        """Score one sub-batch of <=20 articles as a single Groq call."""
        titles = [
            {"article_id": article.id, "title": article.title}
            for article in articles
        ]
        user_prompt = (
            "Classify the following financial news titles. "
            "Return the JSON array only.\n"
            f"Titles: {json.dumps(titles, ensure_ascii=False)}"
        )

        async with self._semaphore:
            raw_content = await self._call_with_retries(
                client, user_prompt
            )

        parsed = self._parse_response(raw_content, articles)
        return parsed

    async def _call_with_retries(
        self,
        client: AsyncGroq,
        user_prompt: str,
    ) -> str:
        """Invoke Groq chat completions with retries on 429/503."""
        attempts = settings.GROQ_MAX_RETRIES
        last_exc: Exception | None = None

        for attempt in range(attempts + 1):
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.GROQ_MODEL_TITLE_SCORING,
                        messages=[
                            {"role": "system", "content": _SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"},
                    ),
                    timeout=settings.GROQ_TIMEOUT_SECONDS,
                )
                content = response.choices[0].message.content or ""
                return content
            except asyncio.TimeoutError as exc:
                last_exc = exc
                if attempt >= attempts:
                    raise RuntimeError(
                        f"Groq API timed out after "
                        f"{settings.GROQ_TIMEOUT_SECONDS}s."
                    ) from exc
            except Exception as exc:  # noqa: BLE001
                status = getattr(exc, "status_code", None)
                if status not in _RETRYABLE_STATUS or attempt >= attempts:
                    raise
                delay = _BACKOFF_DELAYS[
                    min(attempt, len(_BACKOFF_DELAYS) - 1)
                ]
                logger.warning(
                    "Groq API retryable failure; retrying in %.1fs",
                    delay,
                    extra={
                        "context": {
                            "status": status,
                            "attempt": attempt + 1,
                        }
                    },
                )
                await asyncio.sleep(delay)
                last_exc = exc

        # Defensive: loop always returns or raises above.
        raise RuntimeError("Groq API call exhausted retries.") from last_exc

    def _parse_response(
        self,
        raw_content: str,
        articles: list[Article],
    ) -> list[ScoreItemResult]:
        """Parse and validate the LLM JSON payload per item."""
        expected_ids = {a.id for a in articles}
        parsed_items = self._load_json_array(raw_content)
        results: list[ScoreItemResult] = []
        seen: set[int] = set()

        for entry in parsed_items:
            if not isinstance(entry, dict):
                continue
            article_id = entry.get("article_id")
            if not isinstance(article_id, int) or article_id not in expected_ids:
                continue
            seen.add(article_id)
            score = entry.get("score")
            reasoning = entry.get("reasoning")

            if not isinstance(score, int) or isinstance(score, bool) or not (
                1 <= score <= 5
            ):
                results.append(
                    ScoreItemResult(
                        article_id=article_id,
                        status="FAILED",
                        error=f"Invalid relevance score: {score!r}",
                    )
                )
                continue

            if not isinstance(reasoning, str) or not reasoning.strip():
                results.append(
                    ScoreItemResult(
                        article_id=article_id,
                        status="FAILED",
                        error="Missing relevance reasoning.",
                    )
                )
                continue

            reasoning_clean = self._truncate_words(
                reasoning.strip(), _MAX_REASONING_WORDS
            )
            results.append(
                ScoreItemResult(
                    article_id=article_id,
                    status="SUCCESS",
                    relevance_score=score,
                    relevance_reasoning=reasoning_clean,
                )
            )

        # Any expected article missing from the model output → FAILED item.
        for article in articles:
            if article.id not in seen:
                results.append(
                    ScoreItemResult(
                        article_id=article.id,
                        status="FAILED",
                        error="Model response omitted this article.",
                    )
                )

        return results

    @staticmethod
    def _load_json_array(raw_content: str) -> list[Any]:
        """Load a JSON array, tolerating a ``{"items": [...]}`` wrapper."""
        text = raw_content.strip()
        # Strip accidental markdown fences.
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
        if fence:
            text = fence.group(1)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("results", "items", "data", "scores"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []

    @staticmethod
    def _truncate_words(text: str, limit: int) -> str:
        """Truncate ``text`` to at most ``limit`` whitespace-separated words."""
        words = text.split()
        if len(words) <= limit:
            return text
        return " ".join(words[:limit])

    @staticmethod
    def _aggregate(
        results: list[ScoreItemResult],
    ) -> ArticleBatchScoreResponse:
        """Build the response envelope from per-item results."""
        success = sum(1 for r in results if r.status == "SUCCESS")
        failed = sum(1 for r in results if r.status == "FAILED")
        return ArticleBatchScoreResponse(
            processed_count=len(results),
            success_count=success,
            failed_count=failed,
            results=results,
        )