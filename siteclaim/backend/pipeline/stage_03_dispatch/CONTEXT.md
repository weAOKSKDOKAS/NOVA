# Stage 03 — Dispatch (Layer 4 gate, Layer 2 email, mock outbox)

## Inputs
- `ShortlistSet` and `approvals` (`dict[trade, list[firm_id]]`) — the human gate.

## Process
For each approved firm, assemble a `DispatchBundle`: `bundle_doc_refs` lists only
that firm's trade documents, and Layer 2 composes a professional, trade-specific
`email_subject`/`email_body`. Status moves drafted -> approved. A mock outbox
(`db/outbox.py`) records "sent" bundles with a timestamp; **nothing touches the
network**. DEMO_MODE reads a baked `DispatchSet` fixture for the email bodies.

## Outputs
- `DispatchSet` — the per-firm bundles, status `sent_mock` once dispatched.
