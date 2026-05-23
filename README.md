# adk-test

Minimal starter app for experimenting with Google's Agent Development Toolkit
(ADK).

## What this adds

- A tiny Python package with an ADK `root_agent`
- One example tool, `build_experiment_plan`, so the app can demonstrate tool use
- Standard project metadata in `pyproject.toml`

## Prerequisites

- Python 3.11+
- A Gemini API key in `GOOGLE_API_KEY`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run the app

Use the default Gemini model or override it with `ADK_MODEL`.

```bash
export GOOGLE_API_KEY=your-api-key
adk run adk_test
```

To use the web UI:

```bash
export GOOGLE_API_KEY=your-api-key
adk web .
```

Then select `adk_test` in the UI.

## Project layout

```text
adk_test/
  agent.py
```