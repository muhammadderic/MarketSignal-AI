import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
BATCHEXECUTE_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"


class GoogleNewsClient:
    """Pure HTTP layer for Google News' internal endpoints. No parsing/business logic here."""

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    async def get_article_page(self, article_id: str) -> str:
        url = f"https://news.google.com/rss/articles/{article_id}"
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            return response.text

    async def post_batchexecute(self, body: str) -> str:
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.post(BATCHEXECUTE_URL, headers=headers, content=body)
            response.raise_for_status()
            return response.text