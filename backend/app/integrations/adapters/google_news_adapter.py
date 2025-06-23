from app.integrations.clients import GoogleNewsClient
from app.modules.news_scraping.utils import (
    build_batchexecute_body,
    extract_article_id,
    parse_batchexecute_response,
    parse_decoding_params,
)


class GoogleNewsLinkAdapter:
    """Orchestrates the client calls and returns a ready-to-use resolved URL
    (or raises LinkDecodingError) — the service layer never touches raw HTML/JSON."""

    def __init__(self, client: GoogleNewsClient):
        self._client = client

    async def resolve(self, google_url: str) -> str:
        article_id = extract_article_id(google_url)
        html = await self._client.get_article_page(article_id)
        signature, timestamp = parse_decoding_params(html)
        body = build_batchexecute_body(article_id, signature, timestamp)
        raw_response = await self._client.post_batchexecute(body)
        return parse_batchexecute_response(raw_response)