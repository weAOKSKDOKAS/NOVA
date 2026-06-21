"""Stage 01 — ingest: TenderPackage -> ScopePackages.

Layer 2 (Claude) reads the four tender documents (Method of Measurement,
Particular Specification, Tender Addendum, Schedule of Rates) and splits the work
into one :class:`TradeWorkPackage` per trade — a scope summary, the relevant SoR
items, and ``source_refs`` naming which document each came from. The system prompt
forbids the model from pricing or judging a firm; it only splits and extracts.

Layer 1 then validates every returned trade against the canonical taxonomy
(``rules_engine.taxonomy``, which reads ``references/rubrics/trade_taxonomy.md``):
off-taxonomy trades are mapped to a canonical key or surfaced as unmapped — never
silently dropped. The taxonomy check is deterministic Python, not the model.

DEMO_MODE: ``complete_json`` short-circuits to a baked ``ScopePackages`` fixture and
never touches the network, exactly as the SiteClaim extract stage did.
"""

from __future__ import annotations

from typing import Optional

from pipeline.llm_client import LLMClient
from rules_engine.taxonomy import validate_scope
from schemas.models import ScopePackages, TenderPackage

_SYSTEM = (
    "You are a quantity-surveying assistant for a Hong Kong main contractor. "
    "Read the tender documents (Method of Measurement, Particular Specification, "
    "Tender Addendum, Schedule of Rates) and SPLIT the works into one package per "
    "trade. For each trade return a concise scope_summary, the relevant Schedule-of-"
    "Rates items (item_ref, description, unit, qty), and source_refs naming which "
    "document each item came from. Use Hong Kong construction trade names. "
    "You ONLY split and extract scope — you never price the work, never invent a "
    "quantity or rate, and never judge or rank a subcontractor. Return JSON matching "
    "the ScopePackages schema."
)


def _user_prompt(tender: TenderPackage) -> str:
    docs = "\n".join(f"- {d.doc_type.value}: {d.filename}" for d in tender.documents)
    return (
        f"Project: {tender.project_name}\n"
        f"Description: {tender.description}\n"
        f"Tender documents:\n{docs}\n\n"
        "Split this tender into trade work packages."
    )


def ingest_tender(
    tender: TenderPackage,
    demo_fixture: Optional[str] = None,
    *,
    client: Optional[LLMClient] = None,
    images: Optional[list[str]] = None,
) -> ScopePackages:
    """Split ``tender`` into one :class:`TradeWorkPackage` per trade.

    In DEMO_MODE the split is read from ``demo_fixture``; otherwise Layer 2 produces
    it (reading ``images`` — rendered tender pages — when given, for the live upload
    path). Either way Layer 1 normalises trades against the taxonomy before returning.
    """
    client = client or LLMClient()
    scope = client.complete_json(
        system=_SYSTEM,
        user=_user_prompt(tender),
        target_model=ScopePackages,
        demo_fixture=demo_fixture,
        images=images,
    )
    normalised, unmapped = validate_scope(scope)
    if unmapped:
        # Surfaced, not dropped — a human reconciles these against the taxonomy.
        print(f"[ingest] unmapped trades (kept for review): {unmapped}")
    return normalised
