# Stage 03 — Draft (Layer 2: Claude, grounded in Layer 3)

## Inputs

- `ExtractedFacts`, `ValidityReport`, `DeadlineSet` (`schemas.models`).
- Layer 3 template (read-only): `references/cic_templates/payment_claim_template.md`.

## Process

Claude drafts the payment claim, grounded in the CIC template and constrained by
the validated facts. It must not contradict the Rules Engine: a fatal check in
the `ValidityReport` blocks drafting, and warnings are surfaced in the prose
rather than silently resolved. The stage produces both machine-checkable
structured fields and a human-presentable `rendered_markdown` document.

## Outputs

- `ClaimDraft` (`schemas.models`) — structured fields plus `rendered_markdown`,
  passed to Stage 04.
