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
