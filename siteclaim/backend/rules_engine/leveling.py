"""Deterministic bid leveling (Layer 1).

Implements ``references/rubrics/leveling_rules.md``. The LLM parses a reply into a
:class:`BidReply`; **every calculation and judgement below is pure Python**, never
the model:

* recompute each line ``amount = qty x rate`` and use the recomputed value;
* record an :class:`ArithmeticFinding` (warning) wherever the bidder's stated amount
  disagrees with ``qty x rate``;
* ``corrected_total`` = the sum of the recomputed line amounts;
* a **missing rate** (including a missing provisional sum) is a **scope gap** —
  recorded, never treated as zero, never silently filled;
* a **stated exclusion** is a flagged, non-comparable item — recorded, never used to
  silently lower the price;
* ``normalized_total`` puts every bid on the **same scope basis**: it starts from
  ``corrected_total`` and adds, for each scope gap, the peer median price of that
  item across the other bids that did price it — so a bid that left scope out is
  compared like-for-like. Scope differences are surfaced, never absorbed.

``claimed_total`` (the bidder's own total, on :class:`BidReply`) is recorded upstream
but never used for ranking — only ``corrected_total`` is.
"""

from __future__ import annotations

from statistics import median

from schemas.models import ArithmeticFinding, BidReply, LevelledBid, Severity

_EPSILON = 0.005  # currency tolerance for the qty*rate vs stated-amount comparison


def peer_item_reference(replies: list[BidReply]) -> dict[str, float]:
    """For each item_ref, the median recomputed amount across bids that priced it.

    Used to value another bid's scope gaps at a fair peer price for ``normalized_total``.
    """
    amounts: dict[str, list[float]] = {}
    for reply in replies:
        for line in reply.line_items:
            if line.rate is not None:
                amounts.setdefault(line.item_ref, []).append(round(line.qty * line.rate, 2))
    return {item_ref: float(median(values)) for item_ref, values in amounts.items() if values}


def level_reply(
    reply: BidReply, firm_name: str, peer_reference: dict[str, float] | None = None
) -> LevelledBid:
    """Level one :class:`BidReply` into a :class:`LevelledBid` (pure, deterministic)."""
    peer_reference = peer_reference or {}
    findings: list[ArithmeticFinding] = []
    scope_gaps: list[str] = []
    gap_item_refs: list[str] = []
    corrected_total = 0.0

    for line in reply.line_items:
        if line.rate is None:
            # Missing rate / missing provisional sum -> scope gap. Never zero, never filled.
            kind = "missing provisional sum" if "provisional" in line.description.lower() else "missing rate"
            scope_gaps.append(f"{line.item_ref} — {line.description} ({kind})")
            gap_item_refs.append(line.item_ref)
            continue
        recomputed = round(line.qty * line.rate, 2)
        if line.amount is not None and abs(line.amount - recomputed) > _EPSILON:
            findings.append(ArithmeticFinding(
                location=f"line {line.item_ref}",
                issue=f"stated amount {line.amount:,.0f} != qty x rate {recomputed:,.0f}",
                corrected_value=recomputed,
                severity=Severity.WARNING,
            ))
        corrected_total += recomputed

    corrected_total = round(corrected_total, 2)
    normalized_total = round(
        corrected_total + sum(peer_reference.get(ref, 0.0) for ref in gap_item_refs), 2
    )

    return LevelledBid(
        firm_id=reply.firm_id,
        firm_name=firm_name,
        trade=reply.trade,
        normalized_total=normalized_total,
        corrected_total=corrected_total,
        arithmetic_findings=findings,
        exclusions=list(reply.exclusions),  # flagged, non-comparable; never lowers the price
        scope_gaps=scope_gaps,
    )
