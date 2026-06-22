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



def _award_relevance(firm: FirmProfile) -> float:
    """A modest, deterministic match feature for a firm assessed by its public award
    record rather than a held closeout report. Recent, repeated public awards score a
    little higher; always capped below a strong closeout match so firms with assessed
    closeout history still surface first when both are present."""
    if not firm.award_history:
        return 0.0
    years = [int(a.split(":", 1)[0]) for a in firm.award_history if a.split(":", 1)[0].strip().isdigit()]
    recency = (max(years) - 2023) * 0.02 if years else 0.0
    return min(0.40 + 0.03 * min(len(firm.award_history), 3) + recency, 0.58)


def cross_reference(
    conn: sqlite3.Connection, trade: str, scope_query: str, k: int | None = None
) -> list[Candidate]:
    """Return ranked candidates for ``trade`` against ``scope_query``.

    Only firms with an **assessable EOS closeout record** are shortlisted — the
    wider public-record pool is the discovery/coverage layer, screened and counted
    but not auto-shortlisted (a firm with no closeout history would otherwise enter
    at match 0 and bury the genuinely assessed firms). Among the assessable firms,
    none is silently dropped: ``match_score`` is the semantic relevance of its
    closeout history to the scope, ``risk_flags`` are the deterministic adjudication
    of its signals, and the list is ordered clean-first by ranking. ``k`` optionally
    caps the result.
    """
    firms = store.shortlistable_firms_for_trade(conn, trade)
    scores = dict(store.semantic_closeout_matches(conn, scope_query, trade, k=len(firms) or 1))

    candidates = [
        Candidate(
            firm=firm,
            trade=trade,
            match_score=(scores[firm.firm_id] if firm.firm_id in scores else _award_relevance(firm)),
            evidence=_grounding_evidence(firm),
            risk_flags=score_firm(firm),
        )
        for firm in firms
    ]

    ranked = rank_candidates(candidates)
    return ranked[:k] if k is not None else ranked
