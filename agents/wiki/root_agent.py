import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import AgentTool

from .discover_agent import discover_agent
from shared.get_wikipedia_article import get_wikipedia_article

load_dotenv()

root_agent = Agent(
    name="root_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    wait_for_output=True,
    instruction=(
        """You are a Wikipedia research assistant orchestrator.
            For every user term or topic request, call discover_agent as a tool first to get candidate topics with title, url, and snippet.
            Do not automatically pick the first discovery result.
            If one candidate clearly matches the user query more specifically than the others, fetch that candidate by calling get_wikipedia_article with the chosen title.
            Examples of clear intent include queries like "Churchill Tank" or "Churchill, Manitoba".
            If the query is ambiguous or could map to multiple candidates (for example, "Churchill"), do not fetch any article yet.
            Instead, present a numbered candidate list and ask the user to choose exactly one, or provide a refined query.
            If no candidates are returned, explain that discovery failed and ask for a clearer query.
            After the user chooses and you fetch the full article, answer concisely from that content.
            After answering from the fetched article, always end with a markdown link in the format: [<title>](<url>)."""
    ),
    tools=[AgentTool(discover_agent), get_wikipedia_article],
)
