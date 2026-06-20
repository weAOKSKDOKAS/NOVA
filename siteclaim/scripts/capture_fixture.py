#!/usr/bin/env python3
"""Capture a real upload as a replayable DEMO_MODE fixture (Phase 7 — video safety net).

Runs the LIVE pipeline (extract → judge → validate → draft → audit) on real files
for a case id, then writes the exact LLM-stage outputs + the rasterised images into
``backend/fixtures/cases/<case_id>/`` so that case replays BYTE-FOR-BYTE offline.
Finally it re-runs the same case in DEMO_MODE to prove the replay and print the
verdict, so you can run a real invoice through DeepSeek ONCE, lock a clean result,
and record the demo offline and reproducibly.

    python scripts/capture_fixture.py <case_id> <file1> [file2 ...]

Requires the live provider configured (EXTRACTION_PROVIDER, DEEPSEEK_API_KEY) and
DEMO_MODE unset.
"""

import base64
import json
import mimetypes
import os
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

from pipeline.documents import to_images  # noqa: E402
from pipeline.llm_client import demo_mode, extraction_provider  # noqa: E402
from schemas.models import ShipmentDocs, SourceMaterial, UploadedFile  # noqa: E402

DEMO_TODAY = date(2026, 3, 2)


def _die(msg: str, code: int = 2) -> int:
    print(msg, file=sys.stderr)
    return code


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _die("usage: python scripts/capture_fixture.py <case_id> <file1> [file2 ...]")
    case_id, file_paths = argv[0], argv[1:]

    if demo_mode():
        return _die("DEMO_MODE is on — unset it; capture needs the LIVE provider.")
    provider = extraction_provider()
    if provider == "deepseek" and not os.getenv("DEEPSEEK_API_KEY"):
        return _die("DEEPSEEK_API_KEY is not set (EXTRACTION_PROVIDER=deepseek).")

    # --- live extraction + judge over the real documents --------------------
    from pipeline.stage_01_extract.extract import extract_facts
    from pipeline.stage_02_validate.verify import judge_extraction

    images: list[str] = []
    docs: list[UploadedFile] = []
    for path_str in file_paths:
        path = Path(path_str)
        if not path.is_file():
            return _die(f"no such file: {path}")
        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        images.extend(to_images(data, content_type))
        docs.append(UploadedFile(filename=path.name, content_type=content_type, size_bytes=len(data)))

    source = SourceMaterial(
        case_id=case_id,
        description=f"Captured from {', '.join(p.name for p in map(Path, file_paths))}.",
        docs=ShipmentDocs(files=docs),
    )

    print(f"→ provider={provider} model is live; reading {len(images)} page image(s)…")
    facts = extract_facts(source, images=images)
    verdict = judge_extraction(source, facts, images=images)

    # --- write the fixtures -------------------------------------------------
    case_dir = _BACKEND / "fixtures" / "cases" / case_id
    (case_dir / "images").mkdir(parents=True, exist_ok=True)
    (case_dir / "source.json").write_text(source.model_dump_json(indent=2), encoding="utf-8")
    (case_dir / "extracted.json").write_text(facts.model_dump_json(indent=2), encoding="utf-8")
    (case_dir / "verdict.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    for i, b64 in enumerate(images, start=1):
        (case_dir / "images" / f"page-{i:02d}.png").write_bytes(base64.b64decode(b64))
    print(f"→ wrote {case_dir.relative_to(_ROOT)}/ (source, extracted, verdict, {len(images)} image(s))")

    # --- prove the offline replay: re-run the SAME case in DEMO_MODE --------
    os.environ["DEMO_MODE"] = "true"
    from rules_engine.engine import run_validation
    from pipeline.stage_02_validate.verify import verify_extraction
    from pipeline.stage_03_draft.draft import draft_claim
    from pipeline.stage_04_audit.audit import audit_claim

    replay = verify_extraction(source, extract_facts(source))  # loads the just-written fixtures
    report = run_validation(replay.facts, DEMO_TODAY)
    draft = draft_claim(replay.facts, report)
    audit = audit_claim(replay.facts, report, draft, DEMO_TODAY)
    print("→ DEMO_MODE replay (offline):")
    print(f"    validity: {'VALID' if report.is_valid else 'INVALID'}  |  audit verdict: {audit.verdict.value.upper()}")
    print(f"    review flags: {len(replay.review_flags)}  |  findings: {len(audit.findings)}")
    print(f'✓ case "{case_id}" now replays byte-for-byte in DEMO_MODE.')
    if case_id in ("clean", "messy", "gotcha"):
        print("  (refresh the frontend snapshot with: make snapshots)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
