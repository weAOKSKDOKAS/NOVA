"""Layer 1 — the deterministic rules engine (SiteSource).

Pure-Python and deterministic: bid-leveling arithmetic, risk scoring, and
candidate ranking. **No ML, no LLM** lives here. The deterministic modules
(``risk_scoring``, ``ranking``, ``leveling``) are added in later phases; this
package currently exposes only the generic primitives in ``_common``.
"""
