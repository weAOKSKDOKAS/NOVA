# Stage 02 — Validate (Layer 1: Rules Engine)

## Inputs

- `ExtractedFacts` (`schemas.models`) — the output of Stage 01.
- `rules_engine.cisop_config` — all statutory constants.
- Layer 3 reference (read-only): `references/cisop_ordinance/overview.md`.

## Process

The deterministic Rules Engine (pure Python, no ML) runs every statutory check
against the facts — mandatory particulars (CISOP s.13), threshold applicability
for the contract type, and reference-date sanity — grading each as fatal,
warning, or info. It then computes every live deadline (payment response,
payment due, adjudication windows) in business days from the reference date.
**This is where legal correctness lives.**

## Outputs

- `ValidityReport` (a list of `Check`) and `DeadlineSet` (a list of `Deadline`),
  both from `schemas.models`. A fatal check here blocks Stage 03.
