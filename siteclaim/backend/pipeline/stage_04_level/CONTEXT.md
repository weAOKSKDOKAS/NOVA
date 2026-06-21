# Stage 04 — Level (Layer 2 parse, Layer 1 arithmetic, Excel export)

## Inputs
- `list[BidReply]` (returned Schedules of Rates) and the `ScopePackages` basis.

## Process
Layer 2 parses each reply into line items, rates, and exclusions. Layer 1
(`rules_engine/leveling.py`, following `references/rubrics/leveling_rules.md`)
recomputes each amount as `qty x rate`, sums to `corrected_total`, records an
`ArithmeticFinding` per disagreeing line, treats a missing rate as a `scope_gap`
and a stated exclusion as a flagged non-comparable item, and never silently fills
a missing provisional sum. `normalized_total` puts every bid on the same basis.
An `openpyxl` export writes the comparison to `fixtures/out/leveling.xlsx`.

## Outputs
- `list[LevelledBid]` — corrected totals, arithmetic findings, exclusions, gaps.
