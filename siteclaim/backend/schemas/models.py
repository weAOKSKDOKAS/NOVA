"""SiteClaim typed data contracts — the ICM plain-data handoff between stages.

Every pipeline stage consumes and produces the Pydantic v2 models defined in
this module. There is no shared mutable state and no framework "memory": a stage
reads one or more of these objects, does its work, and writes the next object.
Because every model is JSON-serialisable (``model_dump_json`` /
``model_validate_json``), a stage boundary can be an in-process function call, a
file on disk in ``backend/fixtures/``, or an HTTP payload — the contract is
identical either way.

Layering reminder (see ``CLAUDE.md``):

* **Layer 2 (Claude)** populates :class:`ExtractedFacts` and :class:`ClaimDraft`.
* **Layer 1 (Rules Engine)** populates :class:`ValidityReport`,
  :class:`DeadlineSet` and :class:`AuditReport`.

The LLM never decides the law; it fills and drafts. The Rules Engine checks.

Provenance is first-class: most extracted values are wrapped in
:class:`FactField`, which carries a ``confidence`` score and the ``source_span``
the value was read from, so downstream stages — and the human reviewer in
Stage 05 — can see *why* a value is what it is.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp used for model creation defaults."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class ContractType(str, Enum):
    """Coarse contract classification that drives SOPO applicability.

    The distinction matters because the monetary threshold for the Ordinance to
    apply differs between construction work and the mere supply of goods or
    services (see ``rules_engine.sopo_config``). UNVERIFIED — confirm the exact
    statutory categories against the enacted text.
    """

    MAIN_CONSTRUCTION = "main_construction"
    SUBCONTRACT_CONSTRUCTION = "subcontract_construction"
    SUPPLY_GOODS_AND_SERVICES = "supply_goods_and_services"
    CONSULTANCY = "consultancy"
    OTHER = "other"


class Sector(str, Enum):
    """Whether the head contract is public- or private-sector funded."""

    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Shared severity scale for validity checks and audit findings."""

    FATAL = "fatal"  # blocks a compliant claim; must be fixed before service
    WARNING = "warning"  # likely problem; the human reviewer should confirm
    INFO = "info"  # advisory / informational only


# ---------------------------------------------------------------------------
# Provenance wrapper
# ---------------------------------------------------------------------------
class FactField(BaseModel, Generic[T]):
    """A single extracted value plus where it came from and how sure we are.

    Wrapping scalar facts in this envelope keeps provenance attached to the data
    as it flows between stages. ``confidence`` is the extractor's self-reported
    certainty in ``[0.0, 1.0]``; ``source_span`` is a verbatim snippet — or a
    locator such as ``"invoice_3.pdf:p2"`` — pointing back into the source
    material.
    """

    value: Optional[T] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_span: Optional[str] = None


# ---------------------------------------------------------------------------
# Stage 01 input — raw source material
# ---------------------------------------------------------------------------
class UploadedFile(BaseModel):
    """A single raw upload (invoice, site photo, PDF, email export, contract)."""

    filename: str
    content_type: str
    size_bytes: Optional[int] = None
    storage_ref: Optional[str] = None  # path / URL / object key where bytes live
    sha256: Optional[str] = None


class ShipmentDocs(BaseModel):
    """The bundle of raw documents 'shipped in' for a single claim attempt."""

    files: list[UploadedFile] = Field(default_factory=list)


class SourceMaterial(BaseModel):
    """Stage 01 input: the raw uploads plus the user's free-text description.

    This is intentionally unstructured — it is whatever mess the subcontractor
    has on hand. Stage 01 (Layer 2 / Claude) is responsible for turning it into
    typed :class:`ExtractedFacts`; nothing here is assumed clean or complete.
    """

    docs: ShipmentDocs = Field(default_factory=ShipmentDocs)
    description: str = ""  # free-text narrative supplied by the user
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Stage 01 output — extracted facts (with provenance)
# ---------------------------------------------------------------------------
class Party(BaseModel):
    """A contracting party (the claimant or the respondent)."""

    name: str
    role: Optional[str] = None  # e.g. 'main contractor', 'employer', 'subcontractor'
    address: Optional[str] = None
    contact: Optional[str] = None


class Parties(BaseModel):
    """The two sides of the payment claim, each carrying its own provenance."""

    claimant: FactField[Party] = Field(default_factory=FactField)  # who is claiming
    respondent: FactField[Party] = Field(default_factory=FactField)  # who must pay/respond


class WorkPeriod(BaseModel):
    """The period of construction work the claim covers."""

    start: Optional[date] = None
    end: Optional[date] = None


class LineItem(BaseModel):
    """One line of claimed work or value, with its own extraction provenance."""

    description: str
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    rate: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_span: Optional[str] = None


class CertifiedAmount(BaseModel):
    """An amount previously certified or paid, to be netted off the claim."""

    description: Optional[str] = None
    amount: Optional[Decimal] = None
    certificate_ref: Optional[str] = None
    certified_on: Optional[date] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_span: Optional[str] = None


class ExtractedFacts(BaseModel):
    """Stage 01 output: structured facts read out of the source material.

    Produced by Layer 2 (Claude) and consumed by Layer 1 (the Rules Engine) in
    Stage 02. Every value carries provenance so the validator — and the human
    reviewer — can audit *why* a figure is what it is. Nothing here is assumed
    legally correct; establishing that is Stage 02's job.
    """

    contract_sum: FactField[Decimal] = Field(default_factory=FactField)
    contract_type: FactField[ContractType] = Field(default_factory=FactField)
    sector: FactField[Sector] = Field(default_factory=FactField)
    parties: Parties = Field(default_factory=Parties)
    reference_date: FactField[date] = Field(default_factory=FactField)
    claimed_amount: FactField[Decimal] = Field(default_factory=FactField)
    work_period: FactField[WorkPeriod] = Field(default_factory=FactField)
    line_items: list[LineItem] = Field(default_factory=list)
    certified_amounts: list[CertifiedAmount] = Field(default_factory=list)
    supporting_doc_refs: list[str] = Field(default_factory=list)
    extraction_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Stage 02 output — validity report + deadline set (Layer 1, deterministic)
# ---------------------------------------------------------------------------
class Check(BaseModel):
    """A single deterministic rule outcome from the Layer 1 Rules Engine."""

    name: str
    passed: bool
    severity: Severity
    sopo_reference: str  # e.g. 'SOPO s.20' — see rules_engine.sopo_config for tier (SOURCED/UNVERIFIED)
    explanation: str


class ValidityReport(BaseModel):
    """Stage 02 output: the result of running every statutory check.

    This is where legal correctness lives. The LLM does not produce this — the
    Rules Engine does, deterministically, from :class:`ExtractedFacts` and the
    constants in ``rules_engine.sopo_config``.
    """

    checks: list[Check] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)

    @property
    def has_fatal(self) -> bool:
        """True if any check failed at FATAL severity (claim is non-compliant)."""
        return any(c.severity is Severity.FATAL and not c.passed for c in self.checks)

    @property
    def is_valid(self) -> bool:
        """True if no fatal check failed (warnings/info may still be present)."""
        return not self.has_fatal


class Deadline(BaseModel):
    """A statutory deadline computed by the Rules Engine."""

    name: str
    due_date: date
    business_days_remaining: int
    sopo_reference: str  # e.g. 'SOPO s.42(5)' — see rules_engine.sopo_config for tier (SOURCED/UNVERIFIED)


class DeadlineSet(BaseModel):
    """Stage 02 companion output: every live SOPO deadline for this claim."""

    deadlines: list[Deadline] = Field(default_factory=list)
    computed_from: Optional[date] = None  # the reference date used for the maths
    computed_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Stage 03 output — the drafted claim (Layer 2, grounded in Layer 3)
# ---------------------------------------------------------------------------
class ClaimDraft(BaseModel):
    """Stage 03 output: the drafted payment claim, structured + rendered.

    Layer 2 (Claude) writes the prose, grounded in the CIC template (Layer 3)
    and constrained by the validated facts. ``rendered_markdown`` is the
    human-presentable document; the structured fields make the Stage 04 audit
    machine-checkable against :class:`ExtractedFacts`.
    """

    claimant_name: Optional[str] = None
    respondent_name: Optional[str] = None
    contract_reference: Optional[str] = None
    reference_date: Optional[date] = None
    claimed_amount: Optional[Decimal] = None
    currency: str = "HKD"
    line_items: list[LineItem] = Field(default_factory=list)
    basis_of_calculation: Optional[str] = None
    statutory_statement: Optional[str] = None  # the 'made under SOPO' wording
    supporting_doc_refs: list[str] = Field(default_factory=list)
    rendered_markdown: str = ""
    generated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Stage 04 output — audit of the draft against the facts (Layer 1 + optional 2)
# ---------------------------------------------------------------------------
class Finding(BaseModel):
    """A single issue raised by the Stage 04 audit of the draft."""

    issue: str
    location: str  # where in the draft, e.g. 'line_items[2]' or 'claimed_amount'
    severity: Severity
    suggested_fix: str


class AuditReport(BaseModel):
    """Stage 04 output: cross-check of the draft against facts + statute."""

    findings: list[Finding] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)

    @property
    def passed(self) -> bool:
        """True if the audit found no FATAL-severity issues."""
        return not any(f.severity is Severity.FATAL for f in self.findings)


__all__ = [
    # enums
    "ContractType",
    "Sector",
    "Severity",
    # provenance
    "FactField",
    # stage 01 in
    "UploadedFile",
    "ShipmentDocs",
    "SourceMaterial",
    # stage 01 out
    "Party",
    "Parties",
    "WorkPeriod",
    "LineItem",
    "CertifiedAmount",
    "ExtractedFacts",
    # stage 02 out
    "Check",
    "ValidityReport",
    "Deadline",
    "DeadlineSet",
    # stage 03 out
    "ClaimDraft",
    # stage 04 out
    "Finding",
    "AuditReport",
]
