# Stage 02 — Shortlist (Layer 1 cross-reference over the database)

## Inputs
- `ScopePackages` and the proprietary database (`backend/db/`).

## Process
Pure Layer 1, the demo hero. For each `TradeWorkPackage`, the database join
(`db/cross_reference.py`) returns `Candidate`s: firms that do the trade, scored by
semantic relevance of their closeout history to the scope, each with cited
`Evidence` and `RiskFlag`s from `risk_scoring`. `ranking.py` then orders them,
demoting or excluding firms with **fatal** flags regardless of price. The LLM does
not rank. The DB is offline, so DEMO_MODE needs no LLM call.

## Outputs
- `ShortlistSet` — `per_trade` ranked `Candidate`s with attached, citable evidence.
