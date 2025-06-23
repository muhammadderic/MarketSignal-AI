import json
import re
from urllib.parse import quote, urlparse

RPC_ID = "Fbv4je"

_SIGNATURE_RE = re.compile(r'data-n-a-sg="([^"]+)"')
_TIMESTAMP_RE = re.compile(r'data-n-a-ts="([^"]+)"')


class LinkDecodingError(Exception):
    """Raised whenever a Google News link can't be resolved to its real URL."""


def extract_article_id(google_url: str) -> str:
    parsed = urlparse(google_url)
    parts = [p for p in parsed.path.split("/") if p]
    if parsed.hostname != "news.google.com" or len(parts) < 2 or parts[-2] not in ("articles", "read"):
        raise LinkDecodingError(f"Unrecognized Google News URL format: {google_url}")
    return parts[-1]


def parse_decoding_params(html: str) -> tuple[str, str]:
    """Extracts the signature + timestamp Google embeds in the article page markup."""
    sg_match = _SIGNATURE_RE.search(html)
    ts_match = _TIMESTAMP_RE.search(html)
    if not sg_match or not ts_match:
        raise LinkDecodingError("Could not find signature/timestamp in Google News page")
    return sg_match.group(1), ts_match.group(1)


def build_batchexecute_body(article_id: str, signature: str, timestamp: str) -> str:
    inner_payload = [
        "garturlreq",
        [
            ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
            "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
        ],
        article_id,
        timestamp,
        signature,
    ]
    rpc_payload = [[[RPC_ID, json.dumps(inner_payload), None, "generic"]]]
    return f"f.req={quote(json.dumps(rpc_payload))}"


def parse_batchexecute_response(raw_text: str) -> str:
    try:
        body = raw_text.split("\n\n")[1]
        parsed = json.loads(body)
        inner = json.loads(parsed[0][2])
        return inner[1]
    except (IndexError, ValueError, TypeError) as exc:
        raise LinkDecodingError("Unexpected response format from Google batchexecute") from exc