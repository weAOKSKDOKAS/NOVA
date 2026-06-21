"""API wiring — the five stage routes, the xlsx download, and the demo loaders,
exercised end to end through FastAPI's TestClient in DEMO_MODE (offline)."""

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health_reports_demo_mode():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_stage_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert {"/ingest", "/shortlist", "/dispatch", "/level", "/recommend", "/leveling.xlsx"} <= paths
    assert {"/ingest-upload", "/demo/cases", "/demo/{case_id}"} <= paths


def test_demo_loaders_return_tender_and_replies():
    cases = client.get("/demo/cases").json()
    assert any(c["id"] == "kwun-tong" and c["hero_trade"] == "electrical" for c in cases)
    case = client.get("/demo/kwun-tong").json()
    assert case["tender"]["documents"]
    assert len(case["replies"]) == 4
    assert client.get("/demo/nope").status_code == 404


def test_full_pipeline_through_the_api_catches_the_hero():
    case = client.get("/demo/kwun-tong").json()

    scope = client.post("/ingest", json={"tender": case["tender"]}).json()
    assert "electrical" in {p["trade"] for p in scope["packages"]}

    shortlist = client.post("/shortlist", json={"scope": scope}).json()
    electrical = shortlist["per_trade"]["electrical"]
    assert electrical[0]["firm"]["firm_id"] == "F-EL-02"
    gotcha = next(c for c in electrical if c["firm"]["firm_id"] == "F-EL-01")
    assert gotcha["recommended_against"] is True

    dispatch = client.post("/dispatch", json={
        "shortlist": shortlist, "approvals": {"electrical": ["F-EL-02"]},
        "scope": scope, "project_name": case["name"], "send": True,
    }).json()
    assert {b["firm_id"] for b in dispatch["bundles"]} == {"F-EL-02"}
    assert dispatch["bundles"][0]["status"] == "sent_mock"

    levelled = client.post("/level", json={"replies": case["replies"], "scope": scope}).json()
    messy = next(b for b in levelled if b["firm_id"] == "F-EL-03")
    assert messy["arithmetic_findings"] and messy["scope_gaps"]

    rec = client.post("/recommend", json={"levelled": levelled, "trade": "electrical"}).json()
    assert rec["recommended_firm_id"] == "F-EL-02"
    against = next(r for r in rec["ranked"] if r["firm_id"] == "F-EL-01")
    assert against["recommended_against"] is True
    assert rec["historical_band"] is not None


def test_leveling_xlsx_downloads():
    resp = client.get("/leveling.xlsx")
    assert resp.status_code == 200
    assert "spreadsheet" in resp.headers["content-type"]
    assert resp.content[:2] == b"PK"  # xlsx is a zip
