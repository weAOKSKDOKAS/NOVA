# Leveling Rules — deterministic bid normalisation (v1)

These rules are applied by `rules_engine/leveling.py` (pure Python). The LLM parses
a reply into a `BidReply`; **every calculation and judgment below is Layer 1**, never
the model. The goal is to put every bid on the same scope basis so prices are
comparable.

## Arithmetic
1. **Recompute every amount** as `amount = qty x rate`. Do not trust the bidder's
   stated amount.
2. Where the bidder's stated amount disagrees with `qty x rate`, record an
   `ArithmeticFinding` (severity `warning`) with the corrected value and use the
   corrected value.
3. **`corrected_total`** = the sum of the recomputed line amounts.
4. `claimed_total` (the bidder's own total) is recorded but never used for ranking.

## Scope gaps and exclusions
5. A line with a **missing rate** is a **scope gap** — record it in `scope_gaps`;
   do not treat the line as zero.
6. A **stated exclusion** is a flagged, **non-comparable** item (a deduction that
   is not like-for-like) — record it in `exclusions`; it does not silently lower
   the price.
7. **Never silently fill a missing provisional sum.** A missing provisional sum is
   a scope gap, flagged, never assumed.

## Normalisation
8. `normalized_total` puts every bid on the **same scope basis** for comparison:
   start from `corrected_total`, then account for scope gaps and non-comparable
   exclusions so two bids are compared like-for-like. Differences in scope are
   surfaced, never absorbed.

Rules are versioned; bump the version when a rule is added or changed.
