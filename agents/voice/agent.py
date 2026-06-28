import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from .shared.get_wikipedia_article import get_wikipedia_article

load_dotenv()


def get_time(timezone: str = "local") -> dict:
    """Return the current time. Demonstrates that tools work in live (voice) mode.

    Repo convention: return a dict, never raise. On failure return
    {"error": "<reason>", ...} so the agent can handle it conversationally.
    """
    from datetime import datetime

    return {"timezone": timezone, "now": datetime.now().isoformat(timespec="seconds")}


# Voice needs a Live API model. Plain "gemini-2.5-flash" does NOT support the
# Live API and cannot do bidirectional audio.
#
# CRITICAL: the Live model ID is backend-specific, and the backend is chosen by
# GOOGLE_GENAI_USE_VERTEXAI in .env (process-wide). A name from the wrong backend
# fails with "1008 ... not found / not supported for bidiGenerateContent".
#   - AI Studio (GOOGLE_GENAI_USE_VERTEXAI unset/False): gemini-2.5-flash-native-audio-latest
#       (verified via client.models.list(); see also -preview-09-2025 / -12-2025,
#        gemini-3.1-flash-live-preview)
#   - Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=True):         gemini-live-2.5-flash-native-audio
# Note: rag needs Vertex, so running voice on AI Studio means rag won't work in
# the same `adk web` process, and vice versa. Override with VOICE_MODEL_ID in .env.
#
# The default tracks the backend automatically so flipping GOOGLE_GENAI_USE_VERTEXAI
# doesn't silently leave a wrong-backend model name behind (the 1008 footgun above).
_USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1")
_DEFAULT_VOICE_MODEL = (
    "gemini-live-2.5-flash-native-audio"  # Vertex AI
    if _USE_VERTEX
    else "gemini-2.5-flash-native-audio-latest"  # AI Studio
)
root_agent = Agent(
    name="root_agent",
    model=os.getenv("VOICE_MODEL_ID", _DEFAULT_VOICE_MODEL),
    instruction=(
        "You are a friendly voice assistant. Keep replies short and natural, "
        "the way a person speaks out loud. "
        "You have two tools:\n"
        "- get_time(timezone): call it when asked for the current time.\n"
        "- get_wikipedia_article(title): your Wikipedia tool. ALWAYS use it whenever "
        "the user asks you to look up, fetch, or tell them about a topic, person, "
        "place, or thing. Do not answer factual lookups from memory — call the "
        "Wikipedia tool and answer only from what it returns. When the article comes "
        "back, summarize the key points in a few short sentences rather than reading "
        "it out verbatim."
    ),
    tools=[get_time, get_wikipedia_article],
)
