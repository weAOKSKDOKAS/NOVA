"""Stage 01 — ingest: TenderPackage -> ScopePackages.

Layer 2 (Claude) reads the four tender documents and splits the work into one
TradeWorkPackage per trade; Layer 1 validates each trade against
``references/rubrics/trade_taxonomy.md``. Implemented in Phase 3.
"""
