"""Stage 05 — recommend: LevelledBids + database -> Recommendation.

Layer 1 ranks by corrected total but reads each firm against the database (risk
flags, bid distribution, historical pricing low/median/high); a firm with a fatal
flag is `recommended_against` regardless of price, and the best clean firm wins.
Layer 2 only narrates the rationale — it never chooses the winner. Layer 4 records
the human award/override. Phase 7.
"""
