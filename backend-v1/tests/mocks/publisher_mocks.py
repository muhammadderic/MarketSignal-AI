"""Mock factories for publisher web pages.

Used to exercise URL resolution and HTML scraping without live HTTP calls.
"""

from __future__ import annotations


def mock_publisher_html(
    *,
    headline: str = "Acme Corp Q3 Results",
    body: str = "Acme Corp reported quarterly revenue of $1.2B, up 12% year over year.",
) -> str:
    """Return a clean publisher HTML page with boilerplate and script tags."""
    return f"""<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>{headline}</title>
      <script>window.dataLayer = window.dataLayer || [];</script>
      <link rel="stylesheet" href="/styles.css">
    </head>
    <body>
      <header><nav><a href="/">Home</a> | <a href="/markets">Markets</a></nav></header>
      <article>
        <h1>{headline}</h1>
        <p>{body}</p>
      </article>
      <footer>&copy; 2026 Example Publisher</footer>
      <script src="/analytics.js"></script>
    </body>
    </html>
    """


def mock_publisher_html_paywall() -> str:
    """Return a page that should be treated as a paywall / blocked response."""
    return """<!doctype html>
    <html><body>
    <h1>Subscribe to continue reading</h1>
    <p>This content is available to subscribers only.</p>
    </body></html>
    """


def mock_publisher_html_empty_body() -> str:
    """Return a page with no meaningful article body."""
    return """<!doctype html>
    <html><head><title>Empty</title></head><body></body></html>
    """