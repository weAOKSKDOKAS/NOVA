# SiteClaim

SiteClaim is a **SOPO-compliant payment-claim drafting copilot** for Hong Kong
construction subcontractors. A subcontractor describes the work and uploads messy
evidence (invoices, site records, the contract); SiteClaim extracts the facts,
checks them against SOPO — the Construction Industry Security of Payment Ordinance
(Cap. 652) — with a deterministic Rules Engine, drafts a compliant payment claim
grounded in CIC templates, audits the draft against the facts, and routes it to a
person for approval before anything is served.

The guiding principle: **the LLM never decides the law; it fills and drafts — the
Rules Engine checks.**

> ⚠️ Statutory parameters in `backend/rules_engine/sopo_config.py` are tagged
> **SOURCED** or **`# UNVERIFIED`** (see below). Validate every value with a
> quantity surveyor or construction lawyer before relying on output. SiteClaim
> assists drafting; it is **not legal advice**.

## Run the demo (offline, one command)

Requires **Python 3.11+** and **Node 18+**. From `siteclaim/`:

```bash
make demo        # backend (DEMO_MODE) on :8000 + frontend on :5173, zero network
```

Then open <http://localhost:5173> and load a demo case:

- **clean** → walks through to a **Fileable** verdict.
- **messy** → low-confidence facts, draft placeholders → **Fileable with fixes**.
- **gotcha** → served on the wrong legal entity → **Not fileable**, citing
  `notice.correct_party`. Fix the served-on party at the Facts gate and the
  verdict flips to Fileable.

Or run the two processes by hand:

```bash
cd backend && DEMO_MODE=true uvicorn api:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Other shortcuts: `make test` (backend suite), `make build-frontend`,
`make snapshots` (regenerate the frontend's offline fixtures from the pipeline).

## Live document upload (real invoices)

Outside DEMO_MODE, a subcontractor can upload a **real invoice (PDF or image)** and
SiteClaim extracts the facts from the **document content** via a vision model.
PDFs are rasterised to images (PyMuPDF); the model reads them directly (no OCR).
The provider is swappable — default **DeepSeek V4** (OpenAI-compatible), with the
Claude path as the native-multimodal fallback. Configure with env vars:

| Var | Default | Notes |
| --- | --- | --- |
| `EXTRACTION_PROVIDER` | `deepseek` | `deepseek` or `anthropic` |
| `DEEPSEEK_API_KEY` | — | required for DeepSeek |
| `DEEPSEEK_MODEL` | `deepseek-v4-pro` | or `deepseek-v4-flash` |
| `ANTHROPIC_API_KEY` | — | required if `EXTRACTION_PROVIDER=anthropic` |

`openai` and `pymupdf` are imported **lazily** (only on the live upload path), so
DEMO_MODE stays zero-network and zero-dependency. The API endpoint is
`POST /extract-upload` (multipart); the JSON `POST /extract` remains for
fixtures/typed input.

**Capture a fixture (the offline safety net).** Run a real upload through the live
provider once, lock the result, and replay it byte-for-byte in DEMO_MODE:

```bash
EXTRACTION_PROVIDER=deepseek DEEPSEEK_API_KEY=… \
  python scripts/capture_fixture.py <case_id> invoice.pdf [more…]
```

It writes `backend/fixtures/cases/<case_id>/` (source, extracted, judge verdict,
rasterised images) and re-runs the case offline to confirm the replay.

> DeepSeek's official docs confirm the base URL, OpenAI compatibility, and the V4
> model names but do not publish a vision message format; we send the
> OpenAI-standard `image_url` block. If that ever differs, only one function
> (`build_openai_messages`) changes — the Anthropic path is the working swap target.

## Architecture

SiteClaim is an **ICM (Interpretable Context Methodology) workspace**: the folder
structure *is* the architecture. Stages hand off **plain typed data** (the
Pydantic models in `backend/schemas/models.py`) — there is **no agent framework**
(no LangChain / CrewAI / AutoGen), no shared mutable memory. A stage reads one or
more typed objects, does its work, and writes the next object; a stage boundary
can be an in-process call, a file in `backend/fixtures/`, or an HTTP payload — the
contract is identical.

### Four layers

1. **Rules Engine** (`backend/rules_engine/`) — pure, deterministic Python. **Legal
   correctness lives here.** Every statutory number is a named constant in
   `sopo_config.py`; calendar-vs-working-day arithmetic is in `business_days.py`.
   No ML, no LLM imports (enforced by a purity test).
2. **Claude (LLM)** — reads messy input, extracts facts, drafts prose. Used in
   stages 01 and 03, plus an LLM-as-judge confidence pass in 02 and a thin
   consistency pass in 04. It never decides validity or computes a deadline.
3. **RAG grounding** (`backend/references/`) — a curated SOPO + CIC corpus; only
   the relevant sections are loaded into each prompt (tight grounding).
4. **Human-in-the-loop** — a person reviews and edits at **every gate**; nothing
   is served without sign-off. The API has one endpoint per stage (no monolithic
   `/run`) precisely so a human can edit between every step.

### Five stages (`backend/pipeline/`)

Each stage folder carries a `CONTEXT.md` with `## Inputs / ## Process / ## Outputs`.
Flow is strictly forward.

| # | Stage | Layer | In → Out |
| - | ----- | ----- | -------- |
| 01 | `stage_01_extract` | 2 | `SourceMaterial` → `ExtractedFacts` (per-field `confidence` + `source_span`) |
| 02 | `stage_02_validate` | 2 + 1 | LLM-as-judge confidence review, then the deterministic engine → `ValidityReport` + `DeadlineSet` |
| 03 | `stage_03_draft` | 2 + 3 | facts + reports → `ClaimDraft` (structured + `rendered_markdown`; gaps become flagged placeholders) |
| 04 | `stage_04_audit` | 1 (+ thin 2) | forensic cross-check → `AuditReport` + verdict (`FILEABLE` / `FILEABLE_WITH_FIXES` / `NOT_FILEABLE`) |
| 05 | review | 4 | human approval (the wizard's final gate + a person's sign-off) |

A **fatal** check in Stage 02 blocks a fileable draft; a fatal finding in Stage 04
yields `NOT_FILEABLE`. The frontend mirrors these five stages as a review-gate
wizard; the **Savings** view states the time/cost economics from explicit,
adjustable assumptions; and each audit finding **expands to show the fact(s) and
`source_span` it came from** ("interpretable by construction").

### Workspace layout

```
siteclaim/
├── CLAUDE.md            Layer-0 orientation (read first)
├── CONTEXT.md           pipeline routing in brief
├── Makefile             make demo / test / snapshots
├── backend/
│   ├── schemas/models.py        the typed contracts every stage passes
│   ├── rules_engine/            Layer 1 — sopo_config.py + the checks (deterministic)
│   ├── pipeline/stage_NN_*/     one folder per stage, each with a CONTEXT.md
│   ├── references/              Layer 3 corpus (SOPO overview, CIC templates)
│   ├── fixtures/                demo cases + snapshot builder
│   └── api.py                   FastAPI — one POST per stage + /health + demo loaders
└── frontend/            React + TS + Vite + Tailwind review-gate wizard + savings dashboard
```

## Statutory provenance — SOURCED vs UNVERIFIED

Every value in `sopo_config.py` is tagged in one of two tiers:

- **SOURCED** — taken from a secondary source (a law-firm summary or the CIC FAQ),
  still to be cross-checked against the enacted e-legislation Cap. 652 text. Most
  deadline/threshold constants are here.
- **`# UNVERIFIED`** — an unconfirmed placeholder a QS/lawyer must set.

Remaining **UNVERIFIED** items to confirm before any real use:

- **`PERMITTED_SERVICE_METHODS`** — the methods that validly serve a claim are not
  yet confirmed, so `notice.method` is graded a non-blocking **warning**, never
  fatal. (This is deliberate: the demo's fatal defect is wrong-party service,
  which *is* unambiguous.)
- **Consultancy threshold** — whether/what monetary threshold applies to
  consultancy contracts is unconfirmed (`THRESHOLD_BY_CONTRACT_TYPE`).
- Plus the post/deemed-service interval (`DEEMED_SERVICE_DAYS_BY_POST`), the
  minimum interval between claims (`MIN_DAYS_BETWEEN_CLAIMS`), the default
  reference-date interval, and the determination-extension window.

The savings figures in the dashboard are **assumptions, not measurements** —
each is labelled with its basis and shown as a bear/base/bull range so the
economics are auditable rather than asserted.
