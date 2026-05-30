import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from tools.get_wikipedia_article import get_wikipedia_article

load_dotenv()

root_agent = Agent(
    name="root_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    instruction=(
        "You are a Wikipedia research assistant. "
        "For factual questions about people, places, events, and topics, always call "
        "get_wikipedia_article first. Then answer concisely using the tool result. "
        "After your answer, always end with a markdown link to the source article in "
        "the format: [<title>](<url>)"
    ),
    tools=[get_wikipedia_article],
)
