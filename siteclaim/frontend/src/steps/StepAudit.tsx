import { useState } from "react";
import type { AuditReport, ExtractedFacts, Finding } from "../types";
import { traceFor } from "../trace";
import { Button, Card, ConfidenceChip, cx, SeverityTag, VERDICT } from "../ui";
import { StepHeading } from "./StepInput";

export function StepAudit({
  audit,
  facts,
  onBack,
  onReset,
  onShowSavings,
}: {
  audit: AuditReport;
  facts: ExtractedFacts;
  onBack: () => void;
  onReset: () => void;
  onShowSavings: () => void;
}) {
  const [acknowledged, setAcknowledged] = useState(false);
  const verdict = VERDICT[audit.verdict];
  const fatal = audit.findings.filter((f) => f.severity === "fatal");
  const fileable = audit.verdict === "fileable";

  return (
    <div className="space-y-6">
      <StepHeading
        title="Final verdict"
        lead="The forensic audit re-checks the draft against the facts and the statute, then gives a single verdict. This is decision support — a person makes the call."
      />

      <div className={cx("rounded-xl border-2 p-6", verdict.classes)}>
        <span className="text-2xl font-bold tracking-tight">{verdict.label}</span>
        <p className="mt-1.5 text-sm text-ink">{verdict.blurb}</p>
      </div>

      {fatal.length > 0 && (
        <div className="rounded-xl border-2 border-bad/50 bg-bad-bg p-5">
          <div className="flex items-center gap-2 text-bad">
            <span className="text-xl">⛔</span>
            <h2 className="text-base font-bold">Blocking defect — do not file</h2>
          </div>
          {fatal.map((f, i) => (
            <div key={i} className="mt-3 border-t border-bad/20 pt-3 first:border-0 first:pt-0">
              <p className="text-sm font-semibold text-ink">{f.issue}</p>
              <p className="mt-1 text-sm text-ink-soft">
                <span className="font-medium text-ink">Fix:</span> {f.suggested_fix}
              </p>
              {f.sopo_reference && <p className="tabular mt-1 text-xs text-ink-faint">{f.sopo_reference}</p>}
            </div>
          ))}
        </div>
      )}

      <Card>
        <div className="border-b border-line-soft px-4 py-2.5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
            Findings ({audit.findings.length})
          </h2>
          {audit.findings.length > 0 && (
            <p className="text-xs text-ink-faint">Click a finding to trace it back to the facts and source it came from.</p>
          )}
        </div>
        {audit.findings.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-ink-soft">
            Clean cross-check — every figure traces back to your facts and all mandatory particulars are present.
          </p>
        ) : (
          <ul className="divide-y divide-line-soft">
            {audit.findings.map((f, i) => (
              <FindingRow key={i} finding={f} facts={facts} />
            ))}
          </ul>
        )}
      </Card>

      <Card className="p-5">
        {acknowledged ? (
          <div className="rounded-lg border border-ok/30 bg-ok-bg px-4 py-3 text-sm text-ink">
            <span className="font-semibold text-ok">Marked ready for sign-off.</span> A quantity surveyor or
            construction lawyer must approve this claim before it is served. SiteClaim has not filed anything.
          </div>
        ) : (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-md text-sm text-ink-soft">
              {fileable
                ? "A person must give final approval. SiteClaim is decision support, not legal advice."
                : "Resolve the issues above, then re-run the audit. Filing stays locked until the verdict is clear."}
            </p>
            <Button onClick={() => setAcknowledged(true)} disabled={!fileable} title={fileable ? "" : "Locked until fileable"}>
              File claim
            </Button>
          </div>
        )}
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="subtle" onClick={onBack}>
          ← Back to draft
        </Button>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onShowSavings}>
            See the savings story →
          </Button>
          <Button variant="ghost" onClick={onReset}>
            Start over
          </Button>
        </div>
      </div>
    </div>
  );
}

function FindingRow({ finding, facts }: { finding: Finding; facts: ExtractedFacts }) {
  const [open, setOpen] = useState(false);
  const trace = traceFor(finding, facts);
  return (
    <li className="px-4 py-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-start gap-2 text-left"
      >
        <span className={cx("mt-1 text-xs text-ink-faint transition-transform", open && "rotate-90")}>▶</span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <SeverityTag severity={finding.severity} />
            <span className="tabular text-sm font-medium text-ink">{finding.location}</span>
            {finding.sopo_reference && <span className="tabular text-xs text-ink-faint">{finding.sopo_reference}</span>}
          </span>
          <span className="mt-1 block text-sm text-ink">{finding.issue}</span>
          <span className="mt-0.5 block text-sm text-ink-soft">
            <span className="font-medium text-ink">Fix:</span> {finding.suggested_fix}
          </span>
        </span>
      </button>

      {open && (
        <div className="ml-5 mt-3 rounded-lg border border-line-soft bg-paper/60 p-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded bg-brand-bg px-1.5 py-0.5 font-semibold text-brand">{trace.stage}</span>
          </div>
          <p className="mt-2 text-xs text-ink-soft">{trace.basis}</p>
          <ul className="mt-2 space-y-1.5">
            {trace.entries.map((e, i) => (
              <li key={i} className="rounded-md border border-line-soft bg-card px-2.5 py-1.5 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-ink">
                    <span className="font-medium">{e.label}:</span> <span className="tabular">{e.value}</span>
                  </span>
                  {e.confidence != null && <ConfidenceChip confidence={e.confidence} />}
                </div>
                {e.sourceSpan && (
                  <div className="mt-0.5 text-xs text-ink-faint">
                    source: <span className="tabular italic">“{e.sourceSpan}”</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}
