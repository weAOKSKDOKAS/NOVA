"""The hero: the cross-reference demotes the cheapest, best-matching electrical
firm because the database carries a fatal winding-up petition against it."""

from db import store
from db.cross_reference import cross_reference
from db.tests.conftest import ELECTRICAL_SCOPE_QUERY
from schemas.models import Severity


def _ids(candidates):
    return [c.firm.firm_id for c in candidates]


def test_shortlist_puts_clean_runner_up_on_top(conn):
    candidates = cross_reference(conn, "electrical", ELECTRICAL_SCOPE_QUERY)
    ids = _ids(candidates)
    # the clean runner-up wins; the gotcha is present but last among electrical firms
    assert ids[0] == "F-EL-02"
    assert "F-EL-01" in ids
    assert ids.index("F-EL-01") > ids.index("F-EL-02")


def test_gotcha_demoted_below_weaker_but_clean_matches(conn):
    candidates = cross_reference(conn, "electrical", ELECTRICAL_SCOPE_QUERY)
    gotcha = next(c for c in candidates if c.firm.firm_id == "F-EL-01")
    # it is a strong semantic match, yet it sinks to the very bottom …
    assert gotcha.match_score > 0.4
    assert candidates[-1].firm.firm_id == "F-EL-01"
    # … and clean firms with a *weaker* match are ranked above it: the fatal flag,
    # not the score, drove the demotion.
    above = candidates[: candidates.index(gotcha)]
    assert any(c.match_score < gotcha.match_score for c in above)


def test_gotcha_carries_fatal_winding_up_with_evidence(conn):
    candidates = cross_reference(conn, "electrical", ELECTRICAL_SCOPE_QUERY)
    gotcha = next(c for c in candidates if c.firm.firm_id == "F-EL-01")
    fatal = [f for f in gotcha.risk_flags if f.severity is Severity.FATAL]
    rule_refs = {f.rule_ref for f in fatal}
    assert "risk.winding_up" in rule_refs
    assert "risk.safety_prosecutions" in rule_refs
    winding = next(f for f in fatal if f.rule_ref == "risk.winding_up")
    assert winding.evidence and winding.evidence[0].reference == "CR:HCCW-215/2026"


def test_no_eos_electrical_firm_is_silently_dropped(conn):
    # New contract: every electrical firm WITH an assessable EOS record is shown
    # (the flagged firm is demoted, never hidden); none is silently dropped.
    candidates = cross_reference(conn, "electrical", ELECTRICAL_SCOPE_QUERY)
    assert set(_ids(candidates)) == {f.firm_id for f in store.shortlistable_firms_for_trade(conn, "electrical")}
    assert "F-EL-01" in set(_ids(candidates))  # the flagged firm is present, just demoted


def test_public_only_firms_are_in_db_but_never_shortlisted(conn):
    # The wider public-record pool exists in the firms table (discovery/coverage) …
    assessable = store.eos_firm_ids(conn)
    public_only = {f.firm_id for f in store.all_firms(conn)} - assessable
    assert public_only  # the real scrape is present in the DB
    # … but no public-only firm (no EOS) appears in any per-tender shortlist.
    for trade in ("electrical", "mechanical_plumbing", "fire_services"):
        ids = {c.firm.firm_id for c in cross_reference(conn, trade, "scope summary")}
        assert not (ids & public_only)
    # and the electrical shortlist is exactly the four assessed demo firms, in order.
    order = [c.firm.firm_id for c in cross_reference(conn, "electrical", ELECTRICAL_SCOPE_QUERY)]
    assert order == ["F-EL-02", "F-EL-04", "F-EL-03", "F-EL-01"]
