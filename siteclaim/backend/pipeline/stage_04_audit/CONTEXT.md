# Stage 04 — Audit (Layer 1: Rules Engine, optional Layer 2 self-review)

## Inputs

- `ClaimDraft`, `ExtractedFacts`, `ValidityReport` (`schemas.models`).

- `today` (the date the deadline clock is re-run against).

## Process

The draft is cross-checked against the source facts and statutory requirements:
every figure in the draft must trace back to an extracted fact (and the claimed
total must cross-foot against the line items), all mandatory particulars must be
present **in the rendered document** (not merely the structured fields), the
deadline clock is re-run against `today`, and `notice_validity` is re-run to
surface any way the notice could be void. This is deterministic (Layer 1); a thin
Layer-2 LLM pass (skipped offline in DEMO_MODE) adds prose-level consistency
checks only. Each discrepancy becomes a `Finding` graded by severity, sorted
fatal → warning → info.

## Outputs

- `AuditReport` from `schemas.models`: a list of `Finding` plus a single
  top-level `verdict` (`FILEABLE` / `FILEABLE_WITH_FIXES` / `NOT_FILEABLE`),
  derived deterministically from the worst-severity finding. A `NOT_FILEABLE`
  verdict (any fatal finding) must be resolved before Stage 05 can approve.
