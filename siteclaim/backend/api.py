"""SiteClaim HTTP API — one endpoint per pipeline stage (Phase 5).

Run from the ``backend/`` directory::

    DEMO_MODE=true uvicorn api:app --reload

The pipeline is filesystem-first (see ``../CLAUDE.md``); this API is a thin driver
over the five numbered stages under ``./pipeline``. Crucially there is NO single
``/run`` endpoint: each stage is its own POST, and every stage accepts the
(possibly human-edited) output of the previous stage as input. That enforces the
ICM review-gate pattern — a person can edit between every stage, and the next
stage consumes exactly what they left.

``DEMO_MODE`` is respected end-to-end: when on, the LLM stages read canned
fixtures (by ``case_id``) and make zero network calls.
"""

from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rules_engine import sopo_config
from rules_engine.engine import run_validation
from schemas.models import (
    AuditReport,
    ClaimDraft,
    ExtractedFacts,
    ReviewFlag,
    SourceMaterial,
    ValidityReport,
)

from pipeline.llm_client import demo_mode
from pipeline.stage_01_extract.extract import extract_facts
from pipeline.stage_02_validate.verify import verify_extraction
from pipeline.stage_03_draft.draft import draft_claim
from pipeline.stage_04_audit.audit import audit_claim

# In DEMO_MODE the fixtures are anchored to this date (served 2026-03-02), so the
# deadline clock reads sensibly; live requests fall back to the real today.
DEMO_TODAY = date(2026, 3, 2)
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cases"

DEMO_CASES = (
    ("clean", "Clean case", "A straightforward, well-documented claim — extracts cleanly and files."),
    ("messy", "Messy case", "Vague figures and dates — low-confidence extraction that needs review."),
    ("gotcha", "Gotcha case", "Served on the wrong legal entity — a fatal notice defect the audit catches."),
)

app = FastAPI(
    title="SiteClaim API",
    version="1.0.0",
    description="SOPO-compliant payment-claim drafting copilot — one endpoint per review gate.",
)

# Permissive CORS for local dev (Vite on :5173 etc.).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_today(override: Optional[date]) -> date:
    if override is not None:
        return override
    return DEMO_TODAY if demo_mode() else date.today()


# ---------------------------------------------------------------------------
# Request / response envelopes (each carries the prior stage's edited output)
# ---------------------------------------------------------------------------
class VerifyRequest(BaseModel):
    facts: ExtractedFacts
    case_id: Optional[str] = None  # locates the canned judge verdict in DEMO_MODE
    source_description: Optional[str] = None  # feeds the judge on the live path
    today: Optional[date] = None


class VerifyResponse(BaseModel):
    facts: ExtractedFacts  # confidence-adjusted by the judge
    validity: ValidityReport
    review_flags: list[ReviewFlag] = Field(default_factory=list)
    judge_summary: str = ""


class DraftRequest(BaseModel):
    facts: ExtractedFacts
    validity: ValidityReport


class AuditRequest(BaseModel):
    facts: ExtractedFacts
    validity: ValidityReport
    draft: ClaimDraft
    today: Optional[date] = None


class DemoCase(BaseModel):
    case_id: str
    label: str
    description: str


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, object]:
    """Liveness probe: config version + whether the server is offline (DEMO_MODE)."""
    return {
        "status": "ok",
        "config_version": sopo_config.CONFIG_VERSION,
        "demo_mode": demo_mode(),
    }


@app.get("/legal-notice")
def legal_notice() -> dict[str, str]:
    """The statutory warning, surfaced so no client can hide it from the user."""
    return {"warning": sopo_config.STATUTORY_WARNING, "source": sopo_config.STATUTORY_SOURCE}


@app.get("/demo/cases", response_model=list[DemoCase])
def demo_cases() -> list[DemoCase]:
    """The demo fixtures available to load (clean / messy / gotcha)."""
    cases: list[DemoCase] = []
    for case_id, label, blurb in DEMO_CASES:
        path = _FIXTURES / case_id / "source.json"
        description = blurb
        if path.is_file():
            description = SourceMaterial.model_validate_json(path.read_text(encoding="utf-8")).description
        cases.append(DemoCase(case_id=case_id, label=label, description=description))
    return cases


@app.get("/demo/{case_id}", response_model=SourceMaterial)
def demo_case(case_id: str) -> SourceMaterial:
    """Load a demo fixture's SourceMaterial (so the UI can populate the input box)."""
    path = _FIXTURES / case_id / "source.json"
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"unknown demo case: {case_id!r}")
    return SourceMaterial.model_validate_json(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Pipeline — one POST per stage; each consumes the prior (edited) output
# ---------------------------------------------------------------------------
@app.post("/extract", response_model=ExtractedFacts)
def extract(source: SourceMaterial) -> ExtractedFacts:
    """Stage 01 (Layer 2) — read raw source material into typed ExtractedFacts."""
    return extract_facts(source)


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest) -> VerifyResponse:
    """Stage 02 — LLM-as-judge (confidence) + deterministic engine (validity).

    Consumes the (possibly edited) facts from Stage 01. Re-judges confidence and
    runs the statutory checks, returning the adjusted facts, the ValidityReport
    (with the deadline clock), and the fields flagged for human review.
    """
    source = SourceMaterial(case_id=req.case_id, description=req.source_description or "")
    review = verify_extraction(source, req.facts)
    report = run_validation(review.facts, _resolve_today(req.today))
    return VerifyResponse(
        facts=review.facts,
        validity=report,
        review_flags=review.review_flags,
        judge_summary=review.summary,
    )


@app.post("/draft", response_model=ClaimDraft)
def draft(req: DraftRequest) -> ClaimDraft:
    """Stage 03 (Layer 2 + 3) — draft the claim from the (edited) facts + validity."""
    return draft_claim(req.facts, req.validity)


@app.post("/audit", response_model=AuditReport)
def audit(req: AuditRequest) -> AuditReport:
    """Stage 04 (Layer 1 + thin Layer 2) — forensic cross-check + verdict."""
    return audit_claim(req.facts, req.validity, req.draft, _resolve_today(req.today))
