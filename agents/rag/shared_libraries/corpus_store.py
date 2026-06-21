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

"""Single source of truth for which corpus the rag agent points at.

The corpus resource name is stored in agents/rag/.corpus_data (next to the
agent), NOT in the shared root .env — the rag agent owns this file so it never
edits config belonging to the other agents. The ingestion script writes it, the
agent reads it, and delete_corpus.py clears it.
"""

import os

# agents/rag/.corpus_data, resolved relative to this file (shared_libraries/..)
CORPUS_DATA_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".corpus_data")
)


def read_corpus_name():
    """Return the stored corpus resource name, or None if not set."""
    try:
        with open(CORPUS_DATA_FILE, encoding="utf-8") as f:
            name = f.read().strip()
    except FileNotFoundError:
        return None
    return name or None


def write_corpus_name(corpus_name):
    """Record the corpus the agent should use."""
    with open(CORPUS_DATA_FILE, "w", encoding="utf-8") as f:
        f.write(corpus_name + "\n")


def clear_corpus_name():
    """Remove the stored pointer (agent falls back to plain-chat mode)."""
    try:
        os.remove(CORPUS_DATA_FILE)
    except FileNotFoundError:
        pass
