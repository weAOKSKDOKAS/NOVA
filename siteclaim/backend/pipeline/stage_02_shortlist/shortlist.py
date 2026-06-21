"""Stage 02 — shortlist: ScopePackages + database -> ShortlistSet.

The demo hero. Pure Layer 1 cross-reference: for each trade, the database returns
candidate firms scored by semantic relevance of their closeout history, each
carrying cited evidence and risk flags; the ranking module demotes/excludes firms
with fatal flags regardless of price. The LLM is not asked to rank. Phase 4.
"""
