"""Stage 04 — level: BidReplies -> LevelledBids.

Layer 2 parses each returned Schedule of Rates into a `BidReply`. Layer 1
(`rules_engine/leveling.py`, pure Python) does every calculation: recompute each
amount as qty x rate, sum to a corrected total, record an `ArithmeticFinding`
where the bidder disagrees, treat a missing rate as a scope gap and a stated
exclusion as a non-comparable item, and never silently fill a missing provisional
sum. Exports the comparison to Excel (openpyxl). Phase 6.
"""
