# Risk Scoring Rules — deterministic firm risk flags (v1)

Applied by `rules_engine/risk_scoring.py` (pure Python) to a `FirmProfile` from the
database. Each rule that fires produces a `RiskFlag` with the severity below and the
cited `Evidence`. **A `fatal` flag demotes or excludes a firm regardless of price**
(enforced by `rules_engine/ranking.py`); the LLM never sets a flag.

## Fatal — do not award regardless of price
| Rule (`rule_ref`) | Condition | Why |
| --- | --- | --- |
| `risk.winding_up` | An **active winding-up petition** (Companies Registry) | Counterparty may not survive the project |
| `risk.adjudication_unpaid` | An **unpaid adjudication determination** | Demonstrated non-payment / dispute risk |
| `risk.safety_prosecutions` | **Two or more** safety-prosecution convictions (Labour Dept) | Systemic safety failure |
| `risk.debarment` | **Debarred** from public works | Disqualified counterparty |

## Warning — surface for the human to weigh
| Rule (`rule_ref`) | Condition | Why |
| --- | --- | --- |
| `risk.safety_single` | **One** safety-prosecution conviction | Isolated but material |
| `risk.closeout_delay` | A **delayed-closeout** note in project history | Programme risk |
| `risk.grade_band` | **Registered grade is low** for the package's value band | Capacity / capability mismatch |

## Notes
- Severity ordering is fatal > warning > info (see `rules_engine/_common.SEVERITY_RANK`).
- Every flag must carry at least one `Evidence` with a citable `reference`; a flag
  with no evidence is a bug.
- Rules are versioned; bump the version when a rule or threshold changes.
