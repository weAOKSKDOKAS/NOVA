# SiteClaim frontend

A 5-step review-gate wizard (React + TypeScript + Vite + Tailwind) over the
SiteClaim pipeline: **Input → Facts → Validity → Draft → Audit**. A person can
edit at every gate; each step calls its own API endpoint with whatever they left,
so editing a fact flows through verify → draft → audit (the ICM review-gate
pattern). No backend storage — the running claim lives in React state.

## Run it

Two terminals, from `siteclaim/`:

```bash
# 1) backend (offline demo mode) — from siteclaim/backend
DEMO_MODE=true uvicorn api:app --reload --port 8000

# 2) frontend — from siteclaim/frontend
npm install   # first time only
npm run dev
```

Then open http://localhost:5173 and pick a demo case (clean / messy / gotcha).

- **clean** → walks through to a **Fileable** verdict.
- **messy** → low-confidence facts, placeholders in the draft, **Fileable with fixes**.
- **gotcha** → served on the wrong legal entity; the audit returns **Not fileable**
  citing `notice.correct_party`. Fix the served-on party at the Facts gate and the
  verdict flips to Fileable.

The API base defaults to `http://localhost:8000`; override with `VITE_API_BASE`.

> SiteClaim is decision support, not legal advice. Statutory values are
> unverified — a quantity surveyor or construction lawyer must confirm before filing.
