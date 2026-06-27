# syntax=docker/dockerfile:1
#
# Wiki agent image. BUILD FROM THE REPO ROOT (context must be the root so that
# requirements.txt is reachable — COPY cannot climb above the context):
#
#   docker build -f agents/wiki/Dockerfile -t wiki-agent .
#
# No .env is baked in (see /.dockerignore). Inject config at `docker run` time.

# ---- builder: install deps into an isolated prefix ----
FROM python:3.14-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime: slim image with only the installed packages + agent code ----
FROM python:3.14-slim
# Non-root user for the running process
RUN useradd --system --create-home --home-dir /home/appuser appuser
WORKDIR /app

# Bring in installed packages and console scripts (the `adk` CLI) from builder.
# --chown so the non-root user owns them: `adk web` writes a runtime-config.json
# into its own package dir at startup, which fails if the packages are root-owned.
COPY --chown=appuser:appuser --from=builder /install /usr/local

# Wiki app only. It ships its own `shared/` subpackage, so nothing else is needed.
COPY agents/wiki/ agents/wiki/

# Let the non-root user write the ADK session DB it creates under the app dir
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# `agents` is scanned for apps; this image contains only wiki, so the picker
# shows just wiki. --host 0.0.0.0 makes it reachable from outside the container.
CMD ["adk", "web", "agents", "--host", "0.0.0.0", "--port", "8000"]
