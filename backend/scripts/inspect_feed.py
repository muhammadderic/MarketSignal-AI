"""
Inspect the real structure and data types returned by GoogleRSSClient.fetch_feed().

This is a one-off developer utility — NOT a pytest test. It hits the live
Google News RSS API and prints the keys and types of the parsed `feed` and
the first `entries` item, so you can see the actual shape of the data
(`feedparser.util.FeedParserDict` and its nested fields).

Usage:
    python -m scripts.inspect_feed

Notes:
    - Requires network access to https://news.google.com
    - Change `locale=` below to inspect a different locale ("ID" or "US")
    - Fields missing from the feed are silently absent (not None), which is
      why downstream code should check `"field" in entry` before accessing it.
"""
from app.integrations.clients import GoogleRSSClient

client = GoogleRSSClient(locale="ID")
result = client.fetch_feed()

print("TOP-LEVEL:", list(result.keys()))
print("\n--- feed ---")
for k, v in result["feed"].items():
    print(f"{k}: {type(v).__name__} = {repr(v)[:80]}")

print("\n--- entries[0] ---")
for k, v in result["entries"][0].items():
    print(f"{k}: {type(v).__name__} = {repr(v)[:120]}")

print(f"\nentries count: {len(result['entries'])}")