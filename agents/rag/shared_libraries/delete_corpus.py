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

"""Tear down the RAG corpus created by prepare_corpus_and_data.py.

Deleting the corpus removes its files and embeddings, which is what stops the
managed-storage cost. Run this when you are done experimenting:

    python agents/rag/shared_libraries/delete_corpus.py
"""

import os

import vertexai
from dotenv import load_dotenv, unset_key
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
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
CORPUS_DISPLAY_NAME = "Alphabet_10K_2025_corpus"

if not PROJECT_ID or not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in .env."
    )


def main():
    credentials, _ = default()
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

    # Prefer the exact resource name written to .env; fall back to display name.
    corpus_name = os.getenv("RAG_CORPUS")
    if not corpus_name:
        for corpus in rag.list_corpora():
            if corpus.display_name == CORPUS_DISPLAY_NAME:
                corpus_name = corpus.name
                break

    if not corpus_name:
        print("No corpus found to delete (RAG_CORPUS unset and no match by name).")
        return

    print(f"Deleting corpus: {corpus_name}")
    rag.delete_corpus(name=corpus_name)
    print("Corpus deleted (files + embeddings removed).")

    # Clear the stale id so the agent goes back to plain-chat mode.
    unset_key(ENV_FILE_PATH, "RAG_CORPUS")
    print(f"Removed RAG_CORPUS from {ENV_FILE_PATH}")

    print("\nRemaining corpora in this project/location:")
    remaining = list(rag.list_corpora())
    if not remaining:
        print("  (none)")
    for corpus in remaining:
        print(f"  {corpus.display_name} - {corpus.name}")


if __name__ == "__main__":
    main()
