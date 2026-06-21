import os

from dotenv import load_dotenv
from google.adk.agents import Agent

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
root_agent = Agent(
    name="root_agent",
    model=os.getenv("VOICE_MODEL_ID", "gemini-2.5-flash-native-audio-latest"),
    instruction=(
        "You are a friendly voice assistant. Keep replies short and natural, "
        "the way a person speaks out loud. If asked the time, call get_time."
    ),
    tools=[get_time],
)
