# Stage 05 — Review (Layer 4: human-in-the-loop)

## Inputs

- `ClaimDraft`, `ValidityReport`, `DeadlineSet`, `AuditReport` (`schemas.models`).

## Process

The human-in-the-loop approval gate. The subcontractor (or their quantity
surveyor) sees the draft alongside the validity report, the computed deadlines,
and the audit findings, and then approves, edits, or rejects it. **Nothing is
served on a respondent without explicit human sign-off** — the copilot never
auto-sends, and the reviewer's decision is recorded for the audit trail.

## Outputs

- An approved (or rejected) `ClaimDraft` (`schemas.models`). On approval, the
  final document is released for the subcontractor to serve; the human decision
  is recorded.
