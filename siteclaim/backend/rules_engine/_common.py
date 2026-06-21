"""Shared internals for the rules engine (private — not a public API).

Generic primitives only. The deterministic modules added in later phases
(risk scoring, ranking, leveling) build typed findings from ``schemas.models``
(RiskFlag, ArithmeticFinding, …); the only thing they share here is the
severity ordering used to sort those findings.
"""

from schemas.models import Severity

# Lower rank sorts first: fatal -> warning -> info.
SEVERITY_RANK: dict[Severity, int] = {
    Severity.FATAL: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}
