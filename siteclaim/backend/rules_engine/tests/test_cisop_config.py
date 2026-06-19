"""Smoke tests for the statutory config module.

These deliberately do **not** assert the legal *correctness* of any value — that
requires a quantity surveyor or construction lawyer (see the module header). They
only guard the module's *shape* so later Rules Engine code can rely on it: that
the warning is present, that periods are positive integers, that the threshold is
a positive :class:`~decimal.Decimal`, and that the mandatory-particular keys line
up with the schema fields Stage 02 will check.

Run from the ``backend/`` directory:  ``pytest``
"""

from decimal import Decimal

from rules_engine import cisop_config as cfg


def test_warning_constant_is_loud() -> None:
    text = cfg.STATUTORY_WARNING.upper()
    assert "UNVERIFIED" in text or "VALIDATE" in text


def test_core_periods_are_positive_ints() -> None:
    for value in (
        cfg.PAYMENT_RESPONSE_PERIOD_CALENDAR_DAYS,
        cfg.PAYMENT_DUE_PERIOD_CALENDAR_DAYS,
        cfg.ADJUDICATION_DETERMINATION_WORKING_DAYS,
        cfg.MIN_DAYS_BETWEEN_CLAIMS,
    ):
        assert isinstance(value, int) and value > 0


def test_private_sector_threshold_is_positive_decimal() -> None:
    assert isinstance(cfg.PRIVATE_SECTOR_THRESHOLD_HKD, Decimal)
    assert cfg.PRIVATE_SECTOR_THRESHOLD_HKD > 0


def test_mandatory_particulars_align_with_schema_keys() -> None:
    keys = {key for key, _description in cfg.MANDATORY_CLAIM_PARTICULARS}
    # A few load-bearing particulars that Stage 02 will assert are present.
    assert {"claimed_amount", "reference_date", "statutory_statement"} <= keys


def test_threshold_lookup_covers_known_contract_types() -> None:
    assert "main_construction" in cfg.THRESHOLD_BY_CONTRACT_TYPE
    assert all(
        isinstance(v, Decimal) for v in cfg.THRESHOLD_BY_CONTRACT_TYPE.values()
    )
