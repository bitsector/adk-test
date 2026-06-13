# rag — RAG agent (Vertex AI RAG Engine)

Faithful port of the [google/adk-samples RAG agent](https://github.com/google/adk-samples/tree/main/python/agents/RAG).
Answers questions about documents ingested into **Vertex AI RAG Engine** and cites
its sources. By default the corpus is Alphabet's 2025 10-K PDF.

## What was ported vs. adapted

- **Ported verbatim:** the retrieval tool config (`retrieve_rag_documentation`,
  `similarity_top_k=10`, `vector_distance_threshold=0.6`), the grounding prompt in
  [prompts.py](prompts.py), and the corpus-ingestion script in
  [shared_libraries/prepare_corpus_and_data.py](shared_libraries/prepare_corpus_and_data.py).
- **Adapted to this repo:** exposes a module-level `root_agent` (so it shows up in
  the `adk web` picker) instead of the sample's `App(...)` wrapper, and reads the
  model from `MODEL_ID`. The sample's Arize/OpenInference tracing was dropped — it
  needs a separate account and is not part of RAG.

## How the RAG works (where the "RAG part" lives)

1. **Ingestion (run once):** `prepare_corpus_and_data.py` creates a corpus, embeds
   the PDF with `text-embedding-004`, and writes the corpus id to `.env` as `RAG_CORPUS`.
2. **Retrieval (runtime):** [agent.py](agent.py) builds a `VertexAiRagRetrieval` tool
   pointed at `RAG_CORPUS`. Gemini calls it, RAG Engine returns the top matching
   chunks, and Gemini answers from them with citations.

If `RAG_CORPUS` is unset, the tool is skipped and this runs as a plain chat agent.

## Using it on Vertex — step by step

```bash
# 0. Install the Vertex dependency
pip install -r requirements.txt          # adds google-cloud-aiplatform

# 1. A GCP project with billing enabled, then enable the APIs + authenticate.
#    vectorsearch is needed because Serverless mode (step 3) stores vectors in
#    Managed Vector Search; allow 1-2 min for newly enabled APIs to propagate.
gcloud config set project gcp-cloud-run-tests
gcloud services enable aiplatform.googleapis.com vectorsearch.googleapis.com
gcloud auth application-default login
gcloud projects add-iam-policy-binding gcp-cloud-run-tests \
    --member="user:anton.kz.biz@gmail.com" --role="roles/aiplatform.user"

# 2. Configure .env (see .env.example)
#    GOOGLE_GENAI_USE_VERTEXAI=True
#    GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests
#    GOOGLE_CLOUD_LOCATION=us-central1

# 3. (new projects only) switch RAG Engine to Serverless mode. The default
#    "Spanner mode" is allowlist-only for new projects in us-central1/us-east1/us-east4.
#    This is project config -> run it as yourself (Owner), not the runtime SA.
#    gcloud has no native verb for ragEngineConfig, so use gcloud auth + REST:
gcloud auth login            # the runtime SA lacks aiplatform.ragEngineConfigs.update
gcloud config set project gcp-cloud-run-tests
curl -s -X PATCH \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/gcp-cloud-run-tests/locations/us-central1/ragEngineConfig" \
  -d '{"ragManagedDbConfig": {"serverless": {}}}'

# 4. Build the corpus (embeds the 10-K, sets RAG_CORPUS in .env)
python agents/rag/shared_libraries/prepare_corpus_and_data.py

# 4. Run it
adk run agents/rag        # CLI
adk web agents            # web UI, pick "rag" from the dropdown
```

> ⚠️ `GOOGLE_GENAI_USE_VERTEXAI=True` is **process-wide**. When `adk web agents`
> loads every app in one process, the other agents (weather/wiki/extractor) will
> also route through Vertex instead of `GOOGLE_API_KEY`. That's fine as long as the
> project + billing are set up; to keep them on the API-key path, run the RAG agent
> in its own process / shell with that variable set.

To swap in your own documents, change `PDF_URL`/`CORPUS_DISPLAY_NAME` in the
ingestion script (or call `rag.upload_file` / `rag.import_files` for other sources).

## Running in production (service account / WIF, no gcloud)

The code authenticates via **Application Default Credentials (ADC)** and never
calls gcloud, so it runs unchanged in prod — only the credential *source* changes.
ADC resolves: `GOOGLE_APPLICATION_CREDENTIALS` → attached service account → local
gcloud login. Pick the option that matches where you deploy:

**A. On Google Cloud (Cloud Run/GKE) — recommended, keyless.** Attach a service
account to the service; ADC uses the metadata server. No key, no `GOOGLE_APPLICATION_CREDENTIALS`.

```bash
# one-time setup (Console or gcloud; the running service never uses gcloud)
gcloud iam service-accounts create rag-agent --display-name="RAG agent"
gcloud projects add-iam-policy-binding gcp-cloud-run-tests \
    --member="serviceAccount:rag-agent@gcp-cloud-run-tests.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud run deploy rag-agent \
    --service-account=rag-agent@gcp-cloud-run-tests.iam.gserviceaccount.com \
    --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=True,GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests,GOOGLE_CLOUD_LOCATION=us-central1,RAG_CORPUS=<corpus-id>
    # ... + your image/source. Config goes in env vars, NOT a .env file.
```

**B. Off Google Cloud, with an existing identity — WIF, keyless.** Create a
workload identity pool + provider for your IdP (GitHub/AWS/Azure/OIDC), let it
impersonate `rag-agent@...`, download the **credential config** (not a key), and
set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/wif-credential-config.json`.

**C. Off Google Cloud, simplest — service-account JSON key.** Long-lived secret;
use only if A/B don't fit.

```bash
gcloud iam service-accounts keys create secrets/rag-agent-sa-key.json \
    --iam-account=rag-agent@gcp-cloud-run-tests.iam.gserviceaccount.com
# then either point ADC at the file:
#   GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/secrets/rag-agent-sa-key.json
# or keep it inline (agent.py writes it to a private temp file at startup):
#   GOOGLE_SERVICE_ACCOUNT_JSON=$(base64 -w0 secrets/rag-agent-sa-key.json)
```

Keys never expire by default. To force a max lifetime (e.g. 30 days = 720h) set
the org policy `constraints/iam.serviceAccountKeyExpiryHours` (range 8h–2160h) —
it applies to newly created keys. Google considers expiring keys risky for
rotation (they cause outages if not rotated in time); prefer keyless A/B for
real prod and use keys mainly for local/dev.

> 🔒 Key files and WIF configs are gitignored (`secrets/`, `*sa-key*.json`,
> `*service-account*.json`). Keep them out of the image; in real prod use Secret
> Manager / mounted secrets, not a baked-in file. Grant the SA only
> `roles/aiplatform.user` (+ corpus access) — least privilege.

## Verifying & cleaning up

RAG Engine has no real corpus browser in the Cloud Console — the SDK is the source
of truth. The ingestion script confirms success by printing `Total files in corpus`
at the end. To list again at any time: `rag.list_corpora()` / `rag.list_files(...)`.

When you're done, delete the corpus so the managed storage stops costing anything:

```bash
python agents/rag/shared_libraries/delete_corpus.py
```

This calls `rag.delete_corpus` (removes files + embeddings) and clears `RAG_CORPUS`
from `.env`, so the agent drops back to plain-chat mode. The default `RagManagedDb`
storage lives in a Google-managed tenant project, so deleting the corpus — not any
action in your own project's console — is what ends the charge.
