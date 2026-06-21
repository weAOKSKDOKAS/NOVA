# SiteClaim eval scorecard — engine vs. chatbot

Engine scores are computed by `eval/run_engine.py` against the hand-computed ground
truth in `eval/cases.py` (transcribed from `SiteClaim_Eval_Set.md`). The **Chatbot**
column is intentionally empty — run `eval/chatbot_prompts.py` outputs through ChatGPT
(3× for C/D per the doc) and fill it in.

Scoring: verdict (1) + defect (1) + deadline (1, where applicable) per case.
`NM` = the current engine does not model that dimension (not a fail — a coverage gap).

## Score by category

| Category | What it tests | Engine (pass/scoreable) | NM dims | Chatbot |
|---|---|---|---|---|
| A (4) | s.18 basics, formatting | **9/9** | 0 | _tbd_ |
| B (4) | service / party | **8/8** | 0 | _tbd_ |
| C (6) | date & working-day math, deeming | **7/7** | 10 | _tbd_ |
| D (5) | eligibility edges | **8/8** | 2 | _tbd_ |
| **Total** | | **32/32** | 12 | _tbd_ |

## Per-case detail

| Case | GT verdict | Engine verdict | V | D | L | GT date | Engine date |
|---|---|---|---|---|---|---|---|
| A1 | FILEABLE | FILEABLE | ✓ | ✓ | ✓ | 2026-04-01 | 2026-04-01 |
| A2 | NOT_FILEABLE | NOT_FILEABLE | ✓ | ✓ | · | — | — |
| A3 | NOT_FILEABLE | NOT_FILEABLE | ✓ | ✓ | · | — | — |
| A4 | NOT_FILEABLE | NOT_FILEABLE | ✓ | ✓ | · | — | — |
| B1 | FILEABLE | FILEABLE | ✓ | ✓ | · | — | — |
| B2 | NOT_FILEABLE | NOT_FILEABLE | ✓ | ✓ | · | — | — |
| B3 | NOT_FILEABLE | NOT_FILEABLE | ✓ | ✓ | · | — | — |
| B4 | FILEABLE_WITH_FIXES | FILEABLE_WITH_FIXES | ✓ | ✓ | · | — | — |
| C1 | ON_TIME | (FILEABLE) | NM | NM | ✓ | 2026-04-17 | 2026-04-17 |
| C2 | MISSED | (FILEABLE) | NM | NM | ✓ | 2026-04-17 | 2026-04-17 |
| C3 | ON_TIME | (FILEABLE) | NM | NM | NM | 2026-04-16 | 2026-04-16 |
| C4 | ON_TIME | (FILEABLE) | NM | NM | NM | 2026-04-16 | 2026-04-16 |
| C5 | FILEABLE | FILEABLE | ✓ | ✓ | ✓ | 2026-03-30 | 2026-03-30 |
| C6 | FILEABLE | FILEABLE | ✓ | ✓ | · | — | 2026-03-30 |
| D1 | OUT_OF_SCOPE | OUT_OF_SCOPE | ✓ | ✓ | · | — | — |
| D2 | FILEABLE | FILEABLE | ✓ | ✓ | · | — | — |
| D3 | OUT_OF_SCOPE | OUT_OF_SCOPE | ✓ | ✓ | · | — | — |
| D4 | FILEABLE | FILEABLE | ✓ | ✓ | · | — | — |
| D5 | NOT_ADJUDICABLE | (FILEABLE) | NM | NM | · | — | — |

## NOT MODELLED — the coverage gaps this eval surfaced

- **C1** [verdict, defect] — Engine computes the 28-day adjudication window but has no adjudication-notice-served field and does not judge on-time/late.
- **C2** [verdict, defect] — Same as C1 — the engine computes the window but does not compare the notice-served date (20 Apr) against it.
- **C3** [verdict, defect, deadline] — compute_deadlines emits no ANB-service deadline and there is no ANB-timing check. (business_days.add_working_days DOES compute 16 Apr — the gap is wiring, not arithmetic.)
- **C4** [verdict, defect, deadline] — Same ANB gap as C3 (control: 13 Apr is in-window; nothing should flag it late).
- **D5** [verdict, defect] — Engine does not model dispute-type adjudicability or the public-only phase-1 EOT restriction (no 'dispute type' fact).

## Discrepancies (engine ≠ ground truth on a modelled dimension)

- none
