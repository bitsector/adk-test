# syntax=docker/dockerfile:1
#
# Voice agent image. BUILD FROM THE REPO ROOT (context must be the root so that
# requirements.txt is reachable — COPY cannot climb above the context):
#
#   docker build -f agents/voice/Dockerfile -t voice-agent .
#
# This agent runs on the Vertex AI backend (the Live API needs Vertex for the
# transparent session resumption adk web hard-wires; see agents/voice/README.md).
# No .env and no SA key are baked in (see /.dockerignore excludes .env + secrets/).
# Inject config and credentials at `docker run` time. Mic capture/playback happen
# in the BROWSER, not here — this is just the adk web server relaying audio over a
# WebSocket to the Gemini Live API, so the container needs no sound devices.
#
# Run (bind-mount the SA key read-only; do NOT use --env-file .env because its
# GOOGLE_APPLICATION_CREDENTIALS is a host path that won't exist in the container):
#
#   docker run --rm -p 8000:8000 \
#     -e GOOGLE_GENAI_USE_VERTEXAI=True \
#     -e GOOGLE_CLOUD_PROJECT=gcp-cloud-run-tests \
#     -e GOOGLE_CLOUD_LOCATION=us-central1 \
#     -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
#     -v "$PWD/secrets/voice-agent-sa-key.json:/secrets/sa.json:ro" \
#     voice-agent
#
# Then open http://localhost:8000 (localhost is a secure context, so the browser
# grants mic access; a remote host would need HTTPS).

# ---- builder: install deps into an isolated prefix ----
# Alpine (musl) base: it ships no perl-base/glibc, so it avoids the Debian-slim
# OS-package CVEs (perl-base, libc6, libsqlite3). All our deps resolve to
# musllinux wheels, so no compiler/build deps are needed here.
FROM python:3.14-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime: slim image with only the installed packages + agent code ----
FROM python:3.14-alpine
# Non-root user for the running process. Alpine's busybox `adduser` has no
# useradd; -S makes a system user, and we create a matching group first so the
# `appuser:appuser` chowns below resolve (a bare `adduser -S` lands in nogroup).
RUN addgroup -S appuser && adduser -S -G appuser -h /home/appuser appuser
WORKDIR /app

# Bring in installed packages and console scripts (the `adk` CLI) from builder.
# --chown so the non-root user owns them: `adk web` writes a runtime-config.json
# into its own package dir at startup, which fails if the packages are root-owned.
COPY --chown=appuser:appuser --from=builder /install /usr/local

# Voice app only. It ships its own `shared/` subpackage (its copy of the
# Wikipedia tool), so nothing outside agents/voice/ is needed.
COPY agents/voice/ agents/voice/

# Let the non-root user write the ADK session DB it creates under the app dir.
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# `agents` is scanned for apps; this image contains only voice, so the picker
# shows just voice. --host 0.0.0.0 makes it reachable from outside the container.
CMD ["adk", "web", "agents", "--host", "0.0.0.0", "--port", "8000"]
