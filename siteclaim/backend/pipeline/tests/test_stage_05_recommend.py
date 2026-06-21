"""Stage 05 recommend — risk-adjusted: the clean runner-up wins, the cheaper gotcha
is recommended against citing its fatal evidence, and the price sits in the band."""

import pytest

from db import seed, store
from pipeline.stage_04_level.level import level_bids, load_demo_replies
from pipeline.stage_05_recommend.recommend import recommend
from schemas.models import Severity

_REPLIES_FIXTURE = "cases/messy/bid_replies.json"
_RATIONALE_FIXTURE = "cases/clean/recommendation_rationale.json"


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("recommend") / "test.db"
    seed.build_database(db_path)
    connection = store.get_connection(db_path)
    yield connection
    connection.close()


@pytest.fixture
def levelled(conn):
    return level_bids(load_demo_replies(_REPLIES_FIXTURE), conn=conn)


@pytest.fixture
def rec(levelled, conn):
    return recommend(levelled, "electrical", demo_fixture=_RATIONALE_FIXTURE, conn=conn)


def test_recommends_the_clean_runner_up(rec):
    assert rec.recommended_firm_id == "F-EL-02"
    winner = next(r for r in rec.ranked if r.firm_id == "F-EL-02")
    assert winner.recommended_against is False
    assert not [f for f in winner.risk_flags if f.severity is Severity.FATAL]


def test_cheapest_gotcha_is_recommended_against_with_cited_evidence(rec):
    gotcha = next(r for r in rec.ranked if r.firm_id == "F-EL-01")
    # it is the cheapest bid by corrected total …
    assert gotcha.corrected_total == min(r.corrected_total for r in rec.ranked)
    # … yet recommended against, citing the winding-up petition and safety prosecutions
    assert gotcha.recommended_against is True
    assert "risk.winding_up" in gotcha.reason
    assert "risk.safety_prosecutions" in gotcha.reason
    fatal_refs = {f.rule_ref for f in gotcha.risk_flags if f.severity is Severity.FATAL}
    assert {"risk.winding_up", "risk.safety_prosecutions"} <= fatal_refs


def test_price_sits_within_the_historical_band(rec):
    assert rec.historical_band is not None
    winner = next(r for r in rec.ranked if r.firm_id == rec.recommended_firm_id)
    assert rec.historical_band.low <= winner.corrected_total <= rec.historical_band.high


def test_bid_distribution_and_rationale(rec):
    assert len(rec.bid_distribution) == 4
    assert rec.rationale.strip()
    # Layer 2 narration (baked) names the recommendation and the disqualifying signal
    assert "Vantage" in rec.rationale and "winding-up" in rec.rationale.lower()


def test_ranking_is_clean_first_then_flagged(rec):
    # the flagged firm is last despite being cheapest; clean firms ordered by price
    assert rec.ranked[-1].firm_id == "F-EL-01"
    clean_totals = [r.corrected_total for r in rec.ranked if not r.recommended_against]
    assert clean_totals == sorted(clean_totals)
