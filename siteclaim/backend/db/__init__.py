"""Layer 3 — the proprietary fused subcontractor database (the moat).

A hybrid store: SQLite (standard-library ``sqlite3``, no dependency) holds the
structured signals — registered grade, value band, trades, public flags
(Companies Registry winding-up / distress filings, Labour Department safety
prosecutions, debarment, unpaid adjudication), award history, per-project
closeouts, and historical trade pricing — and a ``closeout_embeddings`` table
holds one baked vector per closeout-text chunk so the *runtime never loads a
model or touches the network*. Similarity is cosine over those baked vectors.

The seed fuses two provenance-separated sources (``seed_data/eos`` — our private
closeout archive; ``seed_data/public`` — public-record signals) into one
``sitesource.db``. ``store`` and ``cross_reference`` only read the DB, so they
do not care whether a record came from the mock stub or a real scrape.
"""
