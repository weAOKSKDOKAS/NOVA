import { useState } from "react";
import type { AuditReport, Finding } from "../types";
import { Button, Card, cx, SeverityTag, VERDICT } from "../ui";
import { StepHeading } from "./StepInput";

export function StepAudit({
  audit,
  onBack,
  onReset,
}: {
  audit: AuditReport;
  onBack: () => void;
  onReset: () => void;
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
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-2xl font-bold tracking-tight">{verdict.label}</span>
        </div>
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
        <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
          Findings ({audit.findings.length})
        </h2>
        {audit.findings.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-ink-soft">
            Clean cross-check — every figure traces back to your facts and all mandatory particulars are present.
          </p>
        ) : (
          <ul className="divide-y divide-line-soft">
            {audit.findings.map((f, i) => (
              <FindingRow key={i} finding={f} />
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

      <div className="flex items-center justify-between">
        <Button variant="subtle" onClick={onBack}>
          ← Back to draft
        </Button>
        <Button variant="ghost" onClick={onReset}>
          Start over
        </Button>
      </div>
    </div>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityTag severity={finding.severity} />
        <span className="tabular text-sm font-medium text-ink">{finding.location}</span>
        {finding.sopo_reference && (
          <span className="tabular text-xs text-ink-faint">{finding.sopo_reference}</span>
        )}
      </div>
      <p className="mt-1 text-sm text-ink">{finding.issue}</p>
      <p className="mt-0.5 text-sm text-ink-soft">
        <span className="font-medium text-ink">Fix:</span> {finding.suggested_fix}
      </p>
    </li>
  );
}
