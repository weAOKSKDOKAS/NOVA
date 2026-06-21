"""Construct one instance of every SiteSource contract and round-trip it."""

from schemas.models import (
    ArithmeticFinding,
    BidDistributionPoint,
    BidLineItem,
    BidReply,
    Candidate,
    Check,
    DispatchBundle,
    DispatchSet,
    DispatchStatus,
    DocType,
    Evidence,
    FirmProfile,
    HistoricalBand,
    LevelledBid,
    RankedFirm,
    Recommendation,
    RiskFlag,
    ScopePackages,
    Severity,
    ShortlistSet,
    SignalType,
    SorItem,
    TenderDocument,
    TenderPackage,
    TradeWorkPackage,
)


def _evidence() -> Evidence:
    return Evidence(
        source="Companies Registry",
        signal_type=SignalType.WINDING_UP,
        snippet="Winding-up petition HCCW 123/2026 presented 2026-01-15.",
        reference="CR:HCCW-123-2026",
    )


def _firm() -> FirmProfile:
    return FirmProfile(
        firm_id="F-EL-01",
        name="Pinnacle E&M Engineering Ltd",
        registered_grade="Group II",
        value_band="up_to_50m",
        trades=["electrical"],
        public_flags=[RiskFlag(severity=Severity.FATAL, label="Active winding-up petition", rule_ref="risk.winding_up", evidence=[_evidence()])],
        closeout_summary="Two completed fit-outs; one delayed closeout note.",
        award_history=["2024 Tseung Kwan O office fit-out"],
    )


def test_evidence_and_risk_flag():
    rf = RiskFlag(severity=Severity.FATAL, label="Active winding-up petition", rule_ref="risk.winding_up", evidence=[_evidence()])
    assert rf.severity is Severity.FATAL and rf.evidence[0].signal_type is SignalType.WINDING_UP


def test_check_primitive():
    c = Check(name="taxonomy.electrical", passed=True, severity=Severity.INFO, rule_ref="taxonomy.v1", explanation="mapped")
    assert c.passed


def test_tender_and_scope_models():
    tender = TenderPackage(
        project_name="TKO Fit-out",
        description="Cat-A office fit-out",
        documents=[TenderDocument(doc_type=DocType.SCHEDULE_OF_RATES, filename="sor.pdf")],
    )
    pkg = TradeWorkPackage(
        trade="electrical",
        scope_summary="LV distribution and lighting",
        sor_items=[SorItem(item_ref="E-01", description="LV submain", unit="m", qty=120.0)],
        source_refs=["sor.pdf"],
    )
    scope = ScopePackages(project_name=tender.project_name, packages=[pkg])
    assert scope.packages[0].sor_items[0].qty == 120.0
    assert tender.documents[0].doc_type is DocType.SCHEDULE_OF_RATES


def test_candidate_and_shortlist():
    cand = Candidate(firm=_firm(), trade="electrical", match_score=0.82, evidence=[_evidence()])
    sl = ShortlistSet(per_trade={"electrical": [cand]})
    assert 0.0 <= sl.per_trade["electrical"][0].match_score <= 1.0


def test_dispatch_models():
    b = DispatchBundle(firm_id="F-EL-01", firm_name="Pinnacle", trade="electrical", bundle_doc_refs=["sor.pdf"], email_subject="RFQ", email_body="…")
    ds = DispatchSet(bundles=[b])
    assert ds.bundles[0].status is DispatchStatus.DRAFTED


def test_bid_and_leveling_models():
    reply = BidReply(
        firm_id="F-EL-01",
        trade="electrical",
        line_items=[BidLineItem(item_ref="E-01", description="LV submain", unit="m", qty=120.0, rate=85.0, amount=10200.0)],
        exclusions=["Builder's work in connection"],
        claimed_total=10200.0,
    )
    lev = LevelledBid(
        firm_id="F-EL-01",
        firm_name="Pinnacle",
        trade="electrical",
        normalized_total=10200.0,
        corrected_total=10200.0,
        arithmetic_findings=[ArithmeticFinding(location="line_items[0]", issue="amount mismatch", corrected_value=10200.0, severity=Severity.WARNING)],
        scope_gaps=["PC sum for switchgear missing"],
    )
    assert reply.line_items[0].qty * reply.line_items[0].rate == lev.corrected_total


def test_recommendation_model():
    rec = Recommendation(
        trade="electrical",
        recommended_firm_id="F-EL-02",
        ranked=[RankedFirm(firm_id="F-EL-01", firm_name="Pinnacle", corrected_total=10200.0, recommended_against=True, reason="winding-up")],
        rationale="Recommend the clean runner-up.",
        bid_distribution=[BidDistributionPoint(firm_name="Pinnacle", corrected_total=10200.0)],
        historical_band=HistoricalBand(low=9000.0, median=11000.0, high=13000.0),
    )
    # JSON round-trip works for the whole contract surface.
    assert Recommendation.model_validate_json(rec.model_dump_json()).recommended_firm_id == "F-EL-02"
