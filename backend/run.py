"""Convenience launcher: ``python run.py`` starts the API (and builds the
analysis on first run).  Equivalent to ``uvicorn app.main:app``.
"""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.environ.get("AV_HOST", "127.0.0.1"),
        port=int(os.environ.get("AV_PORT", "8000")),
        reload=os.environ.get("AV_RELOAD", "0") == "1",
    )
