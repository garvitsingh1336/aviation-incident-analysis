# syntax=docker/dockerfile:1

###############################################################################
# AI-Powered Aviation Incident Analysis — single production container
#
# Multi-stage build:
#   Stage 1 (node)    builds the React / Vite dashboard         -> frontend/dist
#   Stage 2 (python)  installs the full NLP stack, bakes the embedding and
#                     spaCy models into the image, copies the API + built
#                     dashboard + prebuilt analysis artifacts, and serves
#                     everything from ONE FastAPI/uvicorn process on port 8000.
#
# The resulting container serves both the REST API (/api/*) and the SPA from
# the same origin, so no CORS configuration is needed in production.
###############################################################################

# ---- Stage 1: build the React dashboard ------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /build

# Install deps first (cached until the lockfile changes).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Build the static bundle -> /build/dist
COPY frontend/ ./
RUN npm run build


# ---- Stage 2: python runtime ------------------------------------------------
FROM python:3.11-slim AS runtime

# The model/cache dirs live under /app so a non-root user can read them, and so
# live semantic search (and any on-demand rebuild) needs no network at runtime.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers \
    AV_HOST=0.0.0.0 \
    AV_PORT=8000

WORKDIR /app

# build-essential is only needed to compile the hdbscan / umap-learn wheels; it
# is removed in the same layer so it never reaches the final image.
#
# NOTE: this installs the default (Linux) PyTorch wheel from PyPI, which is
# reliable but large. For a much smaller CPU-only image, see the "Slimmer
# CPU-only image" section in README.md.
COPY backend/requirements.txt ./backend/requirements.txt
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential; \
    pip install --upgrade pip; \
    pip install -r backend/requirements.txt; \
    python -m spacy download en_core_web_sm; \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; \
    apt-get purge -y --auto-remove build-essential; \
    rm -rf /var/lib/apt/lists/*

# Application code, prebuilt analysis artifacts, and the built dashboard.
#   backend/       -> FastAPI app + pipeline
#   data_store/    -> analysis.json, embeddings.npy, embedder.pkl, meta.json
#   frontend/dist/ -> built SPA (served by FastAPI)
COPY backend/ ./backend/
COPY data_store/ ./data_store/
COPY --from=frontend /build/dist ./frontend/dist

# All models are cached in the image above -> make the runtime fully offline.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Drop privileges.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness: /api/health returns 200 once the app is up (analysis is loaded in
# the lifespan startup hook before traffic is served).
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

# --app-dir puts backend/ on sys.path so `app.main:app` imports; config.py then
# resolves PROJECT_ROOT to /app, locating data_store/ and frontend/dist/.
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
