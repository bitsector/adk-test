import re
from html import unescape
from urllib.parse import quote

import requests

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_REST_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
HEADERS = {"User-Agent": "adk-wiki-agent/1.0 (educational project; local dev)"}


def fetch_short_snippet(page_title: str) -> str:
    """Fetch a short summary line for a Wikipedia title."""
    url = f"{WIKIPEDIA_REST_URL}/{quote(page_title.replace(' ', '_'))}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return "No short snippet available."

    extract = payload.get("extract", "")
    clean = unescape(re.sub(r"\s+", " ", extract)).strip()
    return clean or "No short snippet available."


def discover_wikipedia_candidates(query: str, limit: int = 8) -> list[dict]:
    """Return related Wikipedia pages as title/url/snippet triples."""
    params = {
        "action": "opensearch",
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json",
    }

    try:
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return []

    if not isinstance(payload, list) or len(payload) < 4:
        return []

    titles = payload[1]
    urls = payload[3]

    discovered: list[dict] = []

    for title, url in zip(titles, urls):
        snippet = fetch_short_snippet(title)

        discovered.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
            }
        )

    return discovered


if __name__ == "__main__":
    query = "churchill"
    results = discover_wikipedia_candidates(query)

    print(f"Query: {query}")
    print(f"Found {len(results)} related pages\n")

    for i, item in enumerate(results, start=1):
        print(f"{i}. {item['title']}")
        print(f"   URL: {item['url']}")
        print(f"   Snippet: {item['snippet']}\n")
