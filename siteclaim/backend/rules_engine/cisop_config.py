# ⚠️ STATUTORY PARAMETERS — VALIDATE EVERY VALUE WITH A QUANTITY SURVEYOR OR
# CONSTRUCTION LAWYER BEFORE RELYING ON OUTPUT. Values below are best-effort
# placeholders from secondary research.
#
# Provenance notes (read before trusting anything here):
#   * Section numbers (e.g. "s.13") are INDICATIVE and must be confirmed against
#     the enacted text of the Construction Industry Security of Payment Ordinance
#     ("CISOP", Hong Kong). They are tagged ``# UNVERIFIED`` where uncertain.
#   * Whether a period runs in CALENDAR days or WORKING days is itself a frequent
#     source of error; each constant states which, and is tagged ``# UNVERIFIED``
#     until confirmed.
#   * Monetary thresholds and the public/private distinction must be checked
#     against the Ordinance's application provisions and any commencement notice.
"""SiteClaim statutory parameters for the CISOP (Hong Kong).

This module is **Layer 1's single source of truth** for numbers and rules that
come from the statute. The deterministic Rules Engine imports these constants;
no other layer hard-codes a statutory value. Concentrating them here means a
quantity surveyor or construction lawyer can review one short, well-commented
file rather than hunting through the codebase.

Nothing in this module is legal advice. Every value is an unverified placeholder
until signed off by a qualified professional.
"""

from decimal import Decimal
from typing import Final

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
CONFIG_VERSION: Final[str] = "0.0.0-draft"  # bump when any value below changes
STATUTORY_SOURCE: Final[str] = (
    "Construction Industry Security of Payment Ordinance (Hong Kong) — "
    "secondary-research placeholders, NOT verified against the enacted text."
)

# Importable copy of the header warning so the API / UI can surface it at runtime
# and no client can quietly hide it from the user.
STATUTORY_WARNING: Final[str] = (
    "STATUTORY PARAMETERS ARE UNVERIFIED PLACEHOLDERS. Validate every value with "
    "a quantity surveyor or construction lawyer before relying on output."
)

# ---------------------------------------------------------------------------
# Calendar / business-day definitions
# ---------------------------------------------------------------------------
# Python ``date.weekday()`` indices that are NOT business days (5 = Sat, 6 = Sun).
WEEKEND_DAYS: Final[tuple[int, ...]] = (5, 6)  # UNVERIFIED — confirm 6-day weeks don't apply

# Hong Kong general/public holidays must be loaded from a maintained source
# (Layer 3) before any working-day arithmetic is trusted. Empty on purpose.
PUBLIC_HOLIDAYS: Final[tuple[str, ...]] = ()  # UNVERIFIED — load official gazette holidays

# ---------------------------------------------------------------------------
# Payment claim -> payment response -> payment
# ---------------------------------------------------------------------------
# Period for the respondent to serve a payment response after a payment claim.
PAYMENT_RESPONSE_PERIOD_CALENDAR_DAYS: Final[int] = 30  # CISOP s.? — UNVERIFIED (calendar vs working days UNVERIFIED)

# Period within which an admitted / claimed amount must be paid after the claim.
PAYMENT_DUE_PERIOD_CALENDAR_DAYS: Final[int] = 60  # CISOP s.? — UNVERIFIED

# Minimum interval between successive payment claims (anti-duplication guard).
MIN_DAYS_BETWEEN_CLAIMS: Final[int] = 30  # CISOP s.? — UNVERIFIED

# ---------------------------------------------------------------------------
# Reference dates (when a claim may validly be served)
# ---------------------------------------------------------------------------
# If the contract is silent, reference dates default to monthly intervals.
DEFAULT_REFERENCE_DATE_INTERVAL_DAYS: Final[int] = 30  # CISOP s.? — UNVERIFIED
# Long-stop for serving a claim after the work is completed / contract terminated.
CLAIM_LONGSTOP_AFTER_COMPLETION_DAYS: Final[int] = 540  # ~18 months — CISOP s.? — UNVERIFIED

# ---------------------------------------------------------------------------
# Adjudication windows (WORKING days unless the name says CALENDAR)
# ---------------------------------------------------------------------------
ADJUDICATION_NOTICE_PERIOD_CALENDAR_DAYS: Final[int] = 28  # to commence adjudication — CISOP s.? — UNVERIFIED
ADJUDICATION_APPOINTMENT_WORKING_DAYS: Final[int] = 5  # to appoint the adjudicator — CISOP s.? — UNVERIFIED
ADJUDICATION_RESPONSE_WORKING_DAYS: Final[int] = 20  # respondent's adjudication response — CISOP s.? — UNVERIFIED
ADJUDICATION_DETERMINATION_WORKING_DAYS: Final[int] = 55  # adjudicator's determination — CISOP s.? — UNVERIFIED
ADJUDICATION_DETERMINATION_EXTENSION_WORKING_DAYS: Final[int] = 10  # extra, by agreement — CISOP s.? — UNVERIFIED

# ---------------------------------------------------------------------------
# Monetary thresholds for the Ordinance to apply
# ---------------------------------------------------------------------------
# Main contract for CONSTRUCTION WORK: the Ordinance applies above this value.
MAIN_CONTRACT_CONSTRUCTION_THRESHOLD_HKD: Final[Decimal] = Decimal("5000000")  # CISOP s.? — UNVERIFIED
# Main contract for SUPPLY of goods / services / M&E: applies above this value.
MAIN_CONTRACT_SUPPLY_THRESHOLD_HKD: Final[Decimal] = Decimal("500000")  # CISOP s.? — UNVERIFIED
# Private-sector threshold — mirrors the construction figure for now.
PRIVATE_SECTOR_THRESHOLD_HKD: Final[Decimal] = MAIN_CONTRACT_CONSTRUCTION_THRESHOLD_HKD  # CISOP s.? — UNVERIFIED
# Subcontracts under a qualifying main contract are believed to be covered
# regardless of their own value.
SUBCONTRACT_HAS_OWN_THRESHOLD: Final[bool] = False  # CISOP s.? — UNVERIFIED

# Convenience lookup keyed by ``schemas.models.ContractType`` values.
THRESHOLD_BY_CONTRACT_TYPE: Final[dict[str, Decimal]] = {
    "main_construction": MAIN_CONTRACT_CONSTRUCTION_THRESHOLD_HKD,  # UNVERIFIED
    "supply_goods_and_services": MAIN_CONTRACT_SUPPLY_THRESHOLD_HKD,  # UNVERIFIED
    "subcontract_construction": Decimal("0"),  # covered regardless of value — UNVERIFIED
    "consultancy": MAIN_CONTRACT_SUPPLY_THRESHOLD_HKD,  # UNVERIFIED
}

# ---------------------------------------------------------------------------
# Mandatory payment-claim particulars (CISOP s.13 — UNVERIFIED section number)
# ---------------------------------------------------------------------------
# Each entry is ``(key, human-readable description)``. ``key`` is aligned with
# fields on ``schemas.models.ExtractedFacts`` / ``ClaimDraft`` so Stage 02 can
# check presence deterministically.
MANDATORY_CLAIM_PARTICULARS: Final[tuple[tuple[str, str], ...]] = (
    ("claimant_identity", "Identity of the claimant serving the claim"),  # s.13 — UNVERIFIED
    ("respondent_identity", "Identity of the respondent who must pay/respond"),  # s.13 — UNVERIFIED
    ("contract_identification", "Identification of the construction contract"),  # s.13 — UNVERIFIED
    ("claimed_amount", "The claimed amount"),  # s.13 — UNVERIFIED
    ("reference_date", "The reference date the claim relates to"),  # s.13 — UNVERIFIED
    ("work_description", "Description of the work / goods / services claimed"),  # s.13 — UNVERIFIED
    ("basis_of_calculation", "How the claimed amount is calculated"),  # s.13 — UNVERIFIED
    ("statutory_statement", "Statement that the claim is made under the Ordinance"),  # s.13 — UNVERIFIED
)

# ---------------------------------------------------------------------------
# Service of notices / claims (method affects how deadlines are computed)
# ---------------------------------------------------------------------------
PERMITTED_SERVICE_METHODS: Final[tuple[str, ...]] = (
    "personal_delivery",  # UNVERIFIED
    "post_to_last_known_address",  # UNVERIFIED — may add deemed-receipt days
    "email_if_agreed",  # UNVERIFIED — only where the contract permits
    "contractual_method",  # UNVERIFIED — whatever method the contract specifies
)
# Deemed-receipt days to add when service is by post (affects deadline maths).
DEEMED_SERVICE_DAYS_BY_POST: Final[int] = 2  # CISOP s.? — UNVERIFIED


__all__ = [
    "CONFIG_VERSION",
    "STATUTORY_SOURCE",
    "STATUTORY_WARNING",
    "WEEKEND_DAYS",
    "PUBLIC_HOLIDAYS",
    "PAYMENT_RESPONSE_PERIOD_CALENDAR_DAYS",
    "PAYMENT_DUE_PERIOD_CALENDAR_DAYS",
    "MIN_DAYS_BETWEEN_CLAIMS",
    "DEFAULT_REFERENCE_DATE_INTERVAL_DAYS",
    "CLAIM_LONGSTOP_AFTER_COMPLETION_DAYS",
    "ADJUDICATION_NOTICE_PERIOD_CALENDAR_DAYS",
    "ADJUDICATION_APPOINTMENT_WORKING_DAYS",
    "ADJUDICATION_RESPONSE_WORKING_DAYS",
    "ADJUDICATION_DETERMINATION_WORKING_DAYS",
    "ADJUDICATION_DETERMINATION_EXTENSION_WORKING_DAYS",
    "MAIN_CONTRACT_CONSTRUCTION_THRESHOLD_HKD",
    "MAIN_CONTRACT_SUPPLY_THRESHOLD_HKD",
    "PRIVATE_SECTOR_THRESHOLD_HKD",
    "SUBCONTRACT_HAS_OWN_THRESHOLD",
    "THRESHOLD_BY_CONTRACT_TYPE",
    "MANDATORY_CLAIM_PARTICULARS",
    "PERMITTED_SERVICE_METHODS",
    "DEEMED_SERVICE_DAYS_BY_POST",
]
