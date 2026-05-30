import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from tools.discover_wikipedia_candidates import discover_wikipedia_candidates

load_dotenv()

discover_agent = Agent(
    name="discover_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    instruction=(
        "You are a Wikipedia discovery assistant. "
        "Always call discover_wikipedia_candidates first. "
        "Return candidate pages as title, url, and short snippet. "
        "Do not fetch full article content."
    ),
    tools=[discover_wikipedia_candidates],
)
