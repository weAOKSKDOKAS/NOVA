"""SiteSource HTTP API — thin driver over the five-stage pipeline.

Stripped to a health check during the pivot; the one-POST-per-stage routes
(/ingest, /shortlist, /dispatch, /level, /recommend, /leveling.xlsx) and the
multipart upload route are rebuilt in Phase 8. The chassis pattern is preserved:
``.env`` is auto-loaded before anything reads env, DEMO_MODE is respected, and
CORS is permissive for local dev.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")  # before anything reads env

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from pipeline.llm_client import demo_mode  # noqa: E402

app = FastAPI(
    title="SiteSource API",
    version="0.1.0",
    description="AI subcontractor-sourcing and bid-leveling platform (pivot in progress).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    """Liveness probe; reports whether the server is offline (DEMO_MODE)."""
    return {"status": "ok", "demo_mode": demo_mode()}
