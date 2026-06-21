"""Rules engine entry point (Layer 1, deterministic — NO LLM).

The single place that composes the deterministic modules. In SiteSource the work
splits across ``risk_scoring`` (firm risk flags), ``ranking`` (risk-adjusted
candidate ordering), and ``leveling`` (bid arithmetic) — repointed here as those
modules land in later phases. Kept as the import-stable entry point so the
package always imports.
"""
