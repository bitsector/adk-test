# Voice agent

A bidirectional (audio in / audio out) voice assistant built on the Gemini
**Live API**. Run it through `adk web` and use the microphone in the dev UI.

## Why this needs Vertex AI

`adk web` only offers **transparent** session resumption (it hard-wires
`SessionResumptionConfig(transparent=True)` in the API server), and transparent
resumption is **only supported on the Vertex AI backend**. On the AI Studio
(API-key) backend the same toggle errors with:

> Transparent session resumption is only supported for Vertex AI backend.

So to get session resumption (continuing a conversation past the ~10‑min
connection cap and across drops), the voice agent must run on Vertex.

## What you need

1. **A service account** with exactly one role:

   - `roles/aiplatform.user` (display name "Vertex AI User")

   That role grants `aiplatform.endpoints.predict`, which is the only
   permission the Live API call requires. Nothing else is needed for voice.

   Verify the SA's roles:

   ```bash
   gcloud projects get-iam-policy gcp-cloud-run-tests \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:voice-agent@gcp-cloud-run-tests.iam.gserviceaccount.com" \
     --format="table(bindings.role)"
   # expected: roles/aiplatform.user
   ```

2. **The SA key** downloaded to `secrets/voice-agent-sa-key.json`.

3. **The Vertex AI API enabled** on the project (`aiplatform.googleapis.com`).

4. **`.env` pointed at Vertex** (see below).

## .env settings

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests
GOOGLE_CLOUD_LOCATION=us-central1            # must support the Live model
GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/secrets/voice-agent-sa-key.json
```

`GOOGLE_GENAI_USE_VERTEXAI` is a **process-wide** switch, so it flips every
agent in the same `adk web` session onto Vertex, and they all use the single
`GOOGLE_APPLICATION_CREDENTIALS`. `GOOGLE_API_KEY` is ignored on Vertex.

The Live model ID is backend-specific. On Vertex it is
`gemini-live-2.5-flash-native-audio` (the default in `agent.py`); override with
`VOICE_MODEL_ID` if needed.

## Run

```bash
adk web        # from the repo root, then open the voice agent in the UI
```

## Run in Docker

The image runs `adk web` on the Vertex backend. Mic capture/playback happen in
the **browser**, not the container — it's just the web server relaying audio over
a WebSocket to the Gemini Live API, so no sound devices are needed. The SA key is
**not** baked into the image (`.dockerignore` excludes `secrets/`); bind-mount it
read-only at run time.

Build from the **repo root** (the context must be the root so `requirements.txt`
is reachable):

```bash
docker build -f agents/voice/Dockerfile -t voice-agent .
```

Run (override `GOOGLE_APPLICATION_CREDENTIALS` to the in-container path — do *not*
use `--env-file .env`, whose value is a host path that won't exist in the container):

```bash
docker run --rm -p 8000:8000 \
  -e GOOGLE_GENAI_USE_VERTEXAI=True \
  -e GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests \
  -e GOOGLE_CLOUD_LOCATION=us-central1 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
  -v "$PWD/secrets/voice-agent-sa-key.json:/secrets/sa.json:ro" \
  voice-agent
```

### ⚠️ Open `http://localhost:8000`, NOT `http://0.0.0.0:8000`

The container binds `0.0.0.0` (correct — that's the bind address so the port is
reachable), and ADK's startup banner prints `http://0.0.0.0:8000`. **Do not type
that into the browser.** The microphone (`getUserMedia`) only works in a *secure
context*: browsers trust `localhost` / `127.0.0.1` but **not** `0.0.0.0`. On
`0.0.0.0` the page can't access the mic (`navigator.mediaDevices` is `undefined`),
so the call connects but no audio is ever recorded or sent, and the session drops.

Use **`http://localhost:8000`** (or `http://127.0.0.1:8000`).

> If the browser can't reach the port at all (rather than just no audio), check
> the NordVPN kill switch: `nordvpn set lan-discovery enable`.
