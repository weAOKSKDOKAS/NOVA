# CONTEXT.md — Pipeline routing (Layer 1)

SiteClaim runs as five numbered stages under `backend/pipeline/`. Each stage
reads and writes the typed models in `backend/schemas/models.py` —
**plain-data handoff, no shared state**. Shared **Layer 3 references** live in
`backend/references/` (SOPO overview, CIC templates) and are read-only.
**Layer 1 statutory constants** live in `backend/rules_engine/sopo_config.py`.

| # | Stage | Consumes | Produces | Layer |
| --- | --- | --- | --- | --- |
| 01 | `extract` | `SourceMaterial` | `ExtractedFacts` | 2 (Claude) |
| 02 | `validate` | `ExtractedFacts` | `ValidityReport` + `DeadlineSet` | 1 (Rules) |
| 03 | `draft` | `ExtractedFacts` + `ValidityReport` + `DeadlineSet` | `ClaimDraft` | 2 (Claude) + 3 (RAG) |
| 04 | `audit` | `ClaimDraft` + `ExtractedFacts` + `ValidityReport` | `AuditReport` | 1 (Rules) + 2 |
| 05 | `review` | `ClaimDraft` + `ValidityReport` + `DeadlineSet` + `AuditReport` | approved `ClaimDraft` | 4 (Human) |

**Flow is strictly forward:** a stage may only read the outputs of earlier
stages. A fatal `Check` in Stage 02 blocks Stage 03. No claim leaves Stage 05
without explicit human sign-off.

See `CLAUDE.md` for the full four-layer architecture and the
"LLM drafts / engine checks" principle.
