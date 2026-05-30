import re
from html import unescape
from urllib.parse import quote

import requests

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_REST_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
HEADERS = {"User-Agent": "adk-wiki-agent/1.0 (educational project; local dev)"}


def _fetch_short_snippet(page_title: str) -> str:
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


def discover_wikipedia_candidates(query: str, limit: int = 8) -> dict:
    """Discover related Wikipedia pages as title/url/snippet entries."""
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
    except requests.RequestException as exc:
        return {
            "query": query,
            "candidates": [],
            "error": f"request_failed: {exc.__class__.__name__}",
        }

    if not isinstance(payload, list) or len(payload) < 4:
        return {
            "query": query,
            "candidates": [],
            "error": "invalid_response_shape",
        }

    titles = payload[1]
    urls = payload[3]
    candidates = []

    for title, url in zip(titles, urls):
        candidates.append(
            {
                "title": title,
                "url": url,
                "snippet": _fetch_short_snippet(title),
            }
        )

    return {
        "query": query,
        "candidates": candidates,
    }
