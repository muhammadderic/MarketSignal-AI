from fastapi import HTTPException, status
from typing import Sequence

from app.modules.news_scoring.constants import NEWS_SCORING_MIN_TITLE_PAIRS, NEWS_SCORING_MAX_TITLE_PAIRS
from app.modules.news.news_schemas import ArticleTitleData


def validate_batch_size(
    payload: list,
    min_size: int = 10,
    max_size: int = 20,
) -> bool:
    """
    Validate that a batch payload's list size is within the allowed range.
    
    Args:
        payload: List to validate.
        min_size: Minimum acceptable length (inclusive).
        max_size: Maximum acceptable length (inclusive).
        
    Returns:
        True if payload size is valid.
        
    Raises:
        HTTPException: 400 if payload size is outside the allowed range.
    """
    size = len(payload)
    if size < min_size or size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid size: received {size} items. "
                f"Expected between {min_size} and {max_size}."
            )
        )
    return True


def validate_title_pairs_count(
    pairs: Sequence[ArticleTitleData],
    min_count: int = NEWS_SCORING_MIN_TITLE_PAIRS,
    max_count: int = NEWS_SCORING_MAX_TITLE_PAIRS,
) -> bool:
    """
    Validate that the number of (id, title) pairs falls within an
    inclusive [min_count, max_count] range.

    This utility is intentionally generic: it accepts any Sequence of
    ArticleTitleData and configurable bounds, both defaulting to the
    application-wide constants. Callers (including tests) can override
    either bound per use-case.

    Args:
        pairs: Sequence of ArticleTitleData to validate.
        min_count: Minimum required number of pairs (inclusive).
            Defaults to NEWS_SCORING_MIN_TITLE_PAIRS.
        max_count: Maximum allowed number of pairs (inclusive).
            Defaults to NEWS_SCORING_MAX_TITLE_PAIRS.

    Returns:
        True if min_count <= len(pairs) <= max_count, False otherwise.

    Raises:
        ValueError: If min_count > max_count (misconfiguration guard).
    """
    if min_count > max_count:
        raise ValueError(
            f"Invalid bounds: min_count ({min_count}) must not exceed "
            f"max_count ({max_count})."
        )

    return min_count <= len(pairs) <= max_count
