"""Pipeline test fixtures — everything runs in DEMO_MODE (offline, zero network).

Stage-specific case loaders are added back as the stage fixtures land (Phase 3+).
"""

import pytest


@pytest.fixture(autouse=True)
def _force_demo_mode(monkeypatch):
    """Every pipeline test runs offline against canned fixtures."""
    monkeypatch.setenv("DEMO_MODE", "true")
