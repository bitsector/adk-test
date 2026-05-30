import wikipedia

wikipedia.set_user_agent("adk-wiki-agent/1.0 (educational project; local dev)")


def get_wikipedia_article(title: str) -> dict:
    """Fetches the full text of a Wikipedia article.

    Args:
        title: Article title or search term (e.g. "Vipassana").

    Returns:
        dict with the resolved title, full article text, and source URL.
        On failure, returns a dict with an "error" key.
    """
    try:
        results = wikipedia.search(title, results=1)
        if not results:
            return {"error": "no_results", "query": title}
        page = wikipedia.page(results[0], auto_suggest=False)
        return {
            "title": page.title,
            "content": page.content,
            "url": page.url,
        }
    except wikipedia.DisambiguationError as e:
        return {"error": "disambiguation", "options": e.options[:10]}
    except wikipedia.PageError:
        return {"error": "page_not_found", "query": title}
