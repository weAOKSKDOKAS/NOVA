"""Tests for the CALENDAR-vs-WORKING day helpers.

The distinction these guard is legally load-bearing (e.g. SOPO s.20 runs in
calendar days, s.25(3) in working days). Anchor dates are verified weekdays:
2026-06-19 is a Friday, 2026-06-20 a Saturday, 2026-06-22 a Monday.
"""

from datetime import date

from rules_engine import business_days as bd

FRIDAY = date(2026, 6, 19)
SATURDAY = date(2026, 6, 20)
MONDAY = date(2026, 6, 22)


def test_anchor_weekdays() -> None:
    assert FRIDAY.weekday() == 4 and SATURDAY.weekday() == 5 and MONDAY.weekday() == 0


def test_add_calendar_days_includes_weekend() -> None:
    # Friday + 3 calendar days = Monday (Sat/Sun counted).
    assert bd.add_calendar_days(FRIDAY, 3) == MONDAY
    assert bd.add_calendar_days(FRIDAY, 0) == FRIDAY
    assert bd.add_calendar_days(MONDAY, -3) == FRIDAY


def test_add_working_days_skips_weekend() -> None:
    # Friday + 1 working day = Monday (skips Sat/Sun); 0 leaves it unchanged.
    assert bd.add_working_days(FRIDAY, 1) == MONDAY
    assert bd.add_working_days(FRIDAY, 0) == FRIDAY


def test_add_working_days_skips_holiday() -> None:
    # With Monday a holiday, Friday + 1 working day rolls to Tuesday.
    tuesday = date(2026, 6, 23)
    assert bd.add_working_days(FRIDAY, 1, holidays=[MONDAY]) == tuesday


def test_add_working_days_rejects_negative() -> None:
    import pytest

    with pytest.raises(ValueError):
        bd.add_working_days(FRIDAY, -1)


def test_is_working_day() -> None:
    assert bd.is_working_day(FRIDAY) is True
    assert bd.is_working_day(SATURDAY) is False
    assert bd.is_working_day(MONDAY, holidays=[MONDAY]) is False


def test_working_days_between() -> None:
    # Friday -> Monday crosses the weekend: exactly 1 working day.
    assert bd.working_days_between(FRIDAY, MONDAY) == 1
    assert bd.working_days_between(FRIDAY, FRIDAY) == 0
    assert bd.working_days_between(MONDAY, FRIDAY) == -1
