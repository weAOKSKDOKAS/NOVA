"""Stage 04 — level: BidReplies -> LevelledBids.

Layer 2 parses each returned Schedule of Rates document into a :class:`BidReply`
(line items, rates, exclusions) via ``complete_json``; DEMO_MODE reads baked
``BidReply`` fixtures (see :func:`load_demo_replies`). Layer 1
(:mod:`rules_engine.leveling`, pure Python) then does **every calculation**:
recompute amounts, sum to ``corrected_total``, flag arithmetic disagreements,
record scope gaps and exclusions, and normalise onto a common scope basis.

Firm display names are resolved from the proprietary database (Layer 3); the
arithmetic never depends on the model.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from db import store
from pipeline.llm_client import LLMClient
from rules_engine.leveling import level_reply, peer_item_reference
from schemas.models import BidReply, LevelledBid, ScopePackages

_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"

_PARSE_SYSTEM = (
    "You parse a subcontractor's returned Schedule of Rates into structured data. "
    "Extract each line item (item_ref, description, unit, qty, rate, amount), the "
    "stated exclusions, and the bidder's claimed total. Transcribe faithfully — do "
    "NOT correct arithmetic, do NOT fill a missing rate, do NOT invent a number. "
    "Return JSON matching the BidReply schema."
)


def load_demo_replies(demo_fixture: str) -> list[BidReply]:
    """Load a baked list of :class:`BidReply` from ``backend/fixtures/<demo_fixture>``."""
    data = json.loads((_FIXTURES_DIR / demo_fixture).read_text(encoding="utf-8"))
    return [BidReply.model_validate(item) for item in data]


def parse_bid_reply(
    *, firm_id: str, trade: str, images: list[str], demo_fixture: Optional[str] = None,
    client: Optional[LLMClient] = None,
) -> BidReply:
    """Layer 2: parse one returned SoR document (images) into a BidReply (live path)."""
    client = client or LLMClient()
    return client.complete_json(
        system=_PARSE_SYSTEM,
        user=f"Parse the returned Schedule of Rates for firm {firm_id}, trade {trade}.",
        target_model=BidReply,
        demo_fixture=demo_fixture,
        images=images,
    )


def level_bids(
    replies: list[BidReply],
    scope: Optional[ScopePackages] = None,  # noqa: ARG001 — reserved for scope-aware checks
    demo_fixture: Optional[str] = None,
    *,
    conn: Optional[sqlite3.Connection] = None,
) -> list[LevelledBid]:
    """Level every reply onto a common scope basis.

    If ``replies`` is empty and ``demo_fixture`` is given, the baked ``BidReply``
    fixture is loaded (the DEMO_MODE path). Firm names come from the database.
    """
    if not replies and demo_fixture:
        replies = load_demo_replies(demo_fixture)

    own_conn = conn is None
    conn = conn or store.get_connection()
    try:
        peer = peer_item_reference(replies)
        levelled = []
        for reply in replies:
            profile = store.firm_profile(conn, reply.firm_id)
            firm_name = profile.name if profile is not None else reply.firm_id
            levelled.append(level_reply(reply, firm_name, peer))
        return levelled
    finally:
        if own_conn:
            conn.close()
