import os
import logging
import re
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()
logger = logging.getLogger(__name__)
WIKIPEDIA_HEADERS = {
    "User-Agent": "adk-wiki-agent/1.0 (educational project; local dev)",
    "Accept": "application/json",
}


def _search_wikipedia_title(query: str) -> str | None:
    """Find the best matching Wikipedia page title for a natural-language query."""
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": 1,
        "srlimit": 5,
    }
    response = requests.get(search_url, params=params, headers=WIKIPEDIA_HEADERS, timeout=10)
    logger.info("Wikipedia search status=%s query=%r", response.status_code, query)
    if response.status_code != 200:
        return None

    data = response.json()
    results = data.get("query", {}).get("search", [])
    if not results:
        return None

    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    query_tokens = _tokens(query)
    stop = {
        "what",
        "when",
        "who",
        "is",
        "was",
        "the",
        "of",
        "a",
        "an",
        "birthday",
        "birth",
        "date",
        "born",
    }
    query_tokens = {t for t in query_tokens if t not in stop}

    best_title = None
    best_score = -10_000
    for item in results:
        title = item.get("title", "")
        if not title:
            continue
        title_tokens = _tokens(title)

        # Prefer concise titles with strong token overlap (e.g., "Winston Churchill").
        overlap = len(query_tokens & title_tokens)
        extras = max(0, len(title_tokens - query_tokens))
        exact_bonus = 50 if title.lower() == query.lower() else 0
        score = (overlap * 10) - extras + exact_bonus
        if score > best_score:
            best_score = score
            best_title = title

    return best_title or results[0].get("title")


def _query_candidates(query: str) -> list[str]:
    """Create progressively simpler search candidates from natural language input."""
    candidates: list[str] = []

    def _add(value: str) -> None:
        value = value.strip(" ,")
        if value and value not in candidates:
            candidates.append(value)

    base = query.strip()
    cleaned = re.sub(r"[?!.]+$", "", base).strip()

    reduced = cleaned
    reduced = re.sub(r"(?i)^what\s+was\s+the\s+birthday\s+of\s+", "", reduced)
    reduced = re.sub(r"(?i)^what\s+is\s+the\s+birthday\s+of\s+", "", reduced)
    reduced = re.sub(r"(?i)^when\s+was\s+", "", reduced)
    reduced = re.sub(r"(?i)^who\s+is\s+", "", reduced)
    # Prioritize normalized candidates before the raw sentence.
    _add(reduced)

    no_birth_terms = re.sub(
        r"(?i)\b(birthday|birth\s+date|date\s+of\s+birth|born)\b", "", reduced
    )
    _add(re.sub(r"\s+", " ", no_birth_terms))

    _add(cleaned)
    _add(base)

    return candidates


def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a short summary for a topic.

    Args:
        query: Topic to search on Wikipedia.

    Returns:
        A formatted summary string or an error message.
    """
    try:
        # Natural language input often is not a page title; search with fallbacks.
        title = None
        for candidate in _query_candidates(query):
            title = _search_wikipedia_title(candidate)
            logger.info(
                "Wikipedia candidate query=%r matched_title=%r", candidate, title
            )
            if title:
                break

        if not title:
            return f"No Wikipedia results found for '{query}'."

        extract_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "format": "json",
            "titles": title,
        }
        response = requests.get(
            extract_url,
            params=params,
            headers=WIKIPEDIA_HEADERS,
            timeout=10,
        )
        logger.info(
            "Wikipedia extract status=%s query=%r title=%r",
            response.status_code,
            query,
            title,
        )

        if response.status_code != 200:
            return (
                f"Wikipedia extract lookup failed after searching for '{query}' "
                f"(matched title '{title}', status {response.status_code})."
            )

        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        summary = page.get("extract", "No summary available")
        page_title = page.get("title", title)
        encoded_title = quote(page_title.replace(" ", "_"), safe="()")
        page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"
        return f"Title: {page_title}\nSummary: {summary}\nURL: {page_url}"
    except Exception as exc:
        logger.exception("Wikipedia tool failed for query=%r", query)
        return f"Wikipedia lookup error: {exc}"


root_agent = Agent(
    name="wiki_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    instruction=(
        "You are a Wikipedia research assistant. "
        "For factual questions about people, places, events, and topics, always call "
        "search_wikipedia first. Then answer concisely using the tool result."
    ),
    tools=[search_wikipedia],
)
