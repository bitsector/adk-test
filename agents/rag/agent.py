import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from .prompts import return_instructions_root

load_dotenv()


def _materialize_inline_credentials() -> None:
    """Allow the SA key to be supplied inline instead of as a file.

    ADC only understands a file *path* (GOOGLE_APPLICATION_CREDENTIALS). If you
    prefer to keep the whole key in .env / a single env var, set
    GOOGLE_SERVICE_ACCOUNT_JSON to either the raw JSON (single-quote it in .env)
    or its base64 encoding; we write it to a private temp file and point ADC at
    it. An explicit GOOGLE_APPLICATION_CREDENTIALS path always wins.
    """
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        return
    raw = raw.strip()
    if not raw.startswith("{"):  # not raw JSON -> assume base64-encoded JSON
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    import tempfile

    fd, path = tempfile.mkstemp(prefix="rag-sa-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write(raw)
    os.chmod(path, 0o600)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path


_materialize_inline_credentials()

# --- Vertex AI configuration ---
# RAG Engine is a Vertex AI service, so this agent runs on the Vertex backend
# rather than the AI Studio API-key path the other agents in this repo use.
# Set these in .env when you are ready (see agents/rag/README.md):
#   GOOGLE_GENAI_USE_VERTEXAI=True
#   GOOGLE_CLOUD_PROJECT=<your-project-id>
#   GOOGLE_CLOUD_LOCATION=us-east1
#   RAG_CORPUS=<filled in by prepare_corpus_and_data.py>
#
# Credentials come from Application Default Credentials (ADC), so this code does
# not change between dev and prod. ADC resolves in this order automatically:
#   1. GOOGLE_APPLICATION_CREDENTIALS -> a service-account key or WIF config file
#   2. an attached service account (Cloud Run/GKE) via the metadata server
#   3. your local `gcloud auth application-default login` (dev only)
# Fill GOOGLE_CLOUD_PROJECT from ADC if it is unset.
try:
    import google.auth

    _, _project_id = google.auth.default()
    if _project_id:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", _project_id)
except Exception:
    # No ADC available yet (Vertex not configured) — fine, the agent still
    # loads as a plain chat agent until you set up the corpus.
    pass
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

# The RAG retrieval tool is only wired up once a corpus exists. Run
# `python agents/rag/shared_libraries/prepare_corpus_and_data.py` to create one;
# it writes RAG_CORPUS into .env. Until then this runs as a plain chat agent.
# The Vertex import is guarded so this agent can sit in the `adk web` picker
# alongside the API-key agents before google-cloud-aiplatform is installed.
tools = []
rag_corpus = os.environ.get("RAG_CORPUS")
if rag_corpus:
    try:
        from google.adk.tools.retrieval.vertex_ai_rag_retrieval import (
            VertexAiRagRetrieval,
        )
        from vertexai.preview import rag

        ask_vertex_retrieval = VertexAiRagRetrieval(
            name="retrieve_rag_documentation",
            description=(
                "Use this tool to retrieve documentation and reference materials "
                "for the question from the RAG corpus,"
            ),
            rag_resources=[rag.RagResource(rag_corpus=rag_corpus)],
            similarity_top_k=10,
            vector_distance_threshold=0.6,
        )
        tools.append(ask_vertex_retrieval)
    except ImportError:
        print(
            "[agents/rag] RAG_CORPUS is set but google-cloud-aiplatform is not "
            "installed. Run `pip install -r requirements.txt`. Running as a "
            "plain chat agent for now."
        )

root_agent = Agent(
    name="root_agent",
    model=os.getenv("MODEL_ID", "gemini-2.5-flash"),
    instruction=return_instructions_root(),
    tools=tools,
)
