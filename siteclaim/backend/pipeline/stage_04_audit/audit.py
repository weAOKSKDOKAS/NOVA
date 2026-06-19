"""Stage 04 — forensic audit: catch the fatal error BEFORE filing.

``audit_claim(facts, validity, draft, today) -> AuditReport``

This stage is mostly DETERMINISTIC cross-checking (Layer 1), with a thin Layer-2
LLM pass for prose-level consistency only. It does NOT decide the law — it re-runs
the engine and cross-foots the draft against the facts, so a defect that slipped
through earlier is caught here.

Deterministic checks:
  (a) amount reconciliation — every figure in the draft traces back to
      ExtractedFacts (no drifted numbers), and the claimed total cross-foots
      against the itemised particulars;
  (b) rendered mandatory particulars — the s.18 particulars are actually present
      in ``rendered_markdown`` (not merely in the structured fields), and no
      unresolved ``[⚠️ …]`` placeholder remains;
  (c) deadline clock — recomputed against ``today``: any breached or
      dangerously-close statutory window is surfaced (danger window is
      config-driven, ``sopo_config.DEADLINE_DANGER_WINDOW_WORKING_DAYS``);
  (d) notice validity — ``notice_validity`` is re-run fresh; any way the notice
      could be void is surfaced (this is what catches the demo "gotcha":
      wrong-party service is FATAL).
Plus carried-over non-notice legal failures from the supplied ValidityReport, so
the audit is a complete final gate.

LLM consistency pass (one call, ``claude-sonnet-4-6``): reads the rendered draft
for internal contradictions or particulars referencing facts not in
ExtractedFacts. It is additive and SKIPPED in DEMO_MODE (offline) — the
fatal-catching above is fully deterministic and needs no network.

Every Finding carries a severity and a suggested_fix; findings are sorted
fatal → warning → info. The top-level verdict (FILEABLE / FILEABLE_WITH_FIXES /
NOT_FILEABLE) is derived deterministically from the worst finding by the
AuditReport model itself.
"""

import json
from datetime import date
from decimal import Decimal

from rules_engine import sopo_config
from rules_engine.deadlines import compute_deadlines
from rules_engine.notice_validity import check_notice_validity
from schemas.models import (
    AuditLLMFindings,
    AuditReport,
    Check,
    ClaimDraft,
    ExtractedFacts,
    Finding,
    Severity,
    ValidityReport,
)

from pipeline.llm_client import LLMClient, demo_mode

# The exact cell markers Stage 03 renders for missing / low-confidence particulars.
# Matching these (not the bare "[⚠️" prefix) avoids counting the draft banner's own
# legend text, which references the marker to explain it to the reader.
_PLACEHOLDER_MARKERS = ("[⚠️ MISSING", "[⚠️ UNVERIFIED")
_DANGER_WINDOW = sopo_config.DEADLINE_DANGER_WINDOW_WORKING_DAYS

_SEVERITY_RANK = {Severity.FATAL: 0, Severity.WARNING: 1, Severity.INFO: 2}

_client = LLMClient()


# ---------------------------------------------------------------------------
# Check -> Finding adapter (for the engine re-runs)
# ---------------------------------------------------------------------------
def _finding_from_check(c: Check) -> Finding:
    return Finding(
        issue=c.explanation,
        location=c.name,
        severity=c.severity,
        suggested_fix=f"Resolve the failing check '{c.name}' before filing ({c.sopo_reference}).",
        sopo_reference=c.sopo_reference,
    )


# ---------------------------------------------------------------------------
# (a) Amount reconciliation — no drifted numbers; the total cross-foots
# ---------------------------------------------------------------------------
def _line_item_total(facts: ExtractedFacts) -> Decimal:
    return sum((li.amount for li in facts.line_items if li.amount is not None), Decimal(0))


def _check_amounts(facts: ExtractedFacts, draft: ClaimDraft) -> list[Finding]:
    findings: list[Finding] = []
    md = draft.rendered_markdown
    fact_claimed = facts.claimed_amount.value

    # The drafted claimed amount must equal the extracted fact — a drift is fatal.
    if draft.claimed_amount != fact_claimed:
        findings.append(
            Finding(
                issue=(
                    f"The drafted claimed amount ({draft.claimed_amount}) does not match the "
                    f"extracted claimed amount ({fact_claimed})."
                ),
                location="claimed_amount",
                severity=Severity.FATAL,
                suggested_fix="Reset the claimed amount to the extracted figure; the draft must not drift from the source facts.",
            )
        )

    # The claimed amount must actually appear in the rendered document body.
    if fact_claimed is not None and f"{fact_claimed:,.2f}" not in md:
        findings.append(
            Finding(
                issue=f"The claimed amount {fact_claimed:,.2f} does not appear in the rendered claim document.",
                location="rendered_markdown",
                severity=Severity.WARNING,
                suggested_fix="State the amount claimed verbatim in the body of the claim.",
            )
        )

    # Cross-foot: the claimed total should equal the sum of the itemised particulars.
    line_total = _line_item_total(facts)
    has_amounts = any(li.amount is not None for li in facts.line_items)
    if has_amounts and fact_claimed is not None and line_total != fact_claimed:
        findings.append(
            Finding(
                issue=(
                    f"The claimed total {fact_claimed:,.2f} does not equal the sum of the "
                    f"itemised particulars {line_total:,.2f}."
                ),
                location="line_items",
                severity=Severity.WARNING,
                suggested_fix="Reconcile the line items with the claimed total so they cross-foot.",
            )
        )

    # Each drafted line-item amount must match the corresponding extracted fact.
    for i, (drafted, fact) in enumerate(zip(draft.line_items, facts.line_items)):
        if drafted.amount != fact.amount:
            findings.append(
                Finding(
                    issue=f"Line item {i} amount drifted: draft {drafted.amount} vs fact {fact.amount}.",
                    location=f"line_items[{i}]",
                    severity=Severity.FATAL,
                    suggested_fix="Restore the line-item amount to the extracted value.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# (b) Mandatory particulars actually present in the rendered markdown
# ---------------------------------------------------------------------------
def _check_rendered_particulars(facts: ExtractedFacts, draft: ClaimDraft) -> list[Finding]:
    findings: list[Finding] = []
    md = draft.rendered_markdown

    n = sum(md.count(m) for m in _PLACEHOLDER_MARKERS)
    if n:
        findings.append(
            Finding(
                issue=f"The rendered claim still contains {n} unresolved placeholder(s) (missing or low-confidence mandatory particulars).",
                location="rendered_markdown",
                severity=Severity.WARNING,
                suggested_fix="Confirm and fill every [⚠️ …] placeholder before filing; the document must not go out with placeholders.",
            )
        )

    claimant = facts.parties.claimant.value
    respondent = facts.parties.respondent.value
    required = [
        ("the claimant's name", claimant.name if claimant else None),
        ("the respondent's name", respondent.name if respondent else None),
        ("the statutory statement (Cap. 652)", "Cap. 652"),
    ]
    for label, needle in required:
        if needle and needle not in md:
            findings.append(
                Finding(
                    issue=f"Mandatory particular missing from the document body: {label} is not present in the rendered claim.",
                    location="rendered_markdown",
                    severity=Severity.FATAL,
                    suggested_fix=f"Add {label} to the claim document.",
                    sopo_reference="SOPO s.18",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# (c) Deadline clock — recomputed against `today`
# ---------------------------------------------------------------------------
def _check_deadlines(facts: ExtractedFacts, today: date) -> list[Finding]:
    findings: list[Finding] = []
    ds = compute_deadlines(facts, today)  # re-run the clock against today (don't trust upstream)
    for d in ds.deadlines:
        if d.due_date < today:
            findings.append(
                Finding(
                    issue=(
                        f"Statutory deadline '{d.name}' was due {d.due_date} "
                        f"({-d.business_days_remaining} business day(s) ago) and is BREACHED."
                    ),
                    location=f"deadline:{d.name}",
                    severity=Severity.WARNING,
                    suggested_fix="Confirm whether the window can still be met or an extension/adjudication applies; escalate immediately.",
                    sopo_reference=d.sopo_reference,
                )
            )
        elif 0 <= d.business_days_remaining <= _DANGER_WINDOW:
            findings.append(
                Finding(
                    issue=(
                        f"Statutory deadline '{d.name}' is due {d.due_date} — only "
                        f"{d.business_days_remaining} business day(s) away (danger window {_DANGER_WINDOW})."
                    ),
                    location=f"deadline:{d.name}",
                    severity=Severity.INFO,
                    suggested_fix="Prioritise serving/acting before this window closes.",
                    sopo_reference=d.sopo_reference,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# (d) Notice validity re-run + carried-over non-notice legal failures
# ---------------------------------------------------------------------------
def _check_notice(facts: ExtractedFacts) -> list[Finding]:
    return [_finding_from_check(c) for c in check_notice_validity(facts) if not c.passed]


def _carried_legal_findings(validity: ValidityReport) -> list[Finding]:
    """Surface failed non-notice checks from the supplied report (notice is re-run fresh)."""
    return [
        _finding_from_check(c)
        for c in validity.checks
        if not c.passed and not c.name.startswith("notice.")
    ]


# ---------------------------------------------------------------------------
# Thin LLM consistency pass (live only — skipped offline in DEMO_MODE)
# ---------------------------------------------------------------------------
def _consistency_system_prompt() -> str:
    return (
        "You are the forensic-audit consistency pass of SiteClaim. You are given a drafted "
        "Hong Kong SOPO payment claim (rendered markdown) and the structured ExtractedFacts "
        "it was built from. Find ONLY:\n"
        "  - internal contradictions within the document, and\n"
        "  - particulars in the document that reference facts NOT present in ExtractedFacts "
        "(invented or drifted content).\n"
        "Do NOT re-judge the law, recompute deadlines, or restate facts that are consistent. "
        "Each finding needs: issue, location, severity (fatal|warning|info), suggested_fix. "
        "Return STRICT JSON for the AuditLLMFindings schema — no prose, no code fences.\n\n"
        "AuditLLMFindings JSON schema:\n"
        f"{json.dumps(AuditLLMFindings.model_json_schema(), indent=0)}"
    )


def _consistency_user_prompt(facts: ExtractedFacts, draft: ClaimDraft) -> str:
    return (
        "RENDERED CLAIM DOCUMENT:\n"
        f"{draft.rendered_markdown}\n\n"
        "EXTRACTED FACTS (the only facts that may appear in the document):\n"
        f"{facts.model_dump_json(indent=2)}\n\n"
        "Return the AuditLLMFindings JSON now."
    )


def _llm_consistency_findings(facts: ExtractedFacts, draft: ClaimDraft) -> list[Finding]:
    if demo_mode():
        return []  # offline: deterministic checks carry the audit; the LLM pass is additive
    result: AuditLLMFindings = _client.complete_json(
        system=_consistency_system_prompt(),
        user=_consistency_user_prompt(facts, draft),
        target_model=AuditLLMFindings,
    )
    return list(result.findings)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def audit_claim(
    facts: ExtractedFacts,
    validity: ValidityReport,
    draft: ClaimDraft,
    today: date,
) -> AuditReport:
    """Cross-check the draft against the facts + statute; return a sorted AuditReport.

    The verdict (FILEABLE / FILEABLE_WITH_FIXES / NOT_FILEABLE) is derived
    deterministically from the worst finding by :class:`AuditReport` itself.
    """
    findings: list[Finding] = []
    findings += _check_amounts(facts, draft)
    findings += _check_rendered_particulars(facts, draft)
    findings += _check_deadlines(facts, today)
    findings += _check_notice(facts)
    findings += _carried_legal_findings(validity)
    findings += _llm_consistency_findings(facts, draft)

    findings.sort(key=lambda f: (_SEVERITY_RANK[f.severity], f.location))
    return AuditReport(findings=findings)
