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

if not PROJECT_ID or not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in .env."
    )


def main():
    credentials, _ = default()
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

    # Delete the corpus the agent currently points at (the one in CORPUS_NAME).
    corpus_name = os.getenv("CORPUS_NAME")
    if not corpus_name:
        print(
            "CORPUS_NAME is not set in .env, so there's no active corpus to delete.\n"
            "List/clean up older corpora via the REST API (see README)."
        )
        return

    # rag.delete_corpus won't delete a non-empty corpus (the SDK doesn't pass
    # force=True), so remove the files first, then delete the now-empty corpus.
    files = list(rag.list_files(corpus_name=corpus_name))
    print(f"Deleting {len(files)} file(s) from corpus {corpus_name}...")
    for f in files:
        rag.delete_file(name=f.name)
        print(f"  deleted {f.display_name}")

    rag.delete_corpus(name=corpus_name)
    print("Corpus deleted (files + embeddings removed).")

    # Clear the stale id so the agent goes back to plain-chat mode.
    unset_key(ENV_FILE_PATH, "CORPUS_NAME")
    print(f"Removed CORPUS_NAME from {ENV_FILE_PATH}")

    print("\nRemaining corpora in this project/location:")
    remaining = list(rag.list_corpora())
    if not remaining:
        print("  (none)")
    for corpus in remaining:
        print(f"  {corpus.display_name} - {corpus.name}")


if __name__ == "__main__":
    main()
