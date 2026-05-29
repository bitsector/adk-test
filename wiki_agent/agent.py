import os

import requests
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()


def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a short summary for a topic.

    Args:
        query: Topic to search on Wikipedia.

    Returns:
        A formatted summary string or an error message.
    """
    try:
        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + query.replace(" ", "_")
        )
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "N/A")
            summary = data.get("extract", "No summary available")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            return f"Title: {title}\nSummary: {summary}\nURL: {page_url}"

        return f"Wikipedia page not found for '{query}' (status {response.status_code})."
    except Exception as exc:
        return f"Wikipedia lookup error: {exc}"


root_agent = Agent(
    name="wiki_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    instruction=(
        "You are a research assistant. "
        "For factual questions, call search_wikipedia first and then answer concisely."
    ),
    tools=[search_wikipedia],
)
