# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build a single RAG corpus from every document in agents/rag/rag_materials/.

Drop .pdf / .txt / .docx / .md files into agents/rag/rag_materials/ and run:

    python agents/rag/shared_libraries/prepare_corpus_and_data.py

Each run creates a fresh, timestamped corpus (e.g. 202606141530-corpus) from
every document in rag_materials/ (their union = the knowledge base), writes its
resource name to CORPUS_NAME in .env, and the agent reads CORPUS_NAME to point at
it. Within a run, uploads are retried and de-duplicated on connection resets.

Note: each run leaves the previous corpus behind (orphaned). Delete the active
one with delete_corpus.py, or clean up older ones via the REST list/delete.
"""

import glob
import os
import time
from datetime import datetime

import vertexai
from dotenv import load_dotenv, set_key
from google.api_core.exceptions import ResourceExhausted
from google.auth import default
from vertexai.preview import rag

cwd_env = os.path.join(os.getcwd(), ".env")
if os.path.exists(cwd_env):
    ENV_FILE_PATH = cwd_env
else:
    # repo root is three levels up: shared_libraries -> rag -> agents -> root
    ENV_FILE_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    )
load_dotenv(ENV_FILE_PATH)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable not set. Please set it in your .env file."
    )
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
if not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_LOCATION environment variable not set. Please set it in your .env file."
    )

# A fresh, uniquely-named corpus is created on every run; its resource name is
# written to CORPUS_NAME in .env, and that is what the agent reads to point at it.
CORPUS_DESCRIPTION = "Knowledge base built from the documents in agents/rag/rag_materials/"
# agents/rag/rag_materials, resolved relative to this file (shared_libraries/..)
MATERIALS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "rag_materials")
)
# text-like documents only (no slides/images); the RAG Engine default parser
# handles all of these.
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}
UPLOAD_ATTEMPTS = 3


def initialize_vertex_ai():
    credentials, _ = default()
    vertexai.init(
        project=PROJECT_ID, location=LOCATION, credentials=credentials
    )


def create_corpus():
    """Create a fresh, uniquely-named corpus for this run."""
    display_name = datetime.now().strftime("%Y%m%d%H%M") + "-corpus"
    embedding_model_config = rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-004"
    )
    corpus = rag.create_corpus(
        display_name=display_name,
        description=CORPUS_DESCRIPTION,
        embedding_model_config=embedding_model_config,
    )
    print(f"Created new corpus '{display_name}' ({corpus.name})")
    return corpus


def discover_materials():
    """Returns sorted absolute paths of supported docs in rag_materials/."""
    paths = [
        p
        for p in glob.glob(os.path.join(MATERIALS_DIR, "*"))
        if os.path.isfile(p)
        and os.path.splitext(p)[1].lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(paths)


def existing_display_names(corpus_name):
    return {f.display_name for f in rag.list_files(corpus_name=corpus_name)}


def upload_one(corpus_name, path):
    """Upload a single file into the corpus, idempotent + retrying.

    Re-checks the corpus before each attempt: this both skips files that are
    already present and absorbs the case where a previous upload landed
    server-side even though the client saw a connection reset (which is how we
    previously ended up with duplicate copies).
    """
    display_name = os.path.basename(path)
    for attempt in range(1, UPLOAD_ATTEMPTS + 1):
        if display_name in existing_display_names(corpus_name):
            print(f"  - {display_name}: already in corpus, skipping")
            return
        try:
            rag.upload_file(
                corpus_name=corpus_name,
                path=path,
                display_name=display_name,
                description=f"Uploaded from rag_materials/{display_name}",
            )
            print(f"  - {display_name}: uploaded")
            return
        except ResourceExhausted as e:
            print(f"  - {display_name}: quota exceeded ({e}).")
            print(
                "    You exceeded the embedding-model quota (common on new projects)."
                " See the README troubleshooting section to request an increase."
            )
            return
        except Exception as e:  # noqa: BLE001 - transient upload/connection errors
            print(f"  - {display_name}: attempt {attempt}/{UPLOAD_ATTEMPTS} failed ({e})")
            if attempt < UPLOAD_ATTEMPTS:
                time.sleep(2)
    print(f"  - {display_name}: gave up after {UPLOAD_ATTEMPTS} attempts")


def update_env_file(corpus_name, env_file_path):
    """Point CORPUS_NAME in .env at the corpus the agent should use."""
    try:
        set_key(env_file_path, "CORPUS_NAME", corpus_name)
        print(f"Updated CORPUS_NAME in {env_file_path} to {corpus_name}")
    except Exception as e:
        print(f"Error updating .env file: {e}")


def list_corpus_files(corpus_name):
    """Lists files in the specified corpus."""
    files = list(rag.list_files(corpus_name=corpus_name))
    print(f"Total files in corpus: {len(files)}")
    for file in files:
        print(f"File: {file.display_name} - {file.name}")


def main():
    initialize_vertex_ai()
    corpus = create_corpus()

    update_env_file(corpus.name, ENV_FILE_PATH)

    materials = discover_materials()
    if not materials:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(
            f"No supported documents ({exts}) found in {MATERIALS_DIR}.\n"
            "Drop some documents there and re-run."
        )
    else:
        print(f"Found {len(materials)} document(s) in {MATERIALS_DIR}:")
        for path in materials:
            upload_one(corpus.name, path)

    list_corpus_files(corpus_name=corpus.name)


if __name__ == "__main__":
    main()
