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
   the PDF with `text-embedding-004`, and writes the corpus id to `.env` as `CORPUS_NAME`.
2. **Retrieval (runtime):** [agent.py](agent.py) builds a `VertexAiRagRetrieval` tool
   pointed at `CORPUS_NAME`. Gemini calls it, RAG Engine returns the top matching
   chunks, and Gemini answers from them with citations.

If `CORPUS_NAME` is unset, the tool is skipped and this runs as a plain chat agent.

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

# 4. Drop your .pdf / .txt / .docx / .md documents into agents/rag/rag_materials/,
#    then build the corpus. Each run creates a fresh timestamped corpus from all
#    those files (their union = the knowledge base) and writes its resource name
#    to CORPUS_NAME in .env, which the agent reads.
python agents/rag/shared_libraries/prepare_corpus_and_data.py

# 5. Run it
adk run agents/rag        # CLI
adk web agents            # web UI, pick "rag" from the dropdown
```

> ⚠️ `GOOGLE_GENAI_USE_VERTEXAI=True` is **process-wide**. When `adk web agents`
> loads every app in one process, the other agents (weather/wiki/extractor) will
> also route through Vertex instead of `GOOGLE_API_KEY`. That's fine as long as the
> project + billing are set up; to keep them on the API-key path, run the RAG agent
> in its own process / shell with that variable set.

To add or change documents, just edit the contents of `rag_materials/` and re-run
the ingestion script — it sweeps every `*.pdf` / `*.txt` / `*.docx` / `*.md` there
into a **fresh timestamped corpus** (e.g. `202606141530-corpus`) and repoints
`CORPUS_NAME` at it. The previous corpus is left behind (orphaned) — delete the
active one with `delete_corpus.py`, or clean up older ones via the REST list/delete.
(The engine also supports PPTX/HTML if you widen `SUPPORTED_EXTENSIONS`; images are
not supported.)

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
    --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=True,GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests,GOOGLE_CLOUD_LOCATION=us-central1,CORPUS_NAME=<corpus-resource-name>
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

This calls `rag.delete_corpus` (removes files + embeddings) and clears `CORPUS_NAME`
from `.env`, so the agent drops back to plain-chat mode. The default `RagManagedDb`
storage lives in a Google-managed tenant project, so deleting the corpus — not any
action in your own project's console — is what ends the charge.

### Delete ALL corpora (nuke everything)

`delete_corpus.py` only removes the one corpus in `CORPUS_NAME`. Because each
ingestion run creates a fresh timestamped corpus, orphans accumulate — this
gcloud-auth + REST sweep lists every corpus in a region and force-deletes each
(`force=true` also removes its files). Pure shell, no extra deps:

```bash
REGION=us-central1
PROJECT=gcp-cloud-run-tests
TOKEN=$(gcloud auth print-access-token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://$REGION-aiplatform.googleapis.com/v1beta1/projects/$PROJECT/locations/$REGION/ragCorpora" \
  | grep -oE '"name": *"projects/[^"]*/ragCorpora/[^"]*"' \
  | sed -E 's/.*"(projects[^"]*)"/\1/' \
  | while read -r NAME; do
      echo "Deleting $NAME"
      curl -s -X DELETE -H "Authorization: Bearer $TOKEN" \
        "https://$REGION-aiplatform.googleapis.com/v1beta1/$NAME?force=true"
      echo
    done
```

Corpora are per-region, so repeat with `REGION=us-east1` (etc.) for any other
region you used. Confirm it's clean — the list should return `{}`:

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/gcp-cloud-run-tests/locations/us-central1/ragCorpora"
```
