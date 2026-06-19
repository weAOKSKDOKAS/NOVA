# CISOP — Plain-language overview (Layer 3 reference)

> ⚠️ **UNVERIFIED reference material.** This is a plain-language summary compiled
> from secondary research, written to ground drafting and validation. It is **not
> legal advice** and **not a substitute for the enacted text**. Every specific
> figure, time period, and section reference below is tagged `# UNVERIFIED` and
> must be confirmed with a quantity surveyor or construction lawyer. Authoritative
> numbers live in `backend/rules_engine/cisop_config.py` (also unverified).

## What CISOP is

The **Construction Industry Security of Payment Ordinance** ("CISOP") is Hong
Kong legislation intended to improve cash flow in the construction supply chain.
Its core idea: a party that has done construction work (or supplied related
goods/services) has a statutory right to claim payment, to receive a timely
response, and to refer a payment dispute to **adjudication** — a fast,
interim-binding process — rather than waiting for arbitration or litigation.

## Scope — does it apply?

CISOP is believed to apply to a construction contract where: # UNVERIFIED

- the contract relates to **construction work** carried out in Hong Kong, or to
  the **supply of goods/services** (including plant and M&E) for such work; and
- a monetary **threshold** is met at the head-contract level —
  - construction work main contracts above **HK$5,000,000**; # UNVERIFIED
  - supply-only main contracts above **HK$500,000**; # UNVERIFIED
- once a qualifying main contract exists, **subcontracts beneath it are covered
  regardless of their own value**. # UNVERIFIED

Both **public- and private-sector** contracts may be covered once the threshold
is met. # UNVERIFIED Certain contracts (e.g. with residential occupiers, or
contracts below threshold) may be excluded. # UNVERIFIED

## Key obligations

1. **Right to claim.** A claimant may serve a **payment claim** on or after a
   **reference date**. # UNVERIFIED
2. **Right to a response.** The respondent must serve a **payment response**
   stating the amount it proposes to pay and any reasons for withholding, within
   the statutory window. # UNVERIFIED
3. **Duty to pay.** Admitted amounts must be paid by the statutory/contractual
   due date. # UNVERIFIED
4. **No "pay-when-paid".** Conditional-payment clauses that make payment
   contingent on the payer first being paid by someone else are believed to be
   ineffective. # UNVERIFIED
5. **Right to adjudicate.** A payment dispute may be referred to adjudication;
   the adjudicator's determination is binding on an interim basis. # UNVERIFIED

## The deadline regime (all periods UNVERIFIED)

- **Reference dates** — when a claim may be served; if the contract is silent,
  default to monthly intervals; claims no more often than monthly. # UNVERIFIED
- **Payment response** — typically within **30 days** of the payment claim.
  Calendar vs working days must be confirmed. # UNVERIFIED
- **Payment due** — admitted/claimed amount payable within ~**60 days**. # UNVERIFIED
- **Adjudication** — notice within ~**28 days** of the dispute; adjudicator
  appointed within ~**5 working days**; respondent's response within ~**20
  working days**; **determination within 55 working days** of appointment,
  extendable by agreement. # UNVERIFIED

## What makes a payment claim valid

A compliant claim is believed to need the following **mandatory particulars**
(CISOP s.13 — section number UNVERIFIED): # UNVERIFIED

- identity of the **claimant** and the **respondent**;
- identification of the **construction contract**;
- the **claimed amount**;
- the **reference date** the claim relates to;
- a **description of the work / goods / services** claimed;
- the **basis of calculation** of the claimed amount;
- a **statement that the claim is made under the Ordinance**.

Missing any mandatory particular is treated as a **fatal** defect by the Rules
Engine (Stage 02).

## How notices must be served

Service method matters because it affects when periods start running. Believed
to be permitted: # UNVERIFIED

- **personal delivery**; # UNVERIFIED
- **post** to the last known address (may add deemed-receipt days); # UNVERIFIED
- **email**, where the contract permits it; # UNVERIFIED
- any **method specified in the contract**. # UNVERIFIED

Keep proof of service — it is the anchor for every downstream deadline.

---

### Maintenance

When a value here is verified against the enacted Ordinance, remove its
`# UNVERIFIED` tag here **and** update the matching constant in
`backend/rules_engine/cisop_config.py` so Layer 1 and Layer 3 stay in sync.
