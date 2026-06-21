"""The cross-reference — the join that makes the recommendation defensible.

Given a trade and a scope query, fuse three things into ranked :class:`Candidate`
objects:

1. **Who does the trade** — :func:`db.store.firms_for_trade`.
2. **How well their closeout history matches the scope** — a *feature*, from
   :func:`db.store.semantic_closeout_matches` (cosine over baked vectors, offline).
3. **What risk they carry** — adjudicated by :func:`rules_engine.risk_scoring.score_firm`.

The semantic score is a soft feature; the risk demotion is hard and deterministic
(:func:`rules_engine.ranking.rank_candidates`). This is pure Layer 1 over the
database — no LLM is asked to rank, so the same input always yields the same
shortlist. It is what a generic chatbot cannot do: it has no access to this data.
"""

from __future__ import annotations

import sqlite3

from schemas.models import Candidate, Evidence, FirmProfile, SignalType
from db import store
from rules_engine.ranking import rank_candidates
from rules_engine.risk_scoring import score_firm


def _grounding_evidence(firm: FirmProfile) -> list[Evidence]:
    """Citable evidence for *why this firm is a candidate* (distinct from risk)."""
    evidence: list[Evidence] = []
    if firm.closeout_summary:
        evidence.append(Evidence(
            source="Project closeout (EOS)",
            signal_type=SignalType.CLOSEOUT_PERFORMANCE,
            snippet=firm.closeout_summary,
            reference=f"EOS:{firm.firm_id}",
        ))
    if firm.award_history:
        evidence.append(Evidence(
            source="Public award history",
            signal_type=SignalType.AWARD_HISTORY,
            snippet="; ".join(firm.award_history[:3]),
            reference=f"AWARDS:{firm.firm_id}",
        ))
    return evidence


def cross_reference(
    conn: sqlite3.Connection, trade: str, scope_query: str, k: int | None = None
) -> list[Candidate]:
    """Return ranked candidates for ``trade`` against ``scope_query``.

    Every firm that does the trade becomes a candidate (none is silently dropped);
    its ``match_score`` is the semantic relevance of its closeout history to the
    scope, its ``risk_flags`` are the deterministic adjudication of its signals, and
    the list is ordered clean-first by ranking. ``k`` optionally caps the result.
    """
    firms = store.firms_for_trade(conn, trade)
    scores = dict(store.semantic_closeout_matches(conn, scope_query, trade, k=len(firms) or 1))

    candidates = [
        Candidate(
            firm=firm,
            trade=trade,
            match_score=scores.get(firm.firm_id, 0.0),
            evidence=_grounding_evidence(firm),
            risk_flags=score_firm(firm),
        )
        for firm in firms
    ]

    ranked = rank_candidates(candidates)
    return ranked[:k] if k is not None else ranked
