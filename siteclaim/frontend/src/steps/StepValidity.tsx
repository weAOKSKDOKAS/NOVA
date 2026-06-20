import type { Deadline, ReviewFlag, ValidityReport } from "../types";
import { Button, Card, cx, SeverityTag } from "../ui";
import { StepHeading } from "./StepInput";

export function StepValidity({
  validity,
  reviewFlags,
  judgeSummary,
  onBack,
  onNext,
  loading,
}: {
  validity: ValidityReport;
  reviewFlags: ReviewFlag[];
  judgeSummary: string;
  onBack: () => void;
  onNext: () => void;
  loading: boolean;
}) {
  const fatal = validity.checks.filter((c) => c.severity === "fatal" && !c.passed);
  const deadlines = validity.deadlines?.deadlines ?? [];
  const nearest = pickNearest(deadlines);

  return (
    <div className="space-y-6">
      <StepHeading
        title="Check it against the law"
        lead="The rules engine — not the AI — runs every SOPO requirement deterministically. Fatal issues void the claim; warnings need a human's eye."
      />

      {fatal.length > 0 ? (
        <div className="rounded-xl border-2 border-bad/40 bg-bad-bg p-5">
          <div className="flex items-center gap-2 text-bad">
            <span className="text-lg">⛔</span>
            <h2 className="text-base font-bold">This claim can't be filed as it stands</h2>
          </div>
          <ul className="mt-3 space-y-2">
            {fatal.map((c) => (
              <li key={c.name} className="text-sm text-ink">
                <span className="tabular font-semibold text-bad">{c.name}</span> — {c.explanation}{" "}
                <span className="tabular text-ink-faint">({c.sopo_reference})</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="rounded-xl border border-ok/30 bg-ok-bg p-4 text-sm text-ink">
          <span className="font-semibold text-ok">No fatal defects.</span> The claim clears the statutory checks — any
          warnings below are for a person to weigh.
        </div>
      )}

      {nearest && (
        <Card className="overflow-hidden">
          <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
            Deadline clock
          </h2>
          <div className="grid gap-4 p-4 sm:grid-cols-[auto_1fr] sm:items-center">
            <div className="rounded-lg border border-line bg-paper/50 px-5 py-3 text-center">
              <div className={cx("tabular text-3xl font-bold", clockColor(nearest.business_days_remaining))}>
                {nearest.business_days_remaining}
              </div>
              <div className="text-xs text-ink-faint">business days</div>
            </div>
            <div>
              <div className="text-sm font-semibold text-ink">Next: {humanize(nearest.name)}</div>
              <div className="tabular text-sm text-ink-soft">
                due {nearest.due_date} · {nearest.sopo_reference}
              </div>
            </div>
          </div>
          {deadlines.length > 1 && (
            <ul className="divide-y divide-line-soft border-t border-line-soft">
              {deadlines.map((d) => (
                <li key={d.name} className="flex items-center justify-between px-4 py-2 text-sm">
                  <span className="text-ink">{humanize(d.name)}</span>
                  <span className="tabular text-ink-soft">
                    {d.due_date}{" "}
                    <span className={clockColor(d.business_days_remaining)}>
                      ({d.business_days_remaining > 0 ? "+" : ""}
                      {d.business_days_remaining} bd)
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
          All checks ({validity.checks.length})
        </h2>
        <ul className="divide-y divide-line-soft">
          {validity.checks.map((c) => (
            <li key={c.name} className="flex items-start gap-3 px-4 py-2.5">
              <span className={cx("mt-0.5 text-sm", c.passed ? "text-ok" : "text-bad")}>
                {c.passed ? "✓" : "✗"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="tabular text-sm font-medium text-ink">{c.name}</span>
                  <SeverityTag severity={c.severity} />
                  <span className="tabular text-xs text-ink-faint">{c.sopo_reference}</span>
                </div>
                <p className="mt-0.5 text-sm text-ink-soft">{c.explanation}</p>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {reviewFlags.length > 0 && (
        <div className="rounded-lg border border-warn/30 bg-warn-bg px-4 py-3 text-sm text-ink">
          <span className="font-semibold text-warn">
            {reviewFlags.length} field{reviewFlags.length > 1 ? "s" : ""} flagged to double-check.
          </span>{" "}
          {judgeSummary || "Go back a step to confirm the highlighted values."}
        </div>
      )}

      <div className="flex items-center justify-between">
        <Button variant="subtle" onClick={onBack}>
          ← Back
        </Button>
        <Button onClick={onNext} loading={loading}>
          Draft my claim →
        </Button>
      </div>
    </div>
  );
}

function pickNearest(deadlines: Deadline[]): Deadline | null {
  if (deadlines.length === 0) return null;
  const upcoming = deadlines.filter((d) => d.business_days_remaining >= 0);
  const pool = upcoming.length > 0 ? upcoming : deadlines;
  return pool.reduce((a, b) => (a.due_date <= b.due_date ? a : b));
}

function clockColor(bd: number): string {
  if (bd < 0) return "text-bad";
  if (bd <= 5) return "text-warn";
  return "text-ink";
}

function humanize(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}
