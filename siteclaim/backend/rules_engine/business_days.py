"""Day-count helpers for SOPO deadline arithmetic (Layer 1, deterministic).

The Construction Industry Security of Payment Ordinance (Cap. 652) mixes
**CALENDAR days** and **WORKING days**, and the distinction is legally
load-bearing: e.g. the s.20 payment-response period runs in calendar days, while
the s.25(3) ANB-service period runs in working days. These helpers keep the two
kinds of arithmetic explicit and separate so a caller can never accidentally
treat one as the other — pair ``*_DAYS`` constants with
:func:`add_calendar_days` and ``*_WORKING_DAYS`` constants with
:func:`add_working_days`.

WORKING-day results are only as correct as the (still UNVERIFIED) inputs in
:mod:`rules_engine.sopo_config`: ``WEEKEND_DAYS`` — in particular whether
Saturdays count — and ``PUBLIC_HOLIDAYS``, which is currently empty.
"""

from collections.abc import Iterable
from datetime import date, timedelta

from . import sopo_config


def add_calendar_days(start: date, n: int) -> date:
    """Return ``start`` plus ``n`` CALENDAR days (weekends and holidays included).

    ``n`` may be negative to move backwards.
    """
    return start + timedelta(days=n)


def is_working_day(day: date, holidays: Iterable[date] = ()) -> bool:
    """True if ``day`` is a working day: not a weekend and not a public holiday."""
    if day.weekday() in sopo_config.WEEKEND_DAYS:
        return False
    return day not in set(holidays)


def add_working_days(start: date, n: int, holidays: Iterable[date] = ()) -> date:
    """Return the date ``n`` WORKING days after ``start``.

    Days falling on a weekend (``sopo_config.WEEKEND_DAYS``) or in ``holidays``
    are skipped and not counted. ``n`` must be non-negative; ``n == 0`` returns
    ``start`` unchanged (even if ``start`` itself is not a working day).
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    holiday_set = set(holidays)
    current = start
    counted = 0
    while counted < n:
        current += timedelta(days=1)
        if current.weekday() not in sopo_config.WEEKEND_DAYS and current not in holiday_set:
            counted += 1
    return current


def working_days_between(start: date, end: date, holidays: Iterable[date] = ()) -> int:
    """Count WORKING days from ``start`` to ``end``, exclusive of ``start``.

    Returns a positive count when ``end`` is after ``start`` (the number of
    working days you would step through to reach ``end``), ``0`` when equal, and
    a negative count when ``end`` is before ``start``. Useful for a
    'business days remaining until a deadline' figure.
    """
    if end == start:
        return 0
    step = 1 if end > start else -1
    holiday_set = set(holidays)
    count = 0
    current = start
    while current != end:
        current += timedelta(days=step)
        if current.weekday() not in sopo_config.WEEKEND_DAYS and current not in holiday_set:
            count += step
    return count


__all__ = [
    "add_calendar_days",
    "is_working_day",
    "add_working_days",
    "working_days_between",
]
