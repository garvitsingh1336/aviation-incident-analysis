"""FastAPI application entry point.

Exposes the analysis REST API under ``/api`` and, in production, serves the
built React dashboard from ``frontend/dist``.  On startup it ensures the
analysis artifacts exist (building the full pipeline on first run).
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .api.routes import router
from .core.store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build (first run) or load the cached analysis before serving traffic.
    if os.environ.get("AV_SKIP_STARTUP_BUILD") != "1":
        store.ensure_loaded()
    yield


app = FastAPI(
    title="AI-Powered Aviation Incident Analysis",
    description="Discover recurring themes and potential contributing factors "
                "in aviation safety reports using NLP, embeddings, topic "
                "modelling and clustering.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api")
def api_root():
    return {"service": "aviation-incident-analysis", "docs": "/docs"}


# --------------------------------------------------------------------------- #
# Serve the built frontend (if present).  During development the React dev
# server runs separately on :5173 and talks to this API via CORS.
# --------------------------------------------------------------------------- #
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # Serve static files if they exist, else fall back to index.html (SPA).
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
