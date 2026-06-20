"""The frontend's offline fallback snapshots must stay byte-for-byte in sync with
the pipeline (Phase 6). Regenerate with ``python fixtures/build_demo_snapshots.py``.
"""

import importlib.util
import json
import os
from pathlib import Path

os.environ["DEMO_MODE"] = "true"  # offline; the snapshot builder also defaults this

_BACKEND = Path(__file__).resolve().parent
_DEMO = _BACKEND.parent / "frontend" / "src" / "demo"

_spec = importlib.util.spec_from_file_location(
    "build_demo_snapshots", _BACKEND / "fixtures" / "build_demo_snapshots.py"
)
assert _spec and _spec.loader
bds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bds)


def test_snapshots_match_the_pipeline_byte_for_byte():
    for case_id in bds.CASES:
        committed = json.loads((_DEMO / f"{case_id}.json").read_text(encoding="utf-8"))
        rebuilt = bds._snapshot(case_id)
        assert rebuilt == committed, f"{case_id}.json drifted — re-run fixtures/build_demo_snapshots.py"


def test_snapshot_verdicts_span_the_spectrum():
    assert bds._snapshot("clean")["audit"]["verdict"] == "fileable"
    assert bds._snapshot("messy")["audit"]["verdict"] == "fileable_with_fixes"
    assert bds._snapshot("gotcha")["audit"]["verdict"] == "not_fileable"
