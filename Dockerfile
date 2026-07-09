FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST_ONLY_CANARY=parent-only-not-a-secret \
    MODEL=gemini-3.5-flash \
    PORT=8080

# Required only while ADK is pinned to an exact, unreleased upstream commit.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY sandbox_analyst ./sandbox_analyst
COPY samples ./samples
RUN pip install --upgrade pip \
    && pip install .

EXPOSE 8080
CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT} --log_level INFO --no-reload --session_service_uri memory:// --artifact_service_uri memory:// --allow_origins http://localhost:8080 --allow_origins http://127.0.0.1:8080 ."]
