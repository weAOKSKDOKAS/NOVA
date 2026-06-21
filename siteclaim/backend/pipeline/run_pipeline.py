"""Offline end-to-end pipeline runner — forced DEMO_MODE, readable trace.

Runs the whole SiteSource pipeline on the demo fixtures with no network and no
model load: ingest -> shortlist -> dispatch (auto-approving the clean top firm per
trade) -> level -> recommend. It ends on the hero catch: for the electrical trade
the cheapest bidder is recommended against for an active winding-up petition and two
safety prosecutions, and the clean runner-up is recommended.

Run it:  ``cd backend && python pipeline/run_pipeline.py``
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the top-level packages (db, schemas, pipeline, rules_engine) importable when
# this is run directly as `python pipeline/run_pipeline.py` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DEMO_MODE"] = "true"  # force the offline path before any stage runs

from db import store  # noqa: E402
from db.outbox import send_mock  # noqa: E402
from pipeline.stage_01_ingest.ingest import ingest_tender  # noqa: E402
from pipeline.stage_02_shortlist.shortlist import shortlist  # noqa: E402
from pipeline.stage_03_dispatch.dispatch import build_dispatch  # noqa: E402
from pipeline.stage_04_level.export_xlsx import OUT_PATH, export_leveling_xlsx  # noqa: E402
from pipeline.stage_04_level.level import level_bids, load_demo_replies  # noqa: E402
from pipeline.stage_05_recommend.recommend import recommend  # noqa: E402
from schemas.models import DocType, Severity, TenderDocument, TenderPackage  # noqa: E402

_SCOPE_FIXTURE = "cases/clean/scope_packages.json"
_DISPATCH_FIXTURE = "cases/clean/dispatch.json"
_REPLIES_FIXTURE = "cases/messy/bid_replies.json"
_RATIONALE_FIXTURE = "cases/clean/recommendation_rationale.json"
_HERO_TRADE = "electrical"


def _rule(title: str) -> None:
    print("\n" + "═" * 78 + f"\n  {title}\n" + "═" * 78)


def _money(x: float) -> str:
    return f"HK${x:,.0f}"


def _demo_tender() -> TenderPackage:
    docs = [
        TenderDocument(doc_type=DocType.METHOD_OF_MEASUREMENT, filename="method_of_measurement.pdf"),
        TenderDocument(doc_type=DocType.PARTICULAR_SPECIFICATION, filename="particular_specification.pdf"),
        TenderDocument(doc_type=DocType.TENDER_ADDENDUM, filename="tender_addendum.pdf"),
        TenderDocument(doc_type=DocType.SCHEDULE_OF_RATES, filename="schedule_of_rates.pdf"),
    ]
    return TenderPackage(
        project_name="Kwun Tong Commercial Tower — Category-A Office Fit-out",
        description="Cat-A office fit-out across 12 floors.",
        documents=docs,
    )


def main() -> None:
    conn = store.get_connection()
    try:
        # -- Stage 01: ingest ------------------------------------------------
        _rule("STAGE 01 — INGEST  (Layer 2 splits scope, Layer 1 validates trades)")
        scope = ingest_tender(_demo_tender(), demo_fixture=_SCOPE_FIXTURE)
        print(f"Project: {scope.project_name}")
        for pkg in scope.packages:
            print(f"  • {pkg.trade:22} {len(pkg.sor_items)} SoR items — {pkg.scope_summary[:60]}…")

        # -- Stage 02: shortlist --------------------------------------------
        _rule("STAGE 02 — SHORTLIST  (pure Layer 1 cross-reference over the database)")
        sl = shortlist(scope, conn=conn)
        for cand in sl.per_trade[_HERO_TRADE]:
            tag = "  ⛔ RECOMMEND AGAINST" if cand.recommended_against else ""
            fatal = ", ".join(f.rule_ref for f in cand.risk_flags if f.severity is Severity.FATAL)
            print(f"  {cand.firm.firm_id}  {cand.firm.name[:34]:34} match={cand.match_score:.3f}"
                  f"  {('['+fatal+']') if fatal else ''}{tag}")

        # -- Stage 03: dispatch (auto-approve the clean top firm per trade) ---
        _rule("STAGE 03 — DISPATCH  (Layer 4 gate; trade-only bundles; mock outbox)")
        approvals = {
            trade: [next((c.firm.firm_id for c in cands if not c.recommended_against), cands[0].firm.firm_id)]
            for trade, cands in sl.per_trade.items() if cands
        }
        dispatch = build_dispatch(sl, approvals, demo_fixture=_DISPATCH_FIXTURE, scope=scope, project_name=scope.project_name)
        dispatch = send_mock(dispatch)
        for bundle in dispatch.bundles:
            print(f"  {bundle.trade:22} → {bundle.firm_id} {bundle.firm_name[:26]:26}"
                  f"  docs:{len(bundle.bundle_doc_refs)}  status:{bundle.status.value}")

        # -- Stage 04: level -------------------------------------------------
        _rule("STAGE 04 — LEVEL  (Layer 2 parses, Layer 1 recomputes every number)")
        replies = load_demo_replies(_REPLIES_FIXTURE)
        levelled = level_bids(replies, scope, conn=conn)
        claimed = {r.firm_id: r.claimed_total for r in replies}
        print(f"  {'firm':9} {'claimed':>14} {'corrected':>14}   findings / scope gaps")
        for bid in sorted(levelled, key=lambda b: b.corrected_total):
            notes = []
            if bid.arithmetic_findings:
                notes.append(f"{len(bid.arithmetic_findings)} arithmetic correction(s)")
            if bid.scope_gaps:
                notes.append(f"{len(bid.scope_gaps)} scope gap(s)")
            if bid.exclusions:
                notes.append(f"{len(bid.exclusions)} exclusion(s)")
            print(f"  {bid.firm_id:9} {_money(claimed[bid.firm_id]):>14} {_money(bid.corrected_total):>14}   {'; '.join(notes)}")
        xlsx = export_leveling_xlsx(levelled, replies, item_order=["E-01", "E-02", "E-03", "E-04", "E-05", "E-06"], path=OUT_PATH)
        print(f"  Excel comparison written: {xlsx}")

        # -- Stage 05: recommend (the hero catch) ----------------------------
        _rule("STAGE 05 — RECOMMEND  (Layer 1 risk-adjusted ranking; Layer 2 narrates)")
        rec = recommend(levelled, _HERO_TRADE, demo_fixture=_RATIONALE_FIXTURE, conn=conn)
        winner = next((r for r in rec.ranked if r.firm_id == rec.recommended_firm_id), None)
        print(f"  ✅ RECOMMEND: {winner.firm_name} ({winner.firm_id}) at {_money(winner.corrected_total)}")
        for r in rec.ranked:
            if r.recommended_against:
                print(f"  ⛔ AGAINST:   {r.firm_name} ({r.firm_id}) at {_money(r.corrected_total)} — cheapest, but:")
                for flag in [f for f in r.risk_flags if f.severity is Severity.FATAL]:
                    ev = flag.evidence[0] if flag.evidence else None
                    cite = f" [{ev.source}: {ev.reference}]" if ev else ""
                    print(f"        • {flag.label} ({flag.rule_ref}){cite}")
        if rec.historical_band:
            b = rec.historical_band
            print(f"  Historical band: low {_money(b.low)} / median {_money(b.median)} / high {_money(b.high)}")
        print("\n  Rationale (Layer 2):")
        print("   ", rec.rationale)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
