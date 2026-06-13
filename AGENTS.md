# This is an exmaple project - I want to learn ADK

Here are the sources for you, AI, to learn from and reference to help me learn and implement stuff.

Official documentation

Docs home: https://google.github.io/adk-docs/ (the canonical site; adk.dev you used also resolves to it)
Python quickstart: https://google.github.io/adk-docs/get-started/python/
Get-started hub (all languages): https://google.github.io/adk-docs/get-started/
Google Cloud / Gemini Enterprise Agent Platform ADK page: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk

GitHub

Framework source (Python): https://github.com/google/adk-python
Samples: https://github.com/google/adk-samples, with the Python agents at https://github.com/google/adk-samples/tree/main/python/agents
Docs source: https://github.com/google/adk-docs

Package

PyPI: https://pypi.org/project/google-adk/

## Project layout

`agents/` is the ADK "apps" directory. Each subfolder that exposes a `root_agent`
is one selectable app in the `adk web` dropdown. `shared/` holds tools imported by
agents and is not itself an app.

```
agents/
├── shared/      # shared tool functions (importable as `shared`), not an app
├── wiki/        # app: Wikipedia research orchestrator + discover sub-agent
├── weather/     # app: minimal template agent to copy for new experiments
└── rag/         # app: Vertex AI RAG Engine agent (needs Vertex, see rag/README.md)
```

## Running

Run from the repo root:

```bash
adk web agents      # web UI with an app picker (wiki, weather, …)
adk run agents/wiki # CLI, single app
```

## Adding a new agent

1. Create `agents/<name>/` (name must be a valid Python identifier — no hyphens).
2. Add `__init__.py` containing `from . import agent`.
3. Add `agent.py` defining a module-level `root_agent = Agent(...)`.
4. It appears in the `adk web` picker automatically. Copy `agents/weather/` as a starting point.

## Conventions

- Tool functions return a dict and never raise; on failure return `{"error": "<reason>", ...}`.
- Shared tools live in `agents/shared/` and are imported as `from shared.x import y`.
- Sub-agents (e.g. wiki's discover_agent) are plain modules inside an app folder, not
  separate app folders, so they don't show up in the picker.
- Config is read from `.env` via `python-dotenv` (`GOOGLE_API_KEY`, `MODEL_ID`).