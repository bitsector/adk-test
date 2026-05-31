import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from tools.discover_wikipedia_candidates import discover_wikipedia_candidates

load_dotenv()

discover_agent = Agent(
    name="discover_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    wait_for_output=True,
    instruction=(
        "You are a Wikipedia discovery assistant. "
        "Always call discover_wikipedia_candidates first. "
        "Return only discovery candidates as title, url, and short snippet. "
        "Do not choose a final topic, and do not fetch full article content. "
        "If results are empty, report that no candidates were found. "
        "After calling the tool, return a concise, structured list of candidates and end your response."
    ),
    tools=[discover_wikipedia_candidates],
)
