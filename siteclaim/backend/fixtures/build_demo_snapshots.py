"""Pre-record the full pipeline output per demo case, for the frontend's offline
fallback (Phase 6, demo hardening).

Runs extract -> verify -> validate -> draft -> audit in DEMO_MODE (zero network)
for each case and writes ``frontend/src/demo/<case>.json`` — the exact shape the
React app accumulates (facts, validity, review_flags, judge_summary, draft,
audit). Timestamps are normalised to a fixed value so the output is **byte-for-byte
reproducible**: re-running this script leaves the committed files unchanged.

    cd backend && python fixtures/build_demo_snapshots.py
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ.setdefault("DEMO_MODE", "true")  # offline before importing the client

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

from rules_engine.engine import run_validation  # noqa: E402
from schemas.models import SourceMaterial  # noqa: E402

from pipeline.stage_01_extract.extract import extract_facts  # noqa: E402
from pipeline.stage_02_validate.verify import verify_extraction  # noqa: E402
from pipeline.stage_03_draft.draft import draft_claim  # noqa: E402
from pipeline.stage_04_audit.audit import audit_claim  # noqa: E402

TODAY = date(2026, 3, 2)
CASES = ("clean", "messy", "gotcha")
_FIXED_TS = "2026-03-02T00:00:00+00:00"  # normalise non-deterministic timestamps
_OUT = _BACKEND.parent / "frontend" / "src" / "demo"


def _normalise(obj: object) -> object:
    """Replace every ``*_at`` timestamp with a fixed value so output is stable."""
    if isinstance(obj, dict):
        return {
            k: (_FIXED_TS if k in ("generated_at", "computed_at") and v is not None else _normalise(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_normalise(x) for x in obj]
    return obj


def _snapshot(case_id: str) -> dict:
    source = SourceMaterial.model_validate_json(
        (_BACKEND / "fixtures" / "cases" / case_id / "source.json").read_text(encoding="utf-8")
    )
    review = verify_extraction(source, extract_facts(source))
    facts = review.facts
    validity = run_validation(facts, TODAY)
    draft = draft_claim(facts, validity)
    audit = audit_claim(facts, validity, draft, TODAY)
    snap = {
        "case_id": case_id,
        "facts": json.loads(facts.model_dump_json()),
        "validity": json.loads(validity.model_dump_json()),
        "review_flags": [json.loads(f.model_dump_json()) for f in review.review_flags],
        "judge_summary": review.summary,
        "draft": json.loads(draft.model_dump_json()),
        "audit": json.loads(audit.model_dump_json()),
    }
    return _normalise(snap)  # type: ignore[return-value]


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    for case_id in CASES:
        path = _OUT / f"{case_id}.json"
        path.write_text(json.dumps(_snapshot(case_id), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(_BACKEND.parent)}")


if __name__ == "__main__":
    main()
