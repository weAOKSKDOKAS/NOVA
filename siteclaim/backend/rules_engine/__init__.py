"""Layer 1 — the deterministic Rules Engine.

This package holds the **legally load-bearing** part of SiteClaim: pure-Python,
deterministic checks and deadline arithmetic. No machine learning lives here.
All statutory parameters are centralised in :mod:`rules_engine.sopo_config`, and
the CALENDAR-vs-WORKING day arithmetic that consumes them lives in
:mod:`rules_engine.business_days`.

Stage logic (validation, deadline computation, audit cross-checks) is added in
later phases; for now the statutory config and the day-count helpers are
populated.
"""

from . import business_days, sopo_config

__all__ = ["sopo_config", "business_days"]
