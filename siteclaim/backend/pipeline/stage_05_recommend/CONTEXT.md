# Stage 05 — Recommend (Layer 1 ranking, Layer 2 narration, Layer 4 award)

## Inputs
- `list[LevelledBid]` for a trade, plus the database (track record, bid
  distribution, historical pricing).

## Process
Layer 1 ranks firms by `corrected_total` but reads each against the database: risk
flags from the firm profile, the bid distribution across the levelled bids, and
`historical_pricing(trade)` low/median/high. A firm with a **fatal** flag is
`recommended_against` regardless of price; `recommended_firm_id` is the best clean
firm. Layer 2 narrates the rationale given the deterministic ranking — it does not
pick the winner. Layer 4 records the human award/override.

## Outputs
- `Recommendation` — ranked firms, chosen firm, rationale, bid distribution,
  historical band.
