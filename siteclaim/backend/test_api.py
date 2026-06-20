"""API contract tests (offline): the four stage endpoints chain end to end.

Mirrors what the frontend does — each endpoint consumes the previous step's
output — and pins the two headline outcomes: clean -> fileable, gotcha ->
not_fileable on the notice defect.
"""

import os

os.environ["DEMO_MODE"] = "true"  # offline: stages read canned fixtures, zero network

from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402

client = TestClient(api.app)


def _fatal_checks(validity: dict) -> list[str]:
    return [c["name"] for c in validity["checks"] if c["severity"] == "fatal" and not c["passed"]]


def _run(case_id: str) -> dict:
    """Drive extract -> verify -> draft -> audit for a demo case; return the audit."""
    source = client.get(f"/demo/{case_id}").json()
    facts = client.post("/extract", json=source).json()
    verify = client.post("/verify", json={"facts": facts, "case_id": case_id}).json()
    draft = client.post("/draft", json={"facts": verify["facts"], "validity": verify["validity"]}).json()
    audit = client.post(
        "/audit",
        json={"facts": verify["facts"], "validity": verify["validity"], "draft": draft},
    ).json()
    return {"verify": verify, "draft": draft, "audit": audit}


def test_health_reports_offline():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_demo_cases_lists_the_three_fixtures():
    ids = {c["case_id"] for c in client.get("/demo/cases").json()}
    assert {"clean", "messy", "gotcha"} <= ids


def test_unknown_demo_case_is_404():
    assert client.get("/demo/does-not-exist").status_code == 404


def test_extract_upload_in_demo_replays_the_fixture():
    # DEMO_MODE: the uploaded bytes are ignored (no vision call); the case_id
    # fixture is replayed, so this stays offline and needs no PDF tooling.
    files = {"files": ("invoice.pdf", b"%PDF-1.4 not really a pdf", "application/pdf")}
    res = client.post("/extract-upload", files=files, data={"case_id": "clean", "description": "x"})
    assert res.status_code == 200
    assert res.json()["claimed_amount"]["value"] == "1250000.00"


def test_extract_upload_in_demo_without_case_id_is_400():
    files = {"files": ("invoice.pdf", b"%PDF-1.4 not really a pdf", "application/pdf")}
    res = client.post("/extract-upload", files=files)
    assert res.status_code == 400


def test_clean_flow_is_fileable():
    out = _run("clean")
    assert _fatal_checks(out["verify"]["validity"]) == []
    assert out["audit"]["verdict"] == "fileable"


def test_messy_flow_is_fileable_with_fixes():
    out = _run("messy")
    assert out["verify"]["review_flags"]  # the judge flagged low-confidence fields
    assert out["audit"]["verdict"] == "fileable_with_fixes"


def test_gotcha_flow_is_not_fileable_on_the_notice_defect():
    out = _run("gotcha")
    assert "notice.correct_party" in _fatal_checks(out["verify"]["validity"])
    assert out["audit"]["verdict"] == "not_fileable"
    fatal = [f for f in out["audit"]["findings"] if f["severity"] == "fatal"]
    assert any(f["location"] == "notice.correct_party" for f in fatal)


def test_editing_a_fact_flows_through_to_a_clean_verdict():
    # The ICM review-gate promise: fix the wrong served-on party at the facts gate
    # and the downstream verdict changes from not_fileable to fileable.
    source = client.get("/demo/gotcha").json()
    facts = client.post("/extract", json=source).json()
    facts["service"]["served_on"]["value"] = facts["parties"]["respondent"]["value"]["name"]
    verify = client.post("/verify", json={"facts": facts, "case_id": "gotcha"}).json()
    assert _fatal_checks(verify["validity"]) == []
    draft = client.post("/draft", json={"facts": verify["facts"], "validity": verify["validity"]}).json()
    audit = client.post(
        "/audit", json={"facts": verify["facts"], "validity": verify["validity"], "draft": draft}
    ).json()
    assert audit["verdict"] == "fileable"
