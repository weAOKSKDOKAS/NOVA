"""Run the SiteClaim rules engine over the eval set and score it against ground truth.

For each case: build the ExtractedFacts, run ``rules_engine.engine.run_validation``,
derive the engine's verdict + failing check key(s) + the relevant computed deadline,
and score verdict (1) / defect (1) / deadline (1, where applicable) against the
hand-computed ground truth.

Coverage honesty: cases the current engine cannot evaluate (adjudication on-time/late,
ANB-service timing, EOT adjudicability) are NOT scored as passes — they are marked
NOT MODELLED and listed separately. The harness only reads the engine; it never
modifies rules_engine.

    python eval/run_engine.py
"""

import sys
from datetime import date
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from cases import CASES, Case, by_category, make_facts  # noqa: E402

from rules_engine import business_days, sopo_config  # noqa: E402
from rules_engine.deadlines import hk_public_holidays  # noqa: E402
from rules_engine.engine import run_validation  # noqa: E402
from schemas.models import Severity  # noqa: E402

_VALIDITY_VERDICTS = {"FILEABLE", "NOT_FILEABLE", "OUT_OF_SCOPE", "FILEABLE_WITH_FIXES"}
_DEADLINE_NAME = {"payment_response": "payment_response_due", "adjudication_init": "adjudication_init_due"}


def derive_verdict(report) -> tuple[str, list]:
    """Engine verdict from the ValidityReport.

    Mirrors the audit's verdict logic, with two deliberate choices: an eligibility
    fatal means SOPO does not apply -> OUT_OF_SCOPE (the eval's distinct label); and
    payer-side set_off warnings are excluded — by the engine's own design they never
    affect the claimant's claim, so they must not downgrade fileability.
    """
    fatals = [c for c in report.checks if c.severity is Severity.FATAL and not c.passed]
    warnings = [
        c
        for c in report.checks
        if c.severity is Severity.WARNING and not c.passed and not c.name.startswith("set_off.")
    ]
    if any(c.name.startswith("eligibility.") for c in fatals):
        verdict = "OUT_OF_SCOPE"
    elif fatals:
        verdict = "NOT_FILEABLE"
    elif warnings:
        verdict = "FILEABLE_WITH_FIXES"
    else:
        verdict = "FILEABLE"
    return verdict, fatals + warnings


def engine_deadline(case: Case, report) -> tuple[date | None, str]:
    """The engine's deadline for this case, plus how it was produced."""
    if case.deadline_kind is None:
        return None, ""
    if case.deadline_kind == "anb_service_8wd":
        value = business_days.add_working_days(
            case.anb_start, sopo_config.ANB_SERVICE_WORKING_DAYS, hk_public_holidays()
        )
        return value, "business_days (NOT wired into compute_deadlines)"
    name = _DEADLINE_NAME[case.deadline_kind]
    ds = report.deadlines
    for dl in ds.deadlines if ds else []:
        if dl.name == name:
            return dl.due_date, "run_validation"
    return None, ""


def score_case(case: Case) -> dict:
    facts = make_facts(**case.facts)
    report = run_validation(facts, case.today)
    verdict, failing = derive_verdict(report)
    failing_names = [c.name for c in failing]
    primary_defect = failing_names[0] if failing_names else None
    dl_value, dl_source = engine_deadline(case, report)

    # --- verdict ---
    if case.engine_models_verdict:
        v_mark = "PASS" if verdict == case.gt_verdict else "FAIL"
    else:
        v_mark = "NM"

    # --- defect ---
    if case.engine_models_verdict and case.gt_verdict in _VALIDITY_VERDICTS:
        if case.gt_defect is None:
            d_ok = primary_defect is None
        else:
            d_ok = case.gt_defect in failing_names
        d_mark = "PASS" if d_ok else "FAIL"
    else:
        d_mark = "NM" if not case.engine_models_verdict else "NA"

    # --- deadline ---
    if case.gt_deadline is None:
        l_mark = "NA"
    elif not case.engine_models_deadline:
        l_mark = "NM"
    else:
        l_mark = "PASS" if dl_value == case.gt_deadline else "FAIL"

    return {
        "case": case,
        "engine_verdict": verdict,
        "failing_names": failing_names,
        "primary_defect": primary_defect,
        "deadline_value": dl_value,
        "deadline_source": dl_source,
        "v": v_mark,
        "d": d_mark,
        "l": l_mark,
    }


_GLYPH = {"PASS": "✓", "FAIL": "✗", "NM": "NM", "NA": "·"}


def _fmt_date(d: date | None) -> str:
    return d.isoformat() if d else "—"


def print_report(results: list[dict]) -> None:
    print("SiteClaim engine eval — 19 cases scored against hand-computed ground truth\n")
    header = f"{'Case':<4} {'GT verdict':<18} {'Engine verdict':<18} {'V':<3} {'D':<3} {'L':<3} {'GT date':<11} {'Engine date':<11} defect"
    print(header)
    print("-" * len(header))
    for r in results:
        c: Case = r["case"]
        ev = r["engine_verdict"] if c.engine_models_verdict else f"({r['engine_verdict']})"
        defect = r["primary_defect"] or "none"
        print(
            f"{c.id:<4} {c.gt_verdict:<18} {ev:<18} "
            f"{_GLYPH[r['v']]:<3} {_GLYPH[r['d']]:<3} {_GLYPH[r['l']]:<3} "
            f"{_fmt_date(c.gt_deadline):<11} {_fmt_date(r['deadline_value']):<11} {defect}"
        )

    # per-category totals (scoreable = PASS + FAIL)
    print("\nPer-category score (engine; scoreable = PASS+FAIL, excludes NM/NA):")
    cats = by_category()
    cat_lines = []
    tot_pass = tot_scoreable = 0
    for cat in sorted(cats):
        rs = [r for r in results if r["case"].category == cat]
        passes = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m == "PASS")
        scoreable = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m in ("PASS", "FAIL"))
        nm = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m == "NM")
        tot_pass += passes
        tot_scoreable += scoreable
        line = f"  {cat} ({len(rs)} cases): {passes}/{scoreable} points · {nm} dimension(s) NOT MODELLED"
        cat_lines.append((cat, passes, scoreable, nm))
        print(line)
    print(f"  TOTAL: {tot_pass}/{tot_scoreable} scoreable points")

    # NOT MODELLED list
    print("\nNOT MODELLED (engine cannot currently evaluate — a real coverage finding):")
    for r in results:
        c = r["case"]
        dims = [n for n, m in (("verdict", r["v"]), ("defect", r["d"]), ("deadline", r["l"])) if m == "NM"]
        if dims:
            print(f"  {c.id}  [{', '.join(dims)}]  {c.not_modelled_reason}")

    # discrepancies (engine disagrees with GT on a MODELLED dimension)
    disc = [r for r in results if "FAIL" in (r["v"], r["d"], r["l"])]
    if disc:
        print("\nDISCREPANCIES (engine ≠ ground truth on a modelled dimension — investigate):")
        for r in disc:
            c = r["case"]
            bad = [n for n, m in (("verdict", r["v"]), ("defect", r["d"]), ("deadline", r["l"])) if m == "FAIL"]
            detail = ""
            if "deadline" in bad:
                detail = f" engine {_fmt_date(r['deadline_value'])} vs GT {_fmt_date(c.gt_deadline)}."
            print(f"  {c.id}  [{', '.join(bad)}]{detail} {c.notes}")


def write_scorecard(results: list[dict]) -> Path:
    cats = by_category()
    lines = [
        "# SiteClaim eval scorecard — engine vs. chatbot",
        "",
        "Engine scores are computed by `eval/run_engine.py` against the hand-computed ground",
        "truth in `eval/cases.py` (transcribed from `SiteClaim_Eval_Set.md`). The **Chatbot**",
        "column is intentionally empty — run `eval/chatbot_prompts.py` outputs through ChatGPT",
        "(3× for C/D per the doc) and fill it in.",
        "",
        "Scoring: verdict (1) + defect (1) + deadline (1, where applicable) per case.",
        "`NM` = the current engine does not model that dimension (not a fail — a coverage gap).",
        "",
        "## Score by category",
        "",
        "| Category | What it tests | Engine (pass/scoreable) | NM dims | Chatbot |",
        "|---|---|---|---|---|",
    ]
    tests = {
        "A": "s.18 basics, formatting",
        "B": "service / party",
        "C": "date & working-day math, deeming",
        "D": "eligibility edges",
    }
    tot_pass = tot_scoreable = tot_nm = 0
    for cat in sorted(cats):
        rs = [r for r in results if r["case"].category == cat]
        passes = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m == "PASS")
        scoreable = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m in ("PASS", "FAIL"))
        nm = sum(1 for r in rs for m in (r["v"], r["d"], r["l"]) if m == "NM")
        tot_pass, tot_scoreable, tot_nm = tot_pass + passes, tot_scoreable + scoreable, tot_nm + nm
        lines.append(f"| {cat} ({len(rs)}) | {tests[cat]} | **{passes}/{scoreable}** | {nm} | _tbd_ |")
    lines.append(f"| **Total** | | **{tot_pass}/{tot_scoreable}** | {tot_nm} | _tbd_ |")

    lines += ["", "## Per-case detail", "", "| Case | GT verdict | Engine verdict | V | D | L | GT date | Engine date |", "|---|---|---|---|---|---|---|---|"]
    for r in results:
        c = r["case"]
        ev = r["engine_verdict"] if c.engine_models_verdict else f"({r['engine_verdict']})"
        lines.append(
            f"| {c.id} | {c.gt_verdict} | {ev} | {_GLYPH[r['v']]} | {_GLYPH[r['d']]} | {_GLYPH[r['l']]} "
            f"| {_fmt_date(c.gt_deadline)} | {_fmt_date(r['deadline_value'])} |"
        )

    lines += ["", "## NOT MODELLED — the coverage gaps this eval surfaced", ""]
    for r in results:
        c = r["case"]
        dims = [n for n, m in (("verdict", r["v"]), ("defect", r["d"]), ("deadline", r["l"])) if m == "NM"]
        if dims:
            lines.append(f"- **{c.id}** [{', '.join(dims)}] — {c.not_modelled_reason}")

    lines += ["", "## Discrepancies (engine ≠ ground truth on a modelled dimension)", ""]
    any_disc = False
    for r in results:
        c = r["case"]
        bad = [n for n, m in (("verdict", r["v"]), ("defect", r["d"]), ("deadline", r["l"])) if m == "FAIL"]
        if bad:
            any_disc = True
            extra = f" Engine {_fmt_date(r['deadline_value'])} vs GT {_fmt_date(c.gt_deadline)}." if "deadline" in bad else ""
            lines.append(f"- **{c.id}** [{', '.join(bad)}]{extra} {c.notes}")
    if not any_disc:
        lines.append("- none")

    path = Path(__file__).resolve().parent / "scorecard.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    results = [score_case(c) for c in CASES]
    print_report(results)
    out = write_scorecard(results)
    print(f"\nWrote {out.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
