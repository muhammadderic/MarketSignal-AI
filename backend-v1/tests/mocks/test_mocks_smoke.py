"""Smoke tests proving the mock factories emit usable payloads (AC-004)."""

from __future__ import annotations

import feedparser

from tests.mocks.groq_mocks import (
    mock_groq_scoring_response,
    mock_groq_scoring_response_invalid_reasoning_too_long,
    mock_groq_scoring_response_invalid_score_high,
    mock_groq_scoring_response_invalid_score_low,
)
from tests.mocks.publisher_mocks import mock_publisher_html, mock_publisher_html_paywall
from tests.mocks.rss_mocks import mock_rss_feed_malformed_xml, mock_rss_feed_xml


def test_rss_mock_parses_with_feedparser() -> None:
    parsed = feedparser.parse(mock_rss_feed_xml())
    assert parsed.bozo is False
    assert len(parsed.entries) == 1
    assert parsed.entries[0].title.startswith("Acme Corp")


def test_rss_mock_malformed_is_not_parsed_cleanly() -> None:
    parsed = feedparser.parse(mock_rss_feed_malformed_xml())
    assert parsed.bozo
    assert parsed.bozo_exception is not None


def test_groq_scoring_mocks_cover_valid_and_invalid() -> None:
    assert "relevance_score" in mock_groq_scoring_response()["choices"][0]["message"]["content"]
    for factory in (
        mock_groq_scoring_response_invalid_score_low,
        mock_groq_scoring_response_invalid_score_high,
        mock_groq_scoring_response_invalid_reasoning_too_long,
    ):
        payload = factory()
        assert "choices" in payload


def test_publisher_html_mocks_have_expected_markers() -> None:
    clean = mock_publisher_html()
    assert "<article>" in clean
    assert "<script>" in clean

    paywall = mock_publisher_html_paywall()
    assert "Subscribe" in paywall