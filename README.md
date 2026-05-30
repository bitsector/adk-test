# adk-test

Minimal Google ADK playground with a Wikipedia-search tool.

## Files

- `wiki_agent/agent.py`: ADK agent definition (`root_agent`) with a custom `search_wikipedia` tool.
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

`wiki_agent/agent.py` loads `.env` automatically via `python-dotenv`.

### 4. Run with ADK

ADK app names must be valid Python identifiers (letters, digits, underscores). Since this
repo folder is named `adk-test`, run ADK against the valid subfolder app directly.

```bash
adk web wiki_agent
```

Then open the local URL shown in the terminal.

If the browser is still on a stale URL like `/dev/apps/adk-test/...`, switch to
`wiki_agent` in the app selector or reload from `/`.

Or run directly in CLI mode:

```bash
adk run wiki_agent
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