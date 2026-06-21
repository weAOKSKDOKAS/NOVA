"""Stage 02 shortlist — the hero. Clean runner-up on top, gotcha demoted with
citable fatal evidence. Hermetic: builds its own offline seed, no network."""

import pytest

from db import seed, store
from pipeline.stage_01_ingest.ingest import ingest_tender
from pipeline.stage_02_shortlist.shortlist import shortlist
from schemas.models import Severity, ShortlistSet, TenderPackage

_FIXTURE = "cases/clean/scope_packages.json"


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("shortlist") / "test.db"
    seed.build_database(db_path)
    connection = store.get_connection(db_path)
    yield connection
    connection.close()


@pytest.fixture
def shortlisted(conn) -> ShortlistSet:
    scope = ingest_tender(TenderPackage(project_name="demo", description=""), demo_fixture=_FIXTURE)
    return shortlist(scope, conn=conn)


def test_shortlist_covers_every_trade(shortlisted):
    assert {"electrical", "mechanical_plumbing", "fire_services", "joinery_fitting_out"} <= set(
        shortlisted.per_trade
    )
    assert all(cands for cands in shortlisted.per_trade.values())  # no empty trade


def test_electrical_top_is_the_clean_runner_up(shortlisted):
    electrical = shortlisted.per_trade["electrical"]
    top = electrical[0]
    assert top.firm.firm_id == "F-EL-02"
    assert top.recommended_against is False
    assert not [f for f in top.risk_flags if f.severity is Severity.FATAL]


def test_gotcha_present_but_recommended_against_with_evidence(shortlisted):
    electrical = shortlisted.per_trade["electrical"]
    gotcha = next(c for c in electrical if c.firm.firm_id == "F-EL-01")
    # present, but demoted to the bottom and flagged
    assert gotcha.recommended_against is True
    assert electrical[-1].firm.firm_id == "F-EL-01"
    # the fatal winding-up flag is attached and citable
    winding = next(f for f in gotcha.risk_flags if f.rule_ref == "risk.winding_up")
    assert winding.severity is Severity.FATAL
    assert winding.evidence[0].source == "Companies Registry"
    assert winding.evidence[0].reference == "CR:HCCW-215/2026"
    # and it is a strong match — the demotion is the risk engine, not a weak score
    assert gotcha.match_score > 0.4


def test_gotcha_outranks_a_clean_firm_on_match_yet_is_below_it(shortlisted):
    electrical = shortlisted.per_trade["electrical"]
    gotcha = next(c for c in electrical if c.firm.firm_id == "F-EL-01")
    above_gotcha = electrical[: electrical.index(gotcha)]
    assert any(c.match_score < gotcha.match_score for c in above_gotcha)
