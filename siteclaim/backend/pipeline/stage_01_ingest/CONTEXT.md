# Stage 01 — Ingest (Layer 2 split, Layer 1 taxonomy check)

## Inputs
- `TenderPackage` — the four tender documents (Method of Measurement, Particular
  Specification, Tender Addendum, Schedule of Rates).

## Process
Layer 2 (Claude) reads the documents and splits the scope into one
`TradeWorkPackage` per trade — a scope summary plus the relevant SoR items and
`source_refs`. It only splits and extracts; it never prices or judges a firm.
Layer 1 validates every returned trade against `references/rubrics/trade_taxonomy.md`
(deterministic; an off-taxonomy trade is mapped to the nearest canonical trade or
flagged). DEMO_MODE reads a baked `ScopePackages` fixture.

## Outputs
- `ScopePackages` — `project_name` + one `TradeWorkPackage` per trade.
