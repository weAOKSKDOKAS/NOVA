// "Where did this finding come from?" — map an audit Finding back to the
// extracted fact(s) and their source_span, plus the stage that generated it.
// Facts already carry source_span; this just surfaces it.
import type { ExtractedFacts, FF, Finding, Party } from "./types";

export interface TraceEntry {
  label: string;
  value: string;
  sourceSpan: string | null;
  confidence: number | null;
}

export interface Trace {
  stage: string;
  basis: string;
  entries: TraceEntry[];
}

const REVIEW_THRESHOLD = 0.6;

function ff(label: string, field: FF<unknown> | undefined, render: (v: never) => string = String): TraceEntry {
  if (!field) return { label, value: "—", sourceSpan: null, confidence: null };
  return {
    label,
    value: field.value == null ? "—" : render(field.value as never),
    sourceSpan: field.source_span,
    confidence: field.confidence,
  };
}

const partyName = (v: never) => (v as Party).name;
const FROM_EXTRACTION = "The facts below come from Stage 01 · extraction — each shows the source span it was read from.";

function keyFacts(facts: ExtractedFacts): TraceEntry[] {
  return [
    ff("Claimant", facts.parties.claimant, partyName),
    ff("Respondent", facts.parties.respondent, partyName),
    ff("Reference date", facts.reference_date),
    ff("Amount claimed", facts.claimed_amount),
  ];
}

function lowConfidenceFacts(facts: ExtractedFacts): TraceEntry[] {
  const out: TraceEntry[] = [];
  const consider = (label: string, field: FF<unknown>, render?: (v: never) => string) => {
    if (field.value != null && field.confidence < REVIEW_THRESHOLD) out.push(ff(label, field, render));
  };
  consider("Reference date", facts.reference_date);
  consider("Amount claimed", facts.claimed_amount);
  consider("Contract sum", facts.contract_sum);
  consider("Work period", facts.work_period, (v: never) => {
    const wp = v as { start: string | null; end: string | null };
    return `${wp.start ?? "?"} to ${wp.end ?? "?"}`;
  });
  consider("Date served", facts.service.date_served);
  return out;
}

export function traceFor(finding: Finding, facts: ExtractedFacts): Trace {
  const loc = finding.location;

  if (loc === "notice.correct_party") {
    return {
      stage: "Stage 02 · notice validity (rules engine)",
      basis: `Compares the party the claim was served on against the contracting respondent. ${FROM_EXTRACTION}`,
      entries: [ff("Served on", facts.service.served_on), ff("Respondent (contract)", facts.parties.respondent, partyName)],
    };
  }
  if (loc === "notice.timing") {
    return {
      stage: "Stage 02 · notice validity (rules engine)",
      basis: `Checks the service date against the reference date (CIC Q23 deeming). ${FROM_EXTRACTION}`,
      entries: [ff("Date served", facts.service.date_served), ff("Reference date", facts.reference_date)],
    };
  }
  if (loc === "notice.method") {
    return {
      stage: "Stage 02 · notice validity (rules engine)",
      basis: `Checks the method of service. ${FROM_EXTRACTION}`,
      entries: [ff("Method", facts.service.method)],
    };
  }
  if (loc === "notice.proof_of_service") {
    return {
      stage: "Stage 02 · notice validity (rules engine)",
      basis: `Checks whether dated proof of service is kept. ${FROM_EXTRACTION}`,
      entries: [ff("Proof retained", facts.service.proof_retained, (v: never) => (v ? "yes" : "no"))],
    };
  }
  if (loc === "claimed_amount") {
    return {
      stage: "Stage 04 · amount reconciliation",
      basis: `Checks the drafted amount against the extracted claimed amount. ${FROM_EXTRACTION}`,
      entries: [ff("Claimed amount", facts.claimed_amount)],
    };
  }
  if (loc === "line_items") {
    return {
      stage: "Stage 04 · amount reconciliation",
      basis: `Cross-foots the itemised particulars against the claimed total. ${FROM_EXTRACTION}`,
      entries: [
        ...facts.line_items.map((li, i) => ({
          label: `Line ${i + 1}: ${li.description}`,
          value: li.amount ?? "—",
          sourceSpan: li.source_span ?? null,
          confidence: li.confidence,
        })),
        ff("Claimed total", facts.claimed_amount),
      ],
    };
  }
  if (loc.startsWith("deadline:")) {
    return {
      stage: "Stage 02 · deadline clock",
      basis: `The clock runs from the effective (deemed) service date. ${FROM_EXTRACTION}`,
      entries: [ff("Date served", facts.service.date_served), ff("Reference date", facts.reference_date)],
    };
  }
  if (loc === "rendered_markdown") {
    const low = lowConfidenceFacts(facts);
    return {
      stage: "Stage 04 · document check (vs Stage 03 draft)",
      basis: low.length
        ? "These low-confidence facts became placeholders in the rendered document — confirm them before filing."
        : `Checks the rendered document text against the facts. ${FROM_EXTRACTION}`,
      entries: low.length ? low : keyFacts(facts),
    };
  }
  return {
    stage: "Stage 02–04 · rules engine / audit",
    basis: `Derived deterministically from the extracted facts. ${FROM_EXTRACTION}`,
    entries: keyFacts(facts),
  };
}
