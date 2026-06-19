# ⚠️ STATUTORY PARAMETERS — VALIDATE EVERY VALUE WITH A QUANTITY SURVEYOR OR
# CONSTRUCTION LAWYER BEFORE RELYING ON OUTPUT. Values below are best-effort
# placeholders from secondary research.
#
# Phase 0b update — provenance now has TWO tiers; read before trusting anything:
#   * "# SOURCED (law-firm summary) — cross-check against e-legislation Cap.652
#     text" = grounded in a secondary law-firm summary of the Ordinance. Still
#     NOT read off the enacted text — cross-check before relying on it.
#   * "# UNVERIFIED ..." = best-effort placeholder, not yet sourced at all. Send
#     these to a QS / pull from e-legislation.
#   * Section numbers (e.g. "s.20") are as given by the source and INDICATIVE.
#
# DAY-COUNT CONVENTION (legally load-bearing — the Ordinance mixes both):
#   *_DAYS          -> CALENDAR days  (e.g. s.20 payment response runs in
#                      calendar days). Compute with business_days.add_calendar_days.
#   *_WORKING_DAYS  -> WORKING days, excluding weekends + HK public holidays
#                      (e.g. s.25(3) ANB service). Compute with
#                      business_days.add_working_days. Whether Saturdays count as
#                      working days under Cap.652 is still UNVERIFIED.
"""SiteClaim statutory parameters for SOPO — the Construction Industry Security
of Payment Ordinance (Cap. 652), Hong Kong.

This module is **Layer 1's single source of truth** for numbers and rules that
come from the statute. The deterministic Rules Engine imports these constants;
no other layer hard-codes a statutory value. Concentrating them here means a
quantity surveyor or construction lawyer can review one short, well-commented
file rather than hunting through the codebase.

Day arithmetic that consumes these constants lives in
:mod:`rules_engine.business_days`, which keeps CALENDAR-day and WORKING-day
maths explicitly separate (see the DAY-COUNT CONVENTION header above).

Nothing in this module is legal advice. SOURCED values are grounded in a
secondary law-firm summary and must still be cross-checked against the enacted
Cap.652 text; UNVERIFIED values are unconfirmed placeholders.
"""

from decimal import Decimal
from typing import Final

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
CONFIG_VERSION: Final[str] = "0.1.0-sourced"  # bump when any value below changes
STATUTORY_SOURCE: Final[str] = (
    "Construction Industry Security of Payment Ordinance (Cap. 652), Hong Kong. "
    "Time bars and thresholds SOURCED from a secondary law-firm summary; NOT yet "
    "verified against the e-legislation Cap.652 text."
)
COMMENCEMENT_DATE: Final[str] = "2025-08-28"  # applies to contracts entered on/after this date. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text

# Importable copy of the header warning so the API / UI can surface it at runtime
# and no client can quietly hide it from the user.
STATUTORY_WARNING: Final[str] = (
    "STATUTORY PARAMETERS ARE NOT VERIFIED AGAINST THE ENACTED ORDINANCE. "
    "Validate every value with a quantity surveyor or construction lawyer, and "
    "cross-check against the e-legislation Cap.652 text, before relying on output."
)

# ---------------------------------------------------------------------------
# Calendar / business-day definitions (inputs to business_days helpers)
# ---------------------------------------------------------------------------
# Python ``date.weekday()`` indices treated as NON-working days (5 = Sat, 6 = Sun).
WEEKEND_DAYS: Final[tuple[int, ...]] = (5, 6)  # UNVERIFIED — confirm whether Saturdays count as working days under Cap.652

# Hong Kong general/public holidays must be loaded from a maintained source
# (Layer 3) before any WORKING-day arithmetic can be trusted. Empty on purpose.
PUBLIC_HOLIDAYS: Final[tuple[str, ...]] = ()  # UNVERIFIED — load official gazette holidays (ISO date strings)

# ---------------------------------------------------------------------------
# SOURCED time bars — payment mechanism (CALENDAR days)
# ---------------------------------------------------------------------------
PAYMENT_RESPONSE_DAYS: Final[int] = 30  # s.20 (calendar days) — statutory max; contract may specify shorter. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
MAX_PAYMENT_DEADLINE_DAYS: Final[int] = 60  # (calendar days) — parties may agree earlier. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text

# ---------------------------------------------------------------------------
# SOURCED time bars — adjudication mechanism (note CALENDAR vs WORKING per name)
# ---------------------------------------------------------------------------
ADJUDICATION_INIT_DAYS: Final[int] = 28  # s.24 (calendar days) — from date the payment dispute arises. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
ANB_SERVICE_WORKING_DAYS: Final[int] = 8  # s.25(3) (working days) — if no/more-than-one ANB (Adjudicator Nominating Body) specified. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
ADJUDICATOR_APPOINTMENT_WORKING_DAYS: Final[int] = 7  # (working days) — section not stated in source. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
DETERMINATION_DAYS: Final[int] = 55  # s.42(5) — after adjudicator appointed. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text  [NOTE: calendar vs working days to confirm — name follows the source]
PAY_ADJUDICATED_AMOUNT_DAYS: Final[int] = 30  # s.43 / s.42(7) (calendar days) — if adjudicator unspecified. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text

# ---------------------------------------------------------------------------
# SOURCED monetary thresholds (HKD)
# ---------------------------------------------------------------------------
THRESHOLD_CONSTRUCTION_HKD: Final[Decimal] = Decimal(5_000_000)  # main contract construction work. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
THRESHOLD_GOODS_SERVICES_HKD: Final[Decimal] = Decimal(500_000)  # related goods/services. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
COURT_ROUTING_THRESHOLD_HKD: Final[Decimal] = Decimal(3_000_000)  # >CFI / <District Court (Rules Cap.652A) — enforcement routing. SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text

# Convenience lookup keyed by ``schemas.models.ContractType`` values.
THRESHOLD_BY_CONTRACT_TYPE: Final[dict[str, Decimal]] = {
    "main_construction": THRESHOLD_CONSTRUCTION_HKD,  # SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
    "supply_goods_and_services": THRESHOLD_GOODS_SERVICES_HKD,  # SOURCED (law-firm summary) — cross-check against e-legislation Cap.652 text
    "subcontract_construction": Decimal(0),  # believed covered regardless of value — UNVERIFIED — confirm with Cap.652 text/QS
    "consultancy": THRESHOLD_GOODS_SERVICES_HKD,  # UNVERIFIED — classification unclear; confirm with Cap.652 text/QS
}

# ===========================================================================
# UNVERIFIED placeholders — NOT yet sourced. Send to a QS / pull from
# e-legislation, then move up into the SOURCED sections above.
# ===========================================================================
MIN_DAYS_BETWEEN_CLAIMS: Final[int] = 30  # (calendar days) — UNVERIFIED — confirm with Cap.652 text/QS
DEFAULT_REFERENCE_DATE_INTERVAL_DAYS: Final[int] = 30  # (calendar days) — UNVERIFIED — confirm with Cap.652 text/QS
CLAIM_LONGSTOP_AFTER_COMPLETION_DAYS: Final[int] = 540  # ~18 months (calendar days) — UNVERIFIED — confirm with Cap.652 text/QS
DETERMINATION_EXTENSION_WORKING_DAYS: Final[int] = 10  # extra time by agreement — UNVERIFIED — confirm with Cap.652 text/QS
DEEMED_SERVICE_DAYS_BY_POST: Final[int] = 2  # (calendar days) added on postal service — UNVERIFIED — confirm with Cap.652 text/QS
SUBCONTRACT_HAS_OWN_THRESHOLD: Final[bool] = False  # UNVERIFIED — confirm with Cap.652 text/QS
PERMITTED_SERVICE_METHODS: Final[tuple[str, ...]] = (
    "personal_delivery",  # UNVERIFIED — confirm with Cap.652 text/QS
    "post_to_last_known_address",  # UNVERIFIED — confirm with Cap.652 text/QS
    "email_if_agreed",  # UNVERIFIED — confirm with Cap.652 text/QS
    "contractual_method",  # UNVERIFIED — confirm with Cap.652 text/QS
)

# ---------------------------------------------------------------------------
# Mandatory payment-claim particulars — s.18 content requirements
# ---------------------------------------------------------------------------
# TODO(s.18): the exact required content of a payment claim must be read off the
# Cap.652 text before being encoded. Left intentionally EMPTY so Stage 02 cannot
# silently validate against guessed fields. Do not populate without the enacted
# section text. Each future entry: (key_aligned_to_schema_field, description).
MANDATORY_CLAIM_PARTICULARS: Final[tuple[tuple[str, str], ...]] = ()  # TODO(s.18) — confirm exact fields from Cap.652 text before encoding


__all__ = [
    "CONFIG_VERSION",
    "STATUTORY_SOURCE",
    "COMMENCEMENT_DATE",
    "STATUTORY_WARNING",
    "WEEKEND_DAYS",
    "PUBLIC_HOLIDAYS",
    "PAYMENT_RESPONSE_DAYS",
    "MAX_PAYMENT_DEADLINE_DAYS",
    "ADJUDICATION_INIT_DAYS",
    "ANB_SERVICE_WORKING_DAYS",
    "ADJUDICATOR_APPOINTMENT_WORKING_DAYS",
    "DETERMINATION_DAYS",
    "PAY_ADJUDICATED_AMOUNT_DAYS",
    "THRESHOLD_CONSTRUCTION_HKD",
    "THRESHOLD_GOODS_SERVICES_HKD",
    "COURT_ROUTING_THRESHOLD_HKD",
    "THRESHOLD_BY_CONTRACT_TYPE",
    "MIN_DAYS_BETWEEN_CLAIMS",
    "DEFAULT_REFERENCE_DATE_INTERVAL_DAYS",
    "CLAIM_LONGSTOP_AFTER_COMPLETION_DAYS",
    "DETERMINATION_EXTENSION_WORKING_DAYS",
    "DEEMED_SERVICE_DAYS_BY_POST",
    "SUBCONTRACT_HAS_OWN_THRESHOLD",
    "PERMITTED_SERVICE_METHODS",
    "MANDATORY_CLAIM_PARTICULARS",
]
