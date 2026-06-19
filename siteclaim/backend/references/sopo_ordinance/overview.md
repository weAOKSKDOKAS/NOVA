# SOPO (Cap. 652) — Plain-language overview (Layer 3 reference)

> ⚠️ **Reference material, not legal advice.** Plain-language summary written to
> ground drafting and validation. It is **not a substitute for the enacted text**.
> Two provenance tiers are used below:
> - **SOURCED (law-firm summary)** — grounded in a secondary law-firm summary;
>   cross-check against the e-legislation Cap.652 text before relying on it.
> - **`# UNVERIFIED — confirm with Cap.652 text/QS`** — anything beyond that
>   summary; not yet confirmed.
>
> Authoritative numbers live in `backend/rules_engine/sopo_config.py` (same tiers).

## What SOPO is

The **Construction Industry Security of Payment Ordinance (Cap. 652)** ("SOPO")
is Hong Kong legislation intended to improve cash flow in the construction supply
chain. Its core idea: a party that has carried out construction work (or supplied
related goods/services) has a statutory right to claim payment, to receive a
timely response, and to refer a payment dispute to **adjudication** — a fast,
interim-binding process — rather than waiting for arbitration or litigation.
SOPO provides three linked mechanisms: **payment → adjudication → enforcement.**

## Scope — when it applies

SOURCED (law-firm summary) — cross-check against Cap.652 text:

- Applies to both **public- and private-sector** construction contracts.
- Applies to qualifying contracts **entered into on or after 28 August 2025**.
- Monetary thresholds (at the relevant contract level):
  - **main contract for construction work: above HK$5,000,000**;
  - **related goods/services: above HK$500,000**.

> Whether/how subcontracts beneath a qualifying main contract are covered, and how
> the thresholds interact across the contractual chain, is **# UNVERIFIED — confirm
> with Cap.652 text/QS**.

## Exclusions

SOURCED (law-firm summary) — cross-check against Cap.652 text:

- Contracts relating to **existing private residential** premises.
- **Minor non-residential** works that **do not require Building Authority
  approval**.

> Any other carve-outs or definitional limits are **# UNVERIFIED — confirm with
> Cap.652 text/QS**.

## Pay-when-paid / pay-if-paid prohibited

SOURCED (law-firm summary) — cross-check against Cap.652 text: **conditional
("pay-when-paid" / "pay-if-paid") payment provisions are prohibited** — a payer
cannot make payment contingent on first being paid by someone else.

## The three mechanisms and their timeline

All periods below are **SOURCED (law-firm summary) — cross-check against Cap.652
text**. **CALENDAR vs WORKING days is legally load-bearing** and is encoded in
`sopo_config.py`; the constant names carry the distinction.

### 1. Payment

- A claimant serves a **payment claim**; the respondent serves a **payment
  response**. Response period: **30 days (s.20)** — a statutory maximum; the
  contract may specify a shorter period. *(calendar days)*
- Payment deadline: **up to 60 days**; parties may agree earlier. *(calendar days)*

### 2. Adjudication

- A payment dispute may be referred to adjudication: initiate within **28 days
  (s.24)** of the dispute arising. *(calendar days)*
- If **no — or more than one — Adjudicator Nominating Body (ANB)** is specified,
  serve on the ANB within **8 working days (s.25(3))**.
- **Adjudicator appointed** within **7 working days**.
- **Determination** within **55 days after appointment (s.42(5))**.
  *(calendar vs working days to confirm against Cap.652 — `# UNVERIFIED` on the
  day-type only)*
- The adjudicated amount must be paid within **30 days (s.43 / s.42(7))** where
  the adjudicator has not specified a time. *(calendar days)*
- The determination is **binding on an interim basis** pending final resolution.

### 3. Enforcement

- An adjudicated amount may be enforced through the courts. Court routing turns
  on value: the **HK$3,000,000** threshold separates the **Court of First
  Instance (above)** from the **District Court (below)** under the Rules
  (**Cap.652A**). SOURCED (law-firm summary) — cross-check against Cap.652A text.

## What makes a payment claim valid — s.18 content requirements

> **TODO — do not encode yet.** The exact **mandatory particulars required by
> s.18** must be read off the Cap.652 text before they are listed here or encoded
> in `sopo_config.MANDATORY_CLAIM_PARTICULARS` (currently intentionally empty).
> Until then, Stage 02 must not validate a claim against guessed fields.
> **# UNVERIFIED — confirm with Cap.652 text/QS.**

## Reference dates and service of notices

> Beyond the scope of the sourced summary — **# UNVERIFIED — confirm with Cap.652
> text/QS**: how **reference dates** are fixed (and any minimum interval between
> claims), and the **permitted methods of serving** claims/notices (and any
> deemed-receipt rules). Keep proof of service regardless — it anchors every
> downstream deadline.

---

### Maintenance

When a value here is verified against the enacted Ordinance, update its tier here
**and** the matching constant in `backend/rules_engine/sopo_config.py` so Layer 1
and Layer 3 stay in sync. Resolve the s.18 TODO in both places together.
