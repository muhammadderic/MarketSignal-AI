"""Mock factories for Groq LLM API payloads.

Produces both valid and invalid payloads (per AC-004) for relevance scoring
and financial insight extraction. These are plain dicts matching the JSON
shapes the backend is expected to parse; no Groq SDK calls are made.
"""

from __future__ import annotations

from typing import Any


def mock_groq_scoring_response(
    *,
    score: int = 4,
    reasoning: str = "Reports quarterly earnings with specific revenue and margin figures.",
) -> dict[str, Any]:
    """Return a Groq relevance-scoring payload envelope (valid by construction)."""
    return {
        "id": "chatcmpl-mock",
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        "{\"relevance_score\": " + str(score)
                        + ", \"relevance_reasoning\": \"" + reasoning + "\"}"
                    ),
                },
                "finish_reason": "stop",
            }
        ],
    }


def mock_groq_scoring_response_invalid_score_low() -> dict[str, Any]:
    """Score below 1 (invalid per BR-005)."""
    return mock_groq_scoring_response(score=0)


def mock_groq_scoring_response_invalid_score_high() -> dict[str, Any]:
    """Score above 5 (invalid per BR-005)."""
    return mock_groq_scoring_response(score=6)


def mock_groq_scoring_response_invalid_reasoning_too_long() -> dict[str, Any]:
    """Reasoning exceeding the 50-word limit (invalid per BR-006)."""
    long_reasoning = " ".join(["word"] * 51)
    return mock_groq_scoring_response(reasoning=long_reasoning)


def mock_groq_scoring_response_malformed_json() -> dict[str, Any]:
    """Envelope whose ``content`` is not valid JSON."""
    return {
        "id": "chatcmpl-mock",
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "not-json{"},
                "finish_reason": "stop",
            }
        ],
    }


def mock_groq_insight_response(
    *,
    insight: str = "Revenue rose 12% YoY driven by cloud segment growth.",
) -> dict[str, Any]:
    """Return a Groq financial-insight payload envelope."""
    return {
        "id": "chatcmpl-mock",
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": insight},
                "finish_reason": "stop",
            }
        ],
    }


def mock_groq_rate_limit_error() -> dict[str, Any]:
    """Body shape resembling Groq's 429 response."""
    return {
        "error": {
            "message": "Rate limit reached for requests",
            "type": "rate_limit_error",
            "code": "rate_limit_exceeded",
        }
    }