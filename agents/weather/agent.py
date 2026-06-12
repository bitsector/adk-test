import os

from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()


def get_weather(city: str) -> dict:
    """Stub weather tool. Replace with a real API call.

    Tools follow the repo convention: return a dict, never raise. On failure
    return {"error": "<reason>", ...} so the agent can handle it gracefully.
    """
    return {
        "city": city,
        "forecast": f"Pretend it is sunny in {city}, 22 C.",
    }


root_agent = Agent(
    name="root_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash-lite"),
    instruction=(
        "You are a weather assistant. When asked about a city's weather, call "
        "get_weather with the city name and report the result conversationally."
    ),
    tools=[get_weather],
)
