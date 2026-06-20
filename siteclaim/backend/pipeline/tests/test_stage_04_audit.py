"""Spec for Stage 04 forensic audit (offline): cross-checks, verdict, citations."""

from datetime import date
from decimal import Decimal

from rules_engine.engine import run_validation
from schemas.models import (
    AuditReport,
    AuditVerdict,
    FactField,
    Finding,
    LineItem,
    Severity,
)

from pipeline.stage_01_extract.extract import extract_facts
from pipeline.stage_02_validate.verify import verify_extraction
from pipeline.stage_03_draft.draft import draft_claim
from pipeline.stage_04_audit.audit import audit_claim

_TODAY = date(2026, 3, 2)
_RANK = {Severity.FATAL: 0, Severity.WARNING: 1, Severity.INFO: 2}


def _pipeline(load_case, case_id, today=_TODAY):
    """Run 01 -> 02 -> 03 and return (facts, report, draft) for the audit to chew on."""
    source = load_case(case_id)
    facts = verify_extraction(source, extract_facts(source)).facts
    report = run_validation(facts, today)
    draft = draft_claim(facts, report)
    return facts, report, draft


# --- the three demo cases ---------------------------------------------------
def test_clean_claim_audits_as_fileable(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    audit = audit_claim(facts, report, draft, _TODAY)
    assert audit.verdict is AuditVerdict.FILEABLE
    assert audit.passed
    assert audit.findings == []


def test_messy_claim_audits_as_fileable_with_fixes(load_case):
    facts, report, draft = _pipeline(load_case, "messy")
    audit = audit_claim(facts, report, draft, _TODAY)
    assert audit.verdict is AuditVerdict.FILEABLE_WITH_FIXES
    assert audit.passed  # warnings, but nothing fatal
    ph = next(f for f in audit.findings if f.location == "rendered_markdown")
    assert ph.severity is Severity.WARNING
    # counts the 4 rendered placeholder cells, NOT the banner's legend text.
    assert "4 unresolved placeholder" in ph.issue


def test_gotcha_claim_audits_as_not_fileable_citing_the_notice(load_case):
    facts, report, draft = _pipeline(load_case, "gotcha")
    audit = audit_claim(facts, report, draft, _TODAY)
    assert audit.verdict is AuditVerdict.NOT_FILEABLE
    assert not audit.passed
    nf = next(f for f in audit.findings if f.location == "notice.correct_party")
    assert nf.severity is Severity.FATAL
    assert nf.sopo_reference  # the finding is cited
    assert "does not match" in nf.issue.lower() and "void" in nf.issue.lower()
    assert nf.suggested_fix  # and it tells the user what to do


# --- the deterministic cross-checks -----------------------------------------
def test_a_drifted_amount_is_a_fatal_finding(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    draft.claimed_amount = Decimal("9999999.00")  # tamper: drift from the source facts
    audit = audit_claim(facts, report, draft, _TODAY)
    drift = next(f for f in audit.findings if f.location == "claimed_amount")
    assert drift.severity is Severity.FATAL
    assert audit.verdict is AuditVerdict.NOT_FILEABLE


def test_a_total_that_does_not_cross_foot_is_a_warning(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    # Add an item to the facts after drafting: the itemised total no longer equals
    # the claimed sum (claimed still matches the draft, so this is a cross-foot, not a drift).
    facts.line_items.append(LineItem(description="Extra works", amount=Decimal("50000.00"), confidence=0.9))
    audit = audit_claim(facts, report, draft, _TODAY)
    xfoot = next(f for f in audit.findings if f.location == "line_items")
    assert xfoot.severity is Severity.WARNING
    assert "cross-foot" in xfoot.suggested_fix.lower()


def test_a_mandatory_particular_missing_from_the_body_is_fatal(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    # Strip the respondent's name out of the rendered document body.
    draft.rendered_markdown = draft.rendered_markdown.replace("BigBuild Main Contractor Ltd", "REDACTED")
    audit = audit_claim(facts, report, draft, _TODAY)
    miss = [f for f in audit.findings if f.location == "rendered_markdown" and f.severity is Severity.FATAL]
    assert miss and any("respondent" in f.issue.lower() for f in miss)
    assert audit.verdict is AuditVerdict.NOT_FILEABLE


def test_a_breached_deadline_surfaces_as_a_warning(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    audit = audit_claim(facts, report, draft, date(2027, 1, 1))  # every window is long past
    breaches = [f for f in audit.findings if f.location.startswith("deadline:")]
    assert breaches and all(f.severity is Severity.WARNING for f in breaches)
    assert all(f.sopo_reference for f in breaches)  # deadline findings are cited
    assert any("BREACHED" in f.issue for f in breaches)


def test_a_deadline_inside_the_danger_window_surfaces_as_info(load_case):
    facts, report, draft = _pipeline(load_case, "clean")
    # payment_response_due is 2026-04-01; audit a few days before, inside the danger window.
    audit = audit_claim(facts, report, draft, date(2026, 3, 27))
    close = next(f for f in audit.findings if f.location == "deadline:payment_response_due")
    assert close.severity is Severity.INFO
    assert audit.verdict is AuditVerdict.FILEABLE  # info-only stays fileable


def test_findings_are_sorted_fatal_then_warning_then_info(load_case):
    facts, report, draft = _pipeline(load_case, "gotcha")  # carries the wrong-party FATAL
    facts.line_items.append(LineItem(description="Extra", amount=Decimal("1.00"), confidence=0.9))  # + a warning
    audit = audit_claim(facts, report, draft, _TODAY)
    ranks = [_RANK[f.severity] for f in audit.findings]
    assert ranks == sorted(ranks)
    assert audit.findings[0].severity is Severity.FATAL


# --- the verdict is derived deterministically by the model -------------------
def test_verdict_is_derived_from_the_worst_finding():
    info = Finding(issue="i", location="x", severity=Severity.INFO, suggested_fix="-")
    warn = Finding(issue="w", location="y", severity=Severity.WARNING, suggested_fix="-")
    fatal = Finding(issue="f", location="z", severity=Severity.FATAL, suggested_fix="-")
    assert AuditReport(findings=[]).verdict is AuditVerdict.FILEABLE
    assert AuditReport(findings=[info]).verdict is AuditVerdict.FILEABLE
    assert AuditReport(findings=[info, warn]).verdict is AuditVerdict.FILEABLE_WITH_FIXES
    assert AuditReport(findings=[warn, fatal]).verdict is AuditVerdict.NOT_FILEABLE
    # the derived verdict survives a JSON round-trip (re-derived on validation).
    rt = AuditReport.model_validate_json(AuditReport(findings=[fatal]).model_dump_json())
    assert rt.verdict is AuditVerdict.NOT_FILEABLE
