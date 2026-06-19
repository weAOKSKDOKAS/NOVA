# SiteClaim

SiteClaim is a **SOPO-compliant payment-claim drafting copilot** for Hong Kong
construction subcontractors. A subcontractor uploads messy evidence (invoices,
site records, emails, the contract); SiteClaim extracts the facts, checks them
against SOPO — the Construction Industry Security of Payment Ordinance (Cap. 652)
— with a deterministic Rules Engine, drafts a compliant payment claim grounded in CIC
templates, audits the draft against the facts, and routes it to a human for
approval before anything is served. It is built as an **ICM workspace** — the
folder structure is the architecture, stages hand off plain typed data
(`backend/schemas/models.py`), and there is no agent framework. The guiding
principle: **the LLM never decides the law; it fills and drafts — the Rules
Engine checks.** See [`CLAUDE.md`](CLAUDE.md) for the architecture and
[`CONTEXT.md`](CONTEXT.md) for pipeline routing.

> ⚠️ Statutory parameters in `backend/rules_engine/sopo_config.py` are tagged
> **SOURCED** (from a secondary law-firm summary, to be cross-checked against the
> e-legislation Cap.652 text) or **`# UNVERIFIED`** (unconfirmed placeholders).
> Validate every value with a quantity surveyor or construction lawyer before
> relying on output. SiteClaim assists drafting; it is not legal advice.

## How to run

Requires **Python 3.11+**. From the `backend/` directory:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt

# run the (scaffold) API
uvicorn api:app --reload        # http://127.0.0.1:8000  — try /health and /legal-notice

# run the Layer 1 tests
pytest
```

## Status

**Phase 0** — scaffolding only: schemas, statutory config, reference stubs, and a
thin API. The five pipeline stages under `backend/pipeline/` are specified
(`CONTEXT.md` per stage) but not yet implemented. The `frontend/` is scaffolded
in Phase 5.
