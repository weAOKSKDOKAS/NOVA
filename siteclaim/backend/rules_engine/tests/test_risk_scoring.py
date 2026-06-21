"""Deterministic risk scoring — the rubric, exercised rule by rule, no DB."""

from schemas.models import Evidence, FirmProfile, RiskFlag, Severity, SignalType
from rules_engine.risk_scoring import score_firm


def _raw(signal: SignalType, label: str = "x", ref: str = "REF:1") -> RiskFlag:
    """A raw, unadjudicated signal as the store would hand it to the engine."""
    return RiskFlag(
        severity=Severity.INFO,
        label=label,
        rule_ref=f"signal.{signal.value}",
        evidence=[Evidence(source="src", signal_type=signal, snippet=label, reference=ref)],
    )


def _firm(grade="REC (EMSD)", band="up_to_50m", flags=None) -> FirmProfile:
    return FirmProfile(
        firm_id="F-T-01", name="Test Co", registered_grade=grade, value_band=band,
        trades=["electrical"], public_flags=flags or [],
    )


def _refs(flags):
    return {(f.severity, f.rule_ref) for f in flags}


def test_winding_up_is_fatal():
    flags = score_firm(_firm(flags=[_raw(SignalType.WINDING_UP)]))
    assert (Severity.FATAL, "risk.winding_up") in _refs(flags)


def test_two_safety_prosecutions_are_fatal():
    flags = score_firm(_firm(flags=[_raw(SignalType.SAFETY_PROSECUTION), _raw(SignalType.SAFETY_PROSECUTION)]))
    fatal = [f for f in flags if f.rule_ref == "risk.safety_prosecutions"]
    assert fatal and fatal[0].severity is Severity.FATAL
    assert len(fatal[0].evidence) == 2  # both convictions carried as evidence


def test_one_safety_prosecution_is_a_warning():
    flags = score_firm(_firm(flags=[_raw(SignalType.SAFETY_PROSECUTION)]))
    assert (Severity.WARNING, "risk.safety_single") in _refs(flags)
    assert (Severity.FATAL, "risk.safety_prosecutions") not in _refs(flags)


def test_debarment_and_adjudication_are_fatal():
    flags = score_firm(_firm(flags=[_raw(SignalType.DEBARMENT), _raw(SignalType.ADJUDICATION)]))
    assert (Severity.FATAL, "risk.debarment") in _refs(flags)
    assert (Severity.FATAL, "risk.adjudication_unpaid") in _refs(flags)


def test_distress_and_closeout_are_warnings():
    flags = score_firm(_firm(flags=[_raw(SignalType.DISTRESS_FILING), _raw(SignalType.CLOSEOUT_PERFORMANCE)]))
    assert (Severity.WARNING, "risk.distress_filing") in _refs(flags)
    assert (Severity.WARNING, "risk.closeout_delay") in _refs(flags)


def test_grade_band_warns_when_grade_low_for_band():
    flags = score_firm(_firm(grade="Group A", band="above_200m"))
    assert (Severity.WARNING, "risk.grade_band") in _refs(flags)
    # an adequate grade for the band does not warn
    assert not _refs(score_firm(_firm(grade="Group C", band="up_to_50m")))


def test_specialist_grade_does_not_trigger_grade_band():
    # REC/RFC specialists are off the Group ladder — no false grade_band flag.
    assert not _refs(score_firm(_firm(grade="REC (EMSD)", band="above_200m")))


def test_clean_firm_has_no_flags():
    assert score_firm(_firm()) == []


def test_flags_are_sorted_fatal_first():
    flags = score_firm(_firm(flags=[_raw(SignalType.CLOSEOUT_PERFORMANCE), _raw(SignalType.WINDING_UP)]))
    assert flags[0].severity is Severity.FATAL


def test_scoring_is_idempotent():
    firm = _firm(flags=[_raw(SignalType.WINDING_UP), _raw(SignalType.SAFETY_PROSECUTION), _raw(SignalType.SAFETY_PROSECUTION)])
    once = score_firm(firm)
    # feed the adjudicated flags back in: same verdict (keys off evidence.signal_type)
    twice = score_firm(firm.model_copy(update={"public_flags": once}))
    assert _refs(once) == _refs(twice)
