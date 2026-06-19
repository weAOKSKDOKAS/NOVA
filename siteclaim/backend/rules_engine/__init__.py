"""Layer 1 — the deterministic Rules Engine.

This package holds the **legally load-bearing** part of SiteClaim: pure-Python,
deterministic checks and deadline arithmetic. No machine learning lives here.
All statutory parameters are centralised in :mod:`rules_engine.cisop_config`.

Stage logic (validation, deadline computation, audit cross-checks) is added in
later phases; for now only the statutory config is populated.
"""

from . import cisop_config

__all__ = ["cisop_config"]
