"""Run the steelman chatbot baseline (Anthropic claude-sonnet-4-6) over the eval set
and score it side-by-side with the engine.

The chatbot is the "well-prompted baseline" we compare against: it gets the SAME
steelman prompt (rules preamble + scenario) as in SiteClaim_Eval_Set.md, at default
temperature. A/B cases run once; C/D cases run 3× to check answer consistency
(non-determinism on a legal question is itself a finding).

Reads ANTHROPIC_API_KEY from backend/.env (never hard-coded). Writes every raw
answer to eval/chatbot_raw.md and the combined engine-vs-chatbot scorecard to
eval/scorecard.md. Does NOT touch rules_engine.

    python eval/run_chatbot.py            # live run (needs ANTHROPIC_API_KEY)
    python eval/run_chatbot.py --selftest # offline: exercise the parser/scorer only
"""

import os
import re
import sys
import time
from calendar import month_abbr, month_name
from datetime import date
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
_BACKEND = _EVAL.parent / "backend"
sys.path.insert(0, str(_EVAL))
sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_BACKEND / ".env")  # read ANTHROPIC_API_KEY from backend/.env

from cases import CASES, Case  # noqa: E402
from chatbot_prompts import build_prompt  # noqa: E402
from run_engine import score_case  # noqa: E402  (engine side, read-only)

MODEL = "claude-sonnet-4-6"
RUNS_MULTI = ("C", "D")  # categories run 3× for consistency

# Chatbot-output scoring config (separate from the engine ground truth in cases.py):
# (expected verdict in the 3-value format, defect keywords or None for "no defect").
# For timing/adjudicability cases the verdict mapping is an interpretation of the
# 3-line format and is documented as such in the scorecard.
CB_EXPECT: dict[str, tuple[str, list[str] | None]] = {
    "A1": ("FILEABLE", None),
    "A2": ("NOT_FILEABLE", ["amount", "calcul", "basis", "figure", "dollar", "how it is calc"]),
    "A3": ("NOT_FILEABLE", ["identif", "describ", "what work", "work or goods", "no description"]),
    "A4": ("NOT_FILEABLE", ["writing", "verbal", "oral"]),
    "B1": ("FILEABLE", None),
    "B2": ("NOT_FILEABLE", ["wrong party", "harbour", "unrelated", "different", "not the contract"]),
    "B3": ("NOT_FILEABLE", ["different", "entity", "kowloon", "not the same", "separate", "wrong party"]),
    "B4": ("FILEABLE", ["email", "method", "service"]),  # FILEABLE_WITH_FIXES ~ FILEABLE
    "C1": ("FILEABLE", None),  # on time -> can proceed
    "C2": ("NOT_FILEABLE", ["missed", "late", "out of time", "too late", "expired", "lost", "exceed"]),
    "C3": ("FILEABLE", None),  # on time
    "C4": ("FILEABLE", None),  # on time (control)
    "C5": ("FILEABLE", None),
    "C6": ("FILEABLE", None),  # deemed served -> fileable
    "D1": ("OUT_OF_SCOPE", ["commencement", "before", "28 aug", "predates", "2025", "not apply"]),
    "D2": ("FILEABLE", None),
    "D3": ("OUT_OF_SCOPE", ["threshold", "5,000,000", "5 million", "5m", "below", "not apply"]),
    "D4": ("FILEABLE", None),  # subcontract has no minimum
    "D5": ("OUT_OF_SCOPE", ["eot", "extension of time", "time-related", "private", "public", "phase 1", "not adjudic"]),
}

_MONTHS = {m.lower(): i for i, m in enumerate(month_name) if m}
_MONTHS.update({m.lower(): i for i, m in enumerate(month_abbr) if m})


# ---------------------------------------------------------------------------
# Parsing (pure; offline-testable)
# ---------------------------------------------------------------------------
def parse_verdict(text: str) -> str:
    norm = re.sub(r"[-\s]+", "_", text.upper())
    for v in ("NOT_FILEABLE", "OUT_OF_SCOPE", "FILEABLE"):  # NOT_/OUT_ before FILEABLE
        if v in norm:
            return v
    return "UNKNOWN"


def parse_date(text: str) -> date | None:
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b", text)  # 1 Apr 2026
    if m and m[2].lower() in _MONTHS:
        return date(int(m[3]), _MONTHS[m[2].lower()], int(m[1]))
    m = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})\b", text)  # Apr 1, 2026
    if m and m[1].lower() in _MONTHS:
        return date(int(m[3]), _MONTHS[m[1].lower()], int(m[2]))
    return None


def score_answer(case: Case, text: str) -> dict:
    exp_verdict, defect_kw = CB_EXPECT[case.id]
    low = text.lower()
    pv = parse_verdict(text)
    pdate = parse_date(text)

    v_ok = pv == exp_verdict
    if defect_kw is None:
        d_ok = bool(re.search(r"\bnone\b", low)) or "no defect" in low
    else:
        d_ok = any(kw in low for kw in defect_kw)

    if case.gt_deadline is None:
        l_ok = None
    else:
        l_ok = pdate == case.gt_deadline

    return {"verdict": pv, "date": pdate, "v": v_ok, "d": d_ok, "l": l_ok}


def _mark(ok) -> str:
    return "·" if ok is None else ("✓" if ok else "✗")


# ---------------------------------------------------------------------------
# Live model call
# ---------------------------------------------------------------------------
def make_client():
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY not found. Put it in backend/.env (gitignored) and re-run:\n"
            "    echo 'ANTHROPIC_API_KEY=sk-ant-...' >> backend/.env\n"
            "    python eval/run_chatbot.py\n"
            "(Do not paste the key into chat — it belongs in .env.)"
        )
    import anthropic  # lazy

    return anthropic.Anthropic()


def ask(client, prompt: str, max_retries: int = 4) -> str:
    import anthropic

    last = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=512,  # default temperature (omitted on purpose)
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError, anthropic.InternalServerError) as exc:
            last = exc
            time.sleep(min(2**attempt, 16))
    raise last  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Run + score
# ---------------------------------------------------------------------------
def run_all(client) -> list[dict]:
    results = []
    for case in CASES:
        n = 3 if case.category in RUNS_MULTI else 1
        prompt = build_prompt(case)
        answers = [ask(client, prompt) for _ in range(n)]
        scores = [score_answer(case, a) for a in answers]
        # consistency: identical parsed (verdict, deadline) across the runs
        keys = {(s["verdict"], s["date"].isoformat() if s["date"] else None) for s in scores}
        consistent = None if n == 1 else (len(keys) == 1)
        results.append(
            {"case": case, "answers": answers, "scores": scores, "consistent": consistent, "first": scores[0]}
        )
    return results


def write_raw(results: list[dict]) -> Path:
    lines = ["# Chatbot raw answers — claude-sonnet-4-6, steelman prompt, default temperature", ""]
    for r in results:
        c: Case = r["case"]
        lines.append(f"## {c.id} [{c.category}]  ({len(r['answers'])} run{'s' if len(r['answers']) > 1 else ''})")
        lines.append(f"**Scenario:** {c.scenario_text}")
        lines.append(f"**Ground truth:** {c.gt_verdict} · defect: {c.gt_defect or 'none'} · deadline: {c.gt_deadline or 'N/A'}")
        for i, a in enumerate(r["answers"], 1):
            lines.append(f"\n_Run {i}:_\n\n```\n{a}\n```")
        lines.append("")
    path = _EVAL / "chatbot_raw.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_scorecard(results: list[dict]) -> Path:
    eng = {c.id: score_case(c) for c in CASES}
    glyph = {"PASS": "✓", "FAIL": "✗", "NM": "NM", "NA": "·"}

    lines = [
        "# SiteClaim eval scorecard — engine vs. chatbot",
        "",
        "Engine: `eval/run_engine.py` over `rules_engine` (deterministic). Chatbot: "
        "`eval/run_chatbot.py` — claude-sonnet-4-6, the verbatim steelman prompt, default "
        "temperature; A/B once, C/D 3× (raw answers in `eval/chatbot_raw.md`).",
        "",
        "Marks: ✓ correct · ✗ wrong · NM engine does not model this dimension · · not applicable.",
        "Chatbot verdicts use the 3-line format's FILEABLE/NOT_FILEABLE/OUT_OF_SCOPE; for the "
        "timing/adjudicability cases (C1–C4, D5) that mapping is an interpretation — the objective "
        "signals there are the **deadline date** and **3-run consistency**.",
        "",
        "## Side by side",
        "",
        "| Case | GT verdict | Engine V/D/L | Chatbot V/D/L | 3-run consistent |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        c: Case = r["case"]
        e = eng[c.id]
        s = r["first"]
        ev = f"{glyph[e['v']]} {glyph[e['d']]} {glyph[e['l']]}"
        cv = f"{_mark(s['v'])} {_mark(s['d'])} {_mark(s['l'])}"
        cons = "—" if r["consistent"] is None else ("yes" if r["consistent"] else "**NO**")
        lines.append(f"| {c.id} | {c.gt_verdict} | {ev} | {cv} | {cons} |")

    # category totals
    lines += ["", "## Totals by category (correct / scoreable)", "", "| Category | Engine | Chatbot |", "|---|---|---|"]
    e_tot = c_tot = e_sc = c_sc = 0
    for cat in ("A", "B", "C", "D"):
        rs = [r for r in results if r["case"].category == cat]
        e_pass = e_score = c_pass = c_score = 0
        for r in rs:
            e = eng[r["case"].id]
            for m in (e["v"], e["d"], e["l"]):
                if m in ("PASS", "FAIL"):
                    e_score += 1
                    e_pass += m == "PASS"
            s = r["first"]
            for ok in (s["v"], s["d"], s["l"]):
                if ok is not None:
                    c_score += 1
                    c_pass += bool(ok)
        e_tot += e_pass; e_sc += e_score; c_tot += c_pass; c_sc += c_score
        lines.append(f"| {cat} | {e_pass}/{e_score} | {c_pass}/{c_score} |")
    lines.append(f"| **Total** | **{e_tot}/{e_sc}** | **{c_tot}/{c_sc}** |")

    # consistency summary
    wavered = [r["case"].id for r in results if r["consistent"] is False]
    lines += [
        "",
        "## Consistency (C/D, 3 runs each)",
        "",
        f"- Cases that did NOT give an identical answer across 3 runs: **{wavered or 'none'}**.",
        "- The engine is deterministic by construction (0 wavering).",
        "",
        "## Notes",
        "",
        "- Engine `NM` cells are real coverage gaps (adjudication on-time/late C1–C2, ANB timing "
        "C3–C4, EOT adjudicability D5) — the engine abstains; the chatbot always answers, so its "
        "score there reflects whether it answered correctly, not coverage.",
    ]
    path = _EVAL / "scorecard.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def print_side_by_side(results: list[dict]) -> None:
    eng = {c.id: score_case(c) for c in CASES}
    g = {"PASS": "✓", "FAIL": "✗", "NM": "NM", "NA": "·"}
    print(f"\n{'Case':<5}{'GT verdict':<18}{'Engine VDL':<14}{'Chatbot VDL':<14}{'consistent':<11}")
    print("-" * 62)
    for r in results:
        c = r["case"]; e = eng[c.id]; s = r["first"]
        ev = f"{g[e['v']]} {g[e['d']]} {g[e['l']]}"
        cv = f"{_mark(s['v'])} {_mark(s['d'])} {_mark(s['l'])}"
        cons = "—" if r["consistent"] is None else ("yes" if r["consistent"] else "NO")
        print(f"{c.id:<5}{c.gt_verdict:<18}{ev:<14}{cv:<14}{cons:<11}")


def main() -> None:
    if "--selftest" in sys.argv:
        _selftest()
        return
    client = make_client()
    print(f"Running {len([c for c in CASES])} cases vs {MODEL} (C/D ×3)…")
    results = run_all(client)
    raw = write_raw(results)
    card = write_scorecard(results)
    print_side_by_side(results)
    print(f"\nWrote {raw.relative_to(_EVAL.parent)} and {card.relative_to(_EVAL.parent)}")


# ---------------------------------------------------------------------------
# Offline self-test of the parser/scorer (no API, no key)
# ---------------------------------------------------------------------------
def _selftest() -> None:
    by_id = {c.id: c for c in CASES}
    samples = {
        "B3": "(1) FILEABLE\n(2) none — Dragon Build Limited is the same company\n(3) N/A",  # chatbot error
        "C3": "(1) FILEABLE\n(2) none\n(3) The ANB deadline is 9 April 2026",  # wrong date (ignored holidays)
        "A2": "1) NOT_FILEABLE\n2) The claim never states the amount or how it is calculated\n3) N/A",
        "D4": "(1) OUT_OF_SCOPE\n(2) below the HK$500,000 threshold\n(3) N/A",  # chatbot error on subcontract
        "A1": "FILEABLE / none / payment response due 2026-04-01",
    }
    checks = [
        ("B3", "v", False), ("B3", "d", False),  # wrongly says fileable, wrongly says same company
        ("C3", "l", False),                       # 9 Apr != 16 Apr
        ("A2", "v", True), ("A2", "d", True),
        ("D4", "v", False),                       # OUT_OF_SCOPE wrong (should be FILEABLE)
        ("A1", "v", True), ("A1", "l", True),     # 2026-04-01 matches fixed GT
    ]
    failures = 0
    for cid, dim, want in checks:
        s = score_answer(by_id[cid], samples[cid])
        got = s[dim]
        ok = (got is want)
        print(f"  {cid}.{dim}: parsed={s['verdict']}/{s['date']} -> {dim}={got} (want {want}) {'OK' if ok else 'MISMATCH'}")
        failures += not ok
    print(f"\nself-test: {'PASS' if failures == 0 else f'{failures} MISMATCH'} — parser/scorer logic verified offline.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
