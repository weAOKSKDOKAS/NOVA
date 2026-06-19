"""SiteClaim HTTP API — scaffold only (stage logic lands in later phases).

Run from the ``backend/`` directory::

    uvicorn api:app --reload

The pipeline itself is filesystem-first (see ``../CLAUDE.md`` and
``../CONTEXT.md``); this API is a thin entry point that will, in later phases,
drive the five numbered stages under ``./pipeline``. For now it exposes a health
check, surfaces the statutory warning, and sketches one endpoint per stage so the
typed contract is visible. Each pipeline endpoint returns HTTP 501 until its
stage is implemented.
"""

from fastapi import FastAPI, HTTPException, status

from rules_engine import cisop_config
from schemas.models import (
    AuditReport,
    ClaimDraft,
    DeadlineSet,
    ExtractedFacts,
    SourceMaterial,
    ValidityReport,
)

app = FastAPI(
    title="SiteClaim API",
    version="0.0.0",
    description="CISOP-compliant payment-claim drafting copilot (scaffold).",
)


def _not_implemented(stage: str) -> None:
    """Uniform 501 for pipeline endpoints that are scaffolded but not wired up."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{stage} is scaffolded but not yet implemented (Phase 0).",
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe with the active statutory-config version."""
    return {"status": "ok", "config_version": cisop_config.CONFIG_VERSION}


@app.get("/legal-notice")
def legal_notice() -> dict[str, str]:
    """Surface the statutory warning so no client can hide it from the user."""
    return {"warning": cisop_config.STATUTORY_WARNING, "source": cisop_config.STATUTORY_SOURCE}


# --- Pipeline endpoints (one per numbered stage; NOT YET IMPLEMENTED) -------
@app.post("/claims/extract", response_model=ExtractedFacts)
def extract(source: SourceMaterial) -> ExtractedFacts:  # noqa: ARG001
    """Stage 01 (Layer 2) — read ``SourceMaterial`` into ``ExtractedFacts``."""
    _not_implemented("stage_01_extract")
    raise AssertionError("unreachable")  # pragma: no cover


@app.post("/claims/validate", response_model=ValidityReport)
def validate(facts: ExtractedFacts) -> ValidityReport:  # noqa: ARG001
    """Stage 02 (Layer 1) — run the statutory checks over ``ExtractedFacts``."""
    _not_implemented("stage_02_validate")
    raise AssertionError("unreachable")  # pragma: no cover


@app.post("/claims/deadlines", response_model=DeadlineSet)
def deadlines(facts: ExtractedFacts) -> DeadlineSet:  # noqa: ARG001
    """Stage 02 (Layer 1) — compute the CISOP deadline set for the claim."""
    _not_implemented("stage_02_validate")
    raise AssertionError("unreachable")  # pragma: no cover


@app.post("/claims/draft", response_model=ClaimDraft)
def draft(facts: ExtractedFacts) -> ClaimDraft:  # noqa: ARG001
    """Stage 03 (Layer 2 + 3) — draft the claim from validated facts."""
    _not_implemented("stage_03_draft")
    raise AssertionError("unreachable")  # pragma: no cover


@app.post("/claims/audit", response_model=AuditReport)
def audit(draft_doc: ClaimDraft) -> AuditReport:  # noqa: ARG001
    """Stage 04 (Layer 1 + 2) — cross-check the draft against the facts."""
    _not_implemented("stage_04_audit")
    raise AssertionError("unreachable")  # pragma: no cover


@app.post("/claims/review", response_model=ClaimDraft)
def review(draft_doc: ClaimDraft) -> ClaimDraft:  # noqa: ARG001
    """Stage 05 (Layer 4) — record the human approve/edit/reject decision."""
    _not_implemented("stage_05_review")
    raise AssertionError("unreachable")  # pragma: no cover
