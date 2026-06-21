"""Deterministic firm risk scoring (Layer 1).

Implements ``references/rubrics/risk_scoring.md``. Given a :class:`FirmProfile`
whose ``public_flags`` carry *raw, unadjudicated* signals (each with cited
:class:`Evidence` and an ``Evidence.signal_type``), return the adjudicated
:class:`RiskFlag` list with real severities. Pure Python — no LLM, no DB, no ML.

The function keys off ``Evidence.signal_type`` (a stable fact), not off any
severity already on the input flags, so it is **idempotent**: re-scoring an
already-scored profile yields the same flags. Severity is decided here and
*nowhere else* — the database reports facts; this engine adjudicates them.
"""

from __future__ import annotations

from schemas.models import Evidence, FirmProfile, RiskFlag, Severity, SignalType
from rules_engine._common import SEVERITY_RANK

# Approved-contractor group ladder (lowest capacity -> highest) and the minimum
# group rank a value band needs. Specialist registers (REC/RFC/…) are not on this
# ladder and are treated as adequate (no grade_band flag).
_GROUP_RANK = {"group a": 1, "group b": 2, "group c": 3}
_BAND_MIN_RANK = {"up_to_50m": 1, "50m_to_200m": 2, "above_200m": 3}


def _collect(firm: FirmProfile) -> dict[SignalType, list[Evidence]]:
    """Group every piece of evidence across the firm's flags by its signal type."""
    by_type: dict[SignalType, list[Evidence]] = {}
    for flag in firm.public_flags:
        for ev in flag.evidence:
            by_type.setdefault(ev.signal_type, []).append(ev)
    return by_type


def _grade_band_flag(firm: FirmProfile) -> RiskFlag | None:
    grade_rank = _GROUP_RANK.get((firm.registered_grade or "").strip().lower())
    band_rank = _BAND_MIN_RANK.get((firm.value_band or "").strip().lower())
    if grade_rank is None or band_rank is None or grade_rank >= band_rank:
        return None
    snippet = (
        f"Registered grade {firm.registered_grade!r} is below what the "
        f"{firm.value_band!r} value band typically requires."
    )
    return RiskFlag(
        severity=Severity.WARNING,
        label="Registered grade low for value band",
        rule_ref="risk.grade_band",
        evidence=[Evidence(source="Registry grade vs value band", signal_type=SignalType.GRADE, snippet=snippet, reference=f"GRADE:{firm.firm_id}")],
    )


def score_firm(firm: FirmProfile) -> list[RiskFlag]:
    """Return the adjudicated risk flags for ``firm``, sorted fatal -> warning -> info."""
    signals = _collect(firm)
    flags: list[RiskFlag] = []

    # -- Fatal rules (do not award regardless of price) ---------------------
    if SignalType.WINDING_UP in signals:
        flags.append(RiskFlag(
            severity=Severity.FATAL, label="Active winding-up petition",
            rule_ref="risk.winding_up", evidence=signals[SignalType.WINDING_UP],
        ))
    if SignalType.ADJUDICATION in signals:
        flags.append(RiskFlag(
            severity=Severity.FATAL, label="Unpaid adjudication determination",
            rule_ref="risk.adjudication_unpaid", evidence=signals[SignalType.ADJUDICATION],
        ))
    if SignalType.DEBARMENT in signals:
        flags.append(RiskFlag(
            severity=Severity.FATAL, label="Debarred from public works",
            rule_ref="risk.debarment", evidence=signals[SignalType.DEBARMENT],
        ))

    safety = signals.get(SignalType.SAFETY_PROSECUTION, [])
    if len(safety) >= 2:
        flags.append(RiskFlag(
            severity=Severity.FATAL,
            label=f"{len(safety)} safety-prosecution convictions",
            rule_ref="risk.safety_prosecutions", evidence=safety,
        ))
    elif len(safety) == 1:
        flags.append(RiskFlag(
            severity=Severity.WARNING, label="One safety-prosecution conviction",
            rule_ref="risk.safety_single", evidence=safety,
        ))

    # -- Warning rules (surface for the human to weigh) ---------------------
    if SignalType.DISTRESS_FILING in signals:
        flags.append(RiskFlag(
            severity=Severity.WARNING, label="Financial-distress filing",
            rule_ref="risk.distress_filing", evidence=signals[SignalType.DISTRESS_FILING],
        ))
    if SignalType.CLOSEOUT_PERFORMANCE in signals:
        flags.append(RiskFlag(
            severity=Severity.WARNING, label="Delayed-closeout note in project history",
            rule_ref="risk.closeout_delay", evidence=signals[SignalType.CLOSEOUT_PERFORMANCE],
        ))
    grade_band = _grade_band_flag(firm)
    if grade_band is not None:
        flags.append(grade_band)

    flags.sort(key=lambda f: SEVERITY_RANK[f.severity])
    return flags


def has_fatal(flags: list[RiskFlag]) -> bool:
    """True if any flag is fatal (used by ranking to demote regardless of price)."""
    return any(flag.severity is Severity.FATAL for flag in flags)
