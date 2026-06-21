# CONTEXT.md — Pipeline routing

SiteSource runs as five numbered stages under `backend/pipeline/`. Each stage
reads and writes the typed models in `backend/schemas/models.py` —
**plain-data handoff, no shared state**. The **Layer 3 proprietary database**
lives in `backend/db/`; shared **rubrics** (read-only) live in
`backend/references/rubrics/`.

| # | Stage | Consumes | Produces | Layer |
| --- | --- | --- | --- | --- |
| 01 | `ingest` | `TenderPackage` | `ScopePackages` | 2 (Claude) + 1 (taxonomy) |
| 02 | `shortlist` | `ScopePackages` + database | `ShortlistSet` | 1 (cross-reference) |
| 03 | `dispatch` | `ShortlistSet` + approvals | `DispatchSet` | 4 (gate) + 2 (email) |
| 04 | `level` | `BidReplies` + `ScopePackages` | `LevelledBids` | 2 (parse) + 1 (arithmetic) |
| 05 | `recommend` | `LevelledBids` + database | `Recommendation` | 1 (ranking) + 2 (narrate) + 4 (award) |

**Flow is strictly forward:** a stage may only read the outputs of earlier stages.
A **fatal** risk flag in the cross-reference demotes a firm regardless of price; no
award leaves Stage 05 without explicit human sign-off.

See `CLAUDE.md` for the four-layer architecture and the
"LLM reads & explains / engine computes & checks / database grounds" principle.
