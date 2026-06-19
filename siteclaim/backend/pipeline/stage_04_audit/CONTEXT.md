# Stage 04 — Audit (Layer 1: Rules Engine, optional Layer 2 self-review)

## Inputs

- `ClaimDraft`, `ExtractedFacts`, `ValidityReport` (`schemas.models`).

## Process

The draft is cross-checked against the source facts and statutory requirements:
every figure in the draft must trace back to an extracted fact, all mandatory
particulars must be present, and no number may diverge from `ExtractedFacts`. The
Rules Engine performs the deterministic cross-foot; Claude may add a self-review
pass for tone and completeness. Each discrepancy becomes a `Finding` graded by
severity.

## Outputs

- `AuditReport` (a list of `Finding`) from `schemas.models`. A fatal finding must
  be resolved before Stage 05 can approve.
