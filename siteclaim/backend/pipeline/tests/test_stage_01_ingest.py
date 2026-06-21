"""Stage 01 ingest — DEMO_MODE splits the tender and Layer 1 validates the trades.

DEMO_MODE is forced on by the autouse fixture in ``pipeline/tests/conftest.py``, so
this runs fully offline against the baked fixture.
"""

from pipeline.stage_01_ingest.ingest import ingest_tender
from rules_engine.taxonomy import CANONICAL_TRADES
from schemas.models import DocType, ScopePackages, TenderDocument, TenderPackage

_FIXTURE = "cases/clean/scope_packages.json"


def _tender() -> TenderPackage:
    return TenderPackage(
        project_name="Kwun Tong Commercial Tower — Category-A Office Fit-out",
        description="Cat-A office fit-out across 12 floors.",
        documents=[
            TenderDocument(doc_type=DocType.METHOD_OF_MEASUREMENT, filename="method_of_measurement.pdf"),
            TenderDocument(doc_type=DocType.PARTICULAR_SPECIFICATION, filename="particular_specification.pdf"),
            TenderDocument(doc_type=DocType.TENDER_ADDENDUM, filename="tender_addendum.pdf"),
            TenderDocument(doc_type=DocType.SCHEDULE_OF_RATES, filename="schedule_of_rates.pdf"),
        ],
    )


def test_ingest_returns_scope_packages():
    scope = ingest_tender(_tender(), demo_fixture=_FIXTURE)
    assert isinstance(scope, ScopePackages)
    assert scope.project_name.startswith("Kwun Tong")


def test_ingest_splits_into_at_least_four_trades_including_electrical():
    scope = ingest_tender(_tender(), demo_fixture=_FIXTURE)
    trades = [pkg.trade for pkg in scope.packages]
    assert len(trades) >= 4
    assert "electrical" in trades


def test_every_trade_is_canonical_after_validation():
    # The fixture uses real-world labels ("Mechanical & Plumbing", "Fire Services");
    # Layer 1 normalises them all to canonical taxonomy keys.
    scope = ingest_tender(_tender(), demo_fixture=_FIXTURE)
    assert all(pkg.trade in CANONICAL_TRADES for pkg in scope.packages)
    assert {"electrical", "mechanical_plumbing", "fire_services", "joinery_fitting_out"} <= {
        pkg.trade for pkg in scope.packages
    }


def test_scope_items_and_sources_survive_the_split():
    scope = ingest_tender(_tender(), demo_fixture=_FIXTURE)
    electrical = next(pkg for pkg in scope.packages if pkg.trade == "electrical")
    assert electrical.sor_items and electrical.sor_items[0].qty > 0
    assert electrical.source_refs  # each package cites which tender document it came from
