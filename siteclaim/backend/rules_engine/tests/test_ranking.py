"""Ranking demotes fatal-flagged firms regardless of price or match quality."""

from schemas.models import Candidate, Evidence, FirmProfile, RankedFirm, RiskFlag, Severity, SignalType
from rules_engine.ranking import rank_by_total, rank_candidates

_WINDING_UP = RiskFlag(
    severity=Severity.FATAL, label="Active winding-up petition", rule_ref="risk.winding_up",
    evidence=[Evidence(source="Companies Registry", signal_type=SignalType.WINDING_UP, snippet="petition", reference="CR:1")],
)


def _ranked(firm_id, total, flags=None) -> RankedFirm:
    return RankedFirm(firm_id=firm_id, firm_name=firm_id, corrected_total=total, risk_flags=flags or [])


def test_rank_by_total_demotes_cheapest_but_fatal_below_clean_runner_up():
    gotcha = _ranked("F-EL-01", 9_800_000, flags=[_WINDING_UP])  # cheapest
    runner = _ranked("F-EL-02", 12_400_000)                      # clean, pricier
    third = _ranked("F-EL-03", 13_900_000)                       # clean, pricier still

    order = rank_by_total([gotcha, runner, third])
    ids = [f.firm_id for f in order]

    assert ids[0] == "F-EL-02"          # clean cheapest wins
    assert ids[-1] == "F-EL-01"         # cheapest-overall sinks to the bottom
    flagged = next(f for f in order if f.firm_id == "F-EL-01")
    assert flagged.recommended_against is True
    assert "risk.winding_up" in flagged.reason
    assert all(f.recommended_against is False for f in order if f.firm_id != "F-EL-01")


def _candidate(firm_id, match, flags=None) -> Candidate:
    firm = FirmProfile(firm_id=firm_id, name=firm_id, registered_grade="REC (EMSD)", value_band="up_to_50m", trades=["electrical"])
    return Candidate(firm=firm, trade="electrical", match_score=match, risk_flags=flags or [])


def test_rank_candidates_demotes_best_match_when_fatally_flagged():
    gotcha = _candidate("F-EL-01", 0.95, flags=[_WINDING_UP])  # best semantic match
    runner = _candidate("F-EL-02", 0.80)                       # clean, weaker match
    other = _candidate("F-EL-03", 0.60)

    order = rank_candidates([gotcha, runner, other])
    ids = [c.firm.firm_id for c in order]

    assert ids[0] == "F-EL-02"   # top clean match wins over the flagged best match
    assert ids[-1] == "F-EL-01"


def test_rank_candidates_orders_clean_firms_by_match():
    a = _candidate("A", 0.40)
    b = _candidate("B", 0.90)
    assert [c.firm.firm_id for c in rank_candidates([a, b])] == ["B", "A"]
