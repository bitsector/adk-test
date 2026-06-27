# Wiki agent

A Wikipedia research orchestrator. The root agent calls a `discover_agent`
sub-agent (as a tool) to fetch candidate topics, then pulls the chosen article
with `get_wikipedia_article`. Its Wikipedia tools live in `shared/`, a subpackage
private to this agent.

Unlike the voice and rag agents, wiki needs **no Vertex AI and no service
account** — it runs on the plain AI Studio (API-key) backend. All it reads is
`GOOGLE_API_KEY` and `MODEL_ID` (default `gemini-2.5-flash-lite`).

## Run locally

```bash
adk web agents        # from the repo root, then pick "wiki" in the UI
```

## Run in Docker

No `.env` is baked into the image (`.dockerignore` excludes it); config is
injected at run time. Build from the **repo root** so `requirements.txt` is
reachable (`COPY` can't climb above the build context):

```bash
docker build -f agents/wiki/Dockerfile -t wiki-agent .
```

Run, injecting only the two vars wiki needs:

```bash
docker run --rm -p 8000:8000 \
  -e GOOGLE_API_KEY=your_gemini_api_key \
  -e MODEL_ID=gemini-2.5-flash-lite \
  wiki-agent
```

Then open **http://localhost:8000** (not `0.0.0.0`) and pick wiki.

To avoid putting the key in your shell history, load `.env` and pass the two
vars through by name instead:

```bash
set -a; source .env; set +a
docker run --rm -p 8000:8000 -e GOOGLE_API_KEY -e MODEL_ID wiki-agent
```

> **Do not use `--env-file .env`.** This repo's `.env` sets
> `GOOGLE_GENAI_USE_VERTEXAI=True` (for the voice agent), which would flip wiki
> onto the Vertex backend and then demand a service-account credentials file.
> Listing `-e GOOGLE_API_KEY -e MODEL_ID` forwards *only* those two, leaving the
> Vertex switch behind.

> If `http://localhost:8000` won't connect at all — the request just hangs with
> no access-log line in the container — it's the NordVPN kill switch blocking
> host↔container traffic. Fix: `nordvpn set lan-discovery enable`.
