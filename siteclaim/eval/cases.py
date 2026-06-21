"""SiteClaim eval set — 19 cases (A1–A4, B1–B4, C1–C6, D1–D5) as structured data.

Transcribed from SiteClaim_Eval_Set.md. Each case carries the natural-language
scenario (for the chatbot side), the structured facts needed to build an
``ExtractedFacts`` for the engine, the adjudication/deadline context, and the
hand-computed ground truth (verdict, defect key, deadline).

Coverage honesty is encoded here, not faked at scoring time: ``engine_models_verdict``
and ``engine_models_deadline`` say what the *current* engine can actually evaluate.
Cases the engine does not model (adjudication on-time/late, ANB-service timing,
EOT adjudicability) are flagged so run_engine lists them as NOT MODELLED rather
than scoring a fake pass.
"""

import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from schemas.models import (  # noqa: E402
    ContractType,
    ExtractedFacts,
    FactField,
    LineItem,
    Parties,
    Party,
    PaymentResponseFacts,
    Sector,
    ServiceDetails,
    WorkPeriod,
)


def _ff(value, confidence: float = 0.95):
    return FactField(value=value, confidence=confidence, source_span="eval-fixture")


def make_facts(
    *,
    contract_type: ContractType = ContractType.SUBCONTRACT_CONSTRUCTION,
    contract_sum: Decimal | None = Decimal("1800000"),
    contract_date: date | None = date(2025, 10, 3),  # after 28 Aug 2025 commencement
    sector: Sector = Sector.PRIVATE,
    reference_date: date | None = date(2026, 2, 28),
    claimed_amount: Decimal | None = Decimal("1250000"),
    work_period_present: bool = True,
    line_items_present: bool = True,
    docs_present: bool = True,
    in_writing: bool = True,
    claimant_name: str = "Acme Subcontracting Ltd",
    respondent_name: str = "BigBuild Main Contractor Ltd",
    served_on: str | None = None,  # None -> served on the respondent (correct party)
    service_method: str = "personal_delivery",
    service_date: date | None = date(2026, 3, 2),
    proof_retained: bool = True,
    response_served: bool | None = None,
    response_date: date | None = None,
    response_disputes: bool = False,
) -> ExtractedFacts:
    """Build an ExtractedFacts from case parameters (defaults = a clean valid claim)."""
    work_period = WorkPeriod(start=date(2026, 2, 1), end=reference_date) if work_period_present else None
    line_items = (
        [LineItem(description="Rebar fixing to grid C-F", amount=claimed_amount, confidence=0.9)]
        if line_items_present
        else []
    )
    docs = ["invoice_42.pdf", "site_diary_feb.pdf"] if docs_present else []
    return ExtractedFacts(
        contract_sum=_ff(contract_sum),
        contract_type=_ff(contract_type),
        sector=_ff(sector),
        parties=Parties(
            claimant=_ff(Party(name=claimant_name, role="subcontractor")),
            respondent=_ff(Party(name=respondent_name, role="main contractor")),
        ),
        reference_date=_ff(reference_date),
        claimed_amount=_ff(claimed_amount),
        work_period=_ff(work_period),
        line_items=line_items,
        supporting_doc_refs=docs,
        contract_date=_ff(contract_date),
        claim_served_date=_ff(service_date),
        claim_in_writing=_ff(in_writing),
        service=ServiceDetails(
            method=_ff(service_method),
            served_on=_ff(served_on if served_on is not None else respondent_name),
            date_served=_ff(service_date),
            proof_retained=_ff(proof_retained),
        ),
        payment_response=PaymentResponseFacts(
            served=_ff(response_served),
            date_served=_ff(response_date),
            disputes_claim=_ff(response_disputes),
        ),
    )


@dataclass
class Case:
    id: str
    category: str  # "A" | "B" | "C" | "D"
    scenario_text: str
    facts: dict  # kwargs for make_facts
    # ground truth (hand-computed in the eval doc)
    gt_verdict: str  # FILEABLE / NOT_FILEABLE / OUT_OF_SCOPE / FILEABLE_WITH_FIXES / ON_TIME / MISSED / NOT_ADJUDICABLE
    gt_defect: str | None  # engine check key the engine should fire, or None for "no defect"
    gt_deadline: date | None = None
    # how the CURRENT engine evaluates this case (coverage honesty)
    deadline_kind: str | None = None  # "payment_response" | "adjudication_init" | "anb_service_8wd"
    anb_start: date | None = None  # start date for the 8-working-day ANB window (C3/C4)
    engine_models_verdict: bool = True  # can run_validation judge this case's headline outcome?
    engine_models_deadline: bool = True  # does run_validation EMIT the relevant deadline?
    not_modelled_reason: str = ""
    today: date = date(2026, 3, 2)
    notes: str = ""


# ---------------------------------------------------------------------------
# The steelman chatbot preamble (verbatim from SiteClaim_Eval_Set.md), used by
# chatbot_prompts.py. The scenario is appended after "CASE:".
# ---------------------------------------------------------------------------
PREAMBLE = (
    "You are a Hong Kong construction-law assistant. Under the Construction Industry Security of "
    "Payment Ordinance (Cap. 652, in force 28 Aug 2025): a valid payment claim must (s.18) be in "
    "writing, identify the work/goods, and state the claimed amount and how it is calculated. It must "
    "be served on the correct contracting party. Coverage: main construction contracts ≥ HK$5,000,000 "
    "or related goods/services ≥ HK$500,000; subcontracts in a covered chain have no minimum value; "
    "contracts must be entered on or after 28 Aug 2025. Deadlines: payment response 30 calendar days "
    "(s.20); initiate adjudication within 28 calendar days of the dispute arising (s.24); serve the "
    "adjudication notice on an ANB within 8 working days (s.25(3)); determination 55 working days "
    "(s.42(5)). Working days exclude Saturdays, Sundays, HK general holidays, and black-rainstorm/gale "
    "days. A claim served before its reference/billing date is deemed served on the reference date "
    "(not invalid). Time-related/EOT disputes are adjudicable for public contracts only in phase 1 "
    "(not private). 2026 HK general holidays: 1 Jan; 17–19 Feb; 3, 4, 6, 7 Apr; 1 May; 25 May; "
    "19 Jun; 1 Jul; 26 Sep; 1 Oct; 19 Oct; 25, 26 Dec.\n\n"
    "Given the case below, answer in three lines: (1) FILEABLE / NOT_FILEABLE / OUT_OF_SCOPE; "
    "(2) the single most important defect, or \"none\"; (3) the relevant statutory deadline date, or \"N/A\"."
)


CASES: list[Case] = [
    # ---- Category A — obvious validity (expect a tie) ---------------------
    Case(
        id="A1",
        category="A",
        scenario_text=(
            "Subcontract (HK$1.8M) entered 3 Oct 2025. Written claim for HK$1.25M rebar work, period "
            "Feb 2026, served on the correct main contractor on 2 Mar 2026 (reference date 28 Feb 2026). "
            "All particulars present."
        ),
        facts={},  # all defaults = clean valid claim
        gt_verdict="FILEABLE",
        gt_defect=None,
        gt_deadline=date(2026, 4, 1),
        deadline_kind="payment_response",
        notes="s.20 payment response = 30 calendar days from SERVICE (2 Mar 2026) -> 1 Apr 2026.",
    ),
    Case(
        id="A2",
        category="A",
        scenario_text="Same as A1 but the document states the work and period but never states a dollar figure or how it is calculated.",
        facts={"claimed_amount": None, "line_items_present": False, "docs_present": False},
        gt_verdict="NOT_FILEABLE",
        gt_defect="mandatory.states_amount_and_basis",
    ),
    Case(
        id="A3",
        category="A",
        scenario_text='Written claim states "HK$500,000 due" with no description of what work or goods it relates to.',
        facts={
            "claimed_amount": Decimal("500000"),
            "work_period_present": False,
            "line_items_present": False,
            "docs_present": False,
        },
        gt_verdict="NOT_FILEABLE",
        gt_defect="mandatory.identifies_work",
        notes="Engine also fires mandatory.states_amount_and_basis (amount given, basis absent) — both fatal; identifies_work sorts first.",
    ),
    Case(
        id="A4",
        category="A",
        scenario_text="The subcontractor phoned the QS and verbally demanded HK$400,000 for last month's work. Nothing in writing.",
        facts={"in_writing": False, "claimed_amount": Decimal("400000")},
        gt_verdict="NOT_FILEABLE",
        gt_defect="mandatory.in_writing",
    ),
    # ---- Category B — notice / party (engine edge on the near-miss) -------
    Case(
        id="B1",
        category="B",
        scenario_text='Contract with "Evergreen Civil Engineering Ltd"; claim served on "Evergreen Civil Engineering Ltd".',
        facts={"respondent_name": "Evergreen Civil Engineering Ltd", "served_on": "Evergreen Civil Engineering Ltd"},
        gt_verdict="FILEABLE",
        gt_defect=None,
    ),
    Case(
        id="B2",
        category="B",
        scenario_text='Contract with "Evergreen Civil Engineering Ltd"; claim served on "Harbour Foundations Ltd" (an unrelated company).',
        facts={"respondent_name": "Evergreen Civil Engineering Ltd", "served_on": "Harbour Foundations Ltd"},
        gt_verdict="NOT_FILEABLE",
        gt_defect="notice.correct_party",
    ),
    Case(
        id="B3",
        category="B",
        scenario_text='Subcontract is with "Dragon Build (Kowloon) Limited"; the claim is addressed to and served on "Dragon Build Limited".',
        facts={"respondent_name": "Dragon Build (Kowloon) Limited", "served_on": "Dragon Build Limited"},
        gt_verdict="NOT_FILEABLE",
        gt_defect="notice.correct_party",
        notes="Key differentiator: near-miss group entity. Chatbot likely treats the two names as the same company.",
    ),
    Case(
        id="B4",
        category="B",
        scenario_text="Served on the correct party, but only by email.",
        facts={"service_method": "email"},
        gt_verdict="FILEABLE_WITH_FIXES",
        gt_defect="notice.method",
        notes="Engine must flag the (unverified) method as a WARNING, not a fatal — over-flagging is as bad as under-flagging.",
    ),
    # ---- Category C — deadline arithmetic (engine win — the core) ---------
    Case(
        id="C1",
        category="C",
        scenario_text="Payment dispute arose Fri 20 Mar 2026. Adjudication notice served 15 Apr 2026.",
        facts={
            "service_date": date(2026, 2, 28),
            "reference_date": date(2026, 2, 28),
            "response_served": True,
            "response_disputes": True,
            "response_date": date(2026, 3, 20),
        },
        gt_verdict="ON_TIME",
        gt_defect=None,
        gt_deadline=date(2026, 4, 17),
        deadline_kind="adjudication_init",
        engine_models_verdict=False,
        not_modelled_reason="Engine computes the 28-day adjudication window but has no adjudication-notice-served field and does not judge on-time/late.",
        today=date(2026, 4, 15),
    ),
    Case(
        id="C2",
        category="C",
        scenario_text="Payment dispute arose Fri 20 Mar 2026. Adjudication notice served 20 Apr 2026.",
        facts={
            "service_date": date(2026, 2, 28),
            "reference_date": date(2026, 2, 28),
            "response_served": True,
            "response_disputes": True,
            "response_date": date(2026, 3, 20),
        },
        gt_verdict="MISSED",
        gt_defect=None,
        gt_deadline=date(2026, 4, 17),
        deadline_kind="adjudication_init",
        engine_models_verdict=False,
        not_modelled_reason="Same as C1 — the engine computes the window but does not compare the notice-served date (20 Apr) against it.",
        today=date(2026, 4, 20),
    ),
    Case(
        id="C3",
        category="C",
        scenario_text=(
            "Adjudication notice served on the respondent Wed 1 Apr 2026. No ANB named in the contract, "
            "so it must reach an ANB within 8 working days. It is served on the ANB on 16 Apr 2026."
        ),
        facts={},
        gt_verdict="ON_TIME",
        gt_defect=None,
        gt_deadline=date(2026, 4, 16),
        deadline_kind="anb_service_8wd",
        anb_start=date(2026, 4, 1),
        engine_models_verdict=False,
        engine_models_deadline=False,
        not_modelled_reason="compute_deadlines emits no ANB-service deadline and there is no ANB-timing check. (business_days.add_working_days DOES compute 16 Apr — the gap is wiring, not arithmetic.)",
    ),
    Case(
        id="C4",
        category="C",
        scenario_text="As C3 but the ANB is served on 13 Apr 2026.",
        facts={},
        gt_verdict="ON_TIME",
        gt_defect=None,
        gt_deadline=date(2026, 4, 16),
        deadline_kind="anb_service_8wd",
        anb_start=date(2026, 4, 1),
        engine_models_verdict=False,
        engine_models_deadline=False,
        not_modelled_reason="Same ANB gap as C3 (control: 13 Apr is in-window; nothing should flag it late).",
    ),
    Case(
        id="C5",
        category="C",
        scenario_text="Valid claim served 28 Feb 2026. By when must the paying party serve its payment response?",
        facts={"service_date": date(2026, 2, 28), "reference_date": date(2026, 2, 28)},
        gt_verdict="FILEABLE",
        gt_defect=None,
        gt_deadline=date(2026, 3, 30),
        deadline_kind="payment_response",
        today=date(2026, 2, 28),
    ),
    Case(
        id="C6",
        category="C",
        scenario_text="Reference/billing date is 28 Feb 2026, but the subcontractor served the claim early, on 20 Feb 2026.",
        facts={"service_date": date(2026, 2, 20), "reference_date": date(2026, 2, 28)},
        gt_verdict="FILEABLE",
        gt_defect=None,
        gt_deadline=None,  # GT: "all deadlines run from 28 Feb"; no single date scored
        deadline_kind="payment_response",  # shown as evidence the deeming worked (29 Feb base -> 30 Mar)
        today=date(2026, 2, 20),
        notes="Key differentiator: early service is deemed served on the reference date (CIC Q23), not fatal.",
    ),
    # ---- Category D — eligibility edges (engine win) ----------------------
    Case(
        id="D1",
        category="D",
        scenario_text="Subcontract entered 15 Jul 2025. Otherwise a valid HK$1.2M claim.",
        facts={"contract_date": date(2025, 7, 15), "contract_sum": Decimal("1200000")},
        gt_verdict="OUT_OF_SCOPE",
        gt_defect="eligibility.commencement",
    ),
    Case(
        id="D2",
        category="D",
        scenario_text="Subcontract entered 3 Oct 2025; valid claim.",
        facts={"contract_date": date(2025, 10, 3)},
        gt_verdict="FILEABLE",
        gt_defect=None,
    ),
    Case(
        id="D3",
        category="D",
        scenario_text="A main construction contract worth HK$4,000,000 (below the HK$5M threshold). Valid claim otherwise.",
        facts={"contract_type": ContractType.MAIN_CONSTRUCTION, "contract_sum": Decimal("4000000")},
        gt_verdict="OUT_OF_SCOPE",
        gt_defect="eligibility.threshold",
    ),
    Case(
        id="D4",
        category="D",
        scenario_text="A subcontract worth HK$300,000 within a covered main-contract chain. Valid claim otherwise.",
        facts={"contract_type": ContractType.SUBCONTRACT_CONSTRUCTION, "contract_sum": Decimal("300000")},
        gt_verdict="FILEABLE",
        gt_defect=None,
        notes="Key differentiator: subcontracts in a covered chain have no minimum value.",
    ),
    Case(
        id="D5",
        category="D",
        scenario_text=(
            "A private-sector subcontract. The dispute is purely a time-related / extension-of-time claim, "
            "which the party wants to refer to adjudication."
        ),
        facts={"sector": Sector.PRIVATE},
        gt_verdict="NOT_ADJUDICABLE",
        gt_defect=None,
        engine_models_verdict=False,
        not_modelled_reason="Engine does not model dispute-type adjudicability or the public-only phase-1 EOT restriction (no 'dispute type' fact).",
        notes="Key differentiator.",
    ),
]


def by_category() -> dict[str, list[Case]]:
    out: dict[str, list[Case]] = {}
    for c in CASES:
        out.setdefault(c.category, []).append(c)
    return out
