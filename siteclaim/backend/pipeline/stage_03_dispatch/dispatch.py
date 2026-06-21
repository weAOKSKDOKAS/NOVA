"""Stage 03 — dispatch: ShortlistSet + approvals -> DispatchSet.

Layer 4 gate: only human-approved firms get a bundle. Each `DispatchBundle`
contains only that trade's documents (an electrical firm receives the electrical
scope, not the whole tender); Layer 2 composes the email. Sending is a mock
outbox — nothing touches the network. Phase 5.
"""
