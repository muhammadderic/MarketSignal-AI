# Google News Link Resolution

## Problem
Google News RSS feeds return article links as obfuscated redirect tokens
(`https://news.google.com/rss/articles/CBMi...`), not the real publisher URL.
Since Google's 2024 format change, these tokens can no longer be decoded by
simple base64 decoding — they must be resolved via Google's internal, undocumented
`batchexecute` RPC endpoint.

## Mechanism
1. **Extract article ID** — pull the token from the URL path
   (`utils/google_news_decoder.py::extract_article_id`).
2. **Fetch article page** — `GET https://news.google.com/rss/articles/{id}`
   (`clients/google_news_client.py::get_article_page`, `follow_redirects=True`
   required — Google 302s to the same URL with locale params appended).
3. **Scrape decoding params** — extract `data-n-a-sg` (signature) and
   `data-n-a-ts` (timestamp) attributes from the page HTML
   (`utils/google_news_decoder.py::parse_decoding_params`).
4. **Call batchexecute** — `POST https://news.google.com/_/DotsSplashUi/data/batchexecute`
   with RPC ID `Fbv4je`, article ID, signature, and timestamp packed into
   Google's batch-RPC payload format
   (`utils/google_news_decoder.py::build_batchexecute_body`,
   `clients/google_news_client.py::post_batchexecute`).
5. **Parse response** — unwrap the nested JSON-in-JSON response to extract
   the real publisher URL (`utils/google_news_decoder.py::parse_batchexecute_response`).

This is the same approach used by public decoder libraries
(`google-news-url-decoder`, `GoogleNewsDecoder`, `gnewsdecoder`) — there is no
official Google API for this.

## Layer responsibilities
- `clients/google_news_client.py` — raw HTTP only, no parsing.
- `utils/google_news_decoder.py` — pure functions: ID extraction, regex
  scraping, payload building, response parsing. No I/O.
- `adapters/google_news_adapter.py` — orchestrates client + utils, returns a
  resolved URL or raises `LinkDecodingError`.
- `services/link_resolution_service.py` — business logic: concurrency limit,
  per-article error handling, persistence via repository.

## Batch size guidance
Each article resolution costs **2 sequential HTTP calls** (page fetch +
batchexecute), limited to `MAX_CONCURRENT_RESOLUTIONS = 5` concurrent
articles at a time. Given that:

- **Recommended batch size per request: 10–30 IDs.**
  - Below ~10: concurrency slot (5) is underused, no real efficiency gain from batching.
  - Above ~30: total wall-clock time grows roughly linearly (6+ concurrency
    waves), increasing risk of hitting the overall request timeout, and raises
    the chance of Google rate-limiting/blocking the client mid-batch.
- Rough timing: ~2 HTTP round-trips per article ÷ 5 concurrent ≈ 2 "waves" per
  10 articles. At ~1–2s per call, 30 articles ≈ 12–24s total — still within a
  reasonable HTTP request timeout.
- If regularly resolving more than 30 pending articles, call the route
  repeatedly (e.g. a scheduled job paging through `PENDING` rows) rather than
  sending one large batch.

## ⚠️ Fragility — what breaks and where to look
This entire mechanism depends on **undocumented Google internals** that can
change without notice. If resolution starts failing broadly, check in this order:

| Symptom | Likely cause | Where to fix |
|---|---|---|
| `LinkDecodingError: Could not find signature/timestamp` | Google changed the HTML attribute names/structure of the article page | `parse_decoding_params` regexes |
| `LinkDecodingError: Unexpected response format` | Google changed the batchexecute response shape | `parse_batchexecute_response` |
| HTTP 4xx/5xx from batchexecute | RPC ID (`Fbv4je`) or payload structure changed | `build_batchexecute_body`, `RPC_ID` constant |
| `extract_article_id` raises on valid-looking URLs | Google changed the URL path format | `extract_article_id` |

**First response to any breakage:** check whether a maintained public decoder
library (e.g. `google-news-url-decoder`, `googlenewsdecoder`) has already
shipped a fix — these libraries tend to get patched quickly after Google
changes something, and their diffs are the fastest way to see what changed.

## Known limitations
- No official SLA/stability guarantee from Google — this can break at any time.
- Rate limiting: concurrency is capped (`MAX_CONCURRENT_RESOLUTIONS` in
  `link_resolution_service.py`) to reduce risk of being throttled/blocked.
- Resolution is best-effort: failures are caught and marked `FAILED` per
  article rather than failing the whole batch.