# Stage 01 — Extract (Layer 2: Claude)

## Inputs

- `SourceMaterial` (`schemas.models`) — the raw uploads (`ShipmentDocs`) plus the
  user's free-text description.
- Layer 3 reference (read-only): `references/sopo_ordinance/overview.md`, to know
  which facts a valid claim needs.

## Process

Claude reads the messy source material and extracts structured facts, filling
every field of `ExtractedFacts`. Each value is wrapped in a `FactField` carrying
a `confidence` score and a `source_span` pointer, so later stages can audit
provenance. This stage only **reads and records** what the documents say — it
does not judge legal validity, reconcile figures, or compute deadlines.

## Outputs

- `ExtractedFacts` (`schemas.models`) — written to `backend/fixtures/` (or passed
  in-memory) as the sole input to Stage 02.
