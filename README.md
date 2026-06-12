# adk-test

Minimal Google ADK playground with a Wikipedia-search tool.

## Files

- `agents/`: ADK apps directory. Each subfolder exposing a `root_agent` is a selectable app.
  - `agents/wiki/`: Wikipedia research orchestrator (`root_agent`) + `discover_agent` sub-agent.
  - `agents/weather/`: minimal template agent to copy for new experiments.
  - `agents/shared/`: shared tool functions imported by agents (not an app itself).
- `requirements.txt`: Python dependencies for local development.

## Quickstart

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set your Gemini API key

Set it for the current shell:

```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

Or create a local `.env` file in the repo root:

```bash
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_ID=gemini-2.5-flash-lite
EOF
```

Agents load `.env` automatically via `python-dotenv`.

### 4. Run with ADK

Point ADK at the `agents/` directory. Each subfolder with a `root_agent` shows up as a
selectable app in the web UI. Run from the repo root:

```bash
adk web agents
```

Then open the local URL shown in the terminal and pick an app (`wiki`, `weather`, …)
from the selector.

Or run a single app directly in CLI mode:

```bash
adk run agents/wiki
```

### Debug tool behavior

If the tool result looks wrong, inspect the ADK log file:

```bash
tail -F /tmp/agents_log/agent.latest.log
```

The Wikipedia tool logs search/summary status lines so you can see the query,
matched title, and HTTP status.

## Try prompts

- `Who is Ada Lovelace?`
- `Summarize Kubernetes from Wikipedia.`
- `Find Wikipedia info about Recife.`