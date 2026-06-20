import type { ReactNode } from "react";
import type { ExtractedFacts } from "../types";
import { Button, Card, ConfidenceChip, cx } from "../ui";
import { StepHeading } from "./StepInput";

export function StepFacts({
  facts,
  onChange,
  onBack,
  onNext,
  loading,
}: {
  facts: ExtractedFacts;
  onChange: (f: ExtractedFacts) => void;
  onBack: () => void;
  onNext: () => void;
  loading: boolean;
}) {
  function set(mut: (f: ExtractedFacts) => void) {
    const next = structuredClone(facts);
    mut(next);
    onChange(next);
  }

  const claimant = facts.parties.claimant;
  const respondent = facts.parties.respondent;

  return (
    <div className="space-y-6">
      <StepHeading
        title="Review what we read"
        lead="These facts came from your documents. Each one shows how confident we are — amber and red need a look. Correct anything that's off; the next steps use exactly what you leave here."
      />

      <FactGroup title="The claim">
        <FactRow
          label="Reference date"
          type="date"
          field={facts.reference_date}
          onChange={(v) => set((f) => (f.reference_date.value = v || null))}
        />
        <FactRow
          label="Amount claimed"
          mono
          field={facts.claimed_amount}
          prefix="HKD"
          onChange={(v) => set((f) => (f.claimed_amount.value = v || null))}
        />
        <FactRow
          label="Contract sum"
          mono
          field={facts.contract_sum}
          prefix="HKD"
          onChange={(v) => set((f) => (f.contract_sum.value = v || null))}
        />
        <FactRow
          label="Contract type"
          field={facts.contract_type}
          onChange={(v) => set((f) => (f.contract_type.value = v || null))}
        />
        <Row label="Work period" confidence={facts.work_period.confidence} sourceSpan={facts.work_period.source_span}>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={facts.work_period.value?.start ?? ""}
              onChange={(e) =>
                set((f) => {
                  f.work_period.value = { start: e.target.value || null, end: f.work_period.value?.end ?? null };
                })
              }
              className={inputCls}
            />
            <span className="text-ink-faint">to</span>
            <input
              type="date"
              value={facts.work_period.value?.end ?? ""}
              onChange={(e) =>
                set((f) => {
                  f.work_period.value = { start: f.work_period.value?.start ?? null, end: e.target.value || null };
                })
              }
              className={inputCls}
            />
          </div>
        </Row>
      </FactGroup>

      <FactGroup title="The parties">
        <Row label="Claimant" confidence={claimant.confidence} sourceSpan={claimant.source_span}>
          <input
            value={claimant.value?.name ?? ""}
            placeholder="Claimant name"
            onChange={(e) =>
              set((f) => {
                const name = e.target.value;
                f.parties.claimant.value = name
                  ? { name, role: f.parties.claimant.value?.role ?? "subcontractor" }
                  : null;
              })
            }
            className={inputCls}
          />
        </Row>
        <Row label="Respondent" confidence={respondent.confidence} sourceSpan={respondent.source_span}>
          <input
            value={respondent.value?.name ?? ""}
            placeholder="Respondent name"
            onChange={(e) =>
              set((f) => {
                const name = e.target.value;
                f.parties.respondent.value = name
                  ? { name, role: f.parties.respondent.value?.role ?? "main contractor" }
                  : null;
              })
            }
            className={inputCls}
          />
        </Row>
      </FactGroup>

      <FactGroup title="Service of the claim">
        <FactRow
          label="Served on"
          field={facts.service.served_on}
          onChange={(v) => set((f) => (f.service.served_on.value = v || null))}
        />
        <FactRow
          label="Method"
          field={facts.service.method}
          onChange={(v) => set((f) => (f.service.method.value = v || null))}
        />
        <FactRow
          label="Date served"
          type="date"
          field={facts.service.date_served}
          onChange={(v) => set((f) => (f.service.date_served.value = v || null))}
        />
        <Row
          label="Proof of service kept"
          confidence={facts.service.proof_retained.confidence}
          sourceSpan={facts.service.proof_retained.source_span}
        >
          <select
            value={boolToStr(facts.service.proof_retained.value)}
            onChange={(e) => set((f) => (f.service.proof_retained.value = strToBool(e.target.value)))}
            className={inputCls}
          >
            <option value="">Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </Row>
      </FactGroup>

      {facts.supporting_doc_refs.length > 0 && (
        <FactGroup title="Supporting documents">
          <div className="flex flex-wrap gap-2 px-4 py-3">
            {facts.supporting_doc_refs.map((d) => (
              <span key={d} className="tabular rounded-md border border-line bg-paper/60 px-2 py-1 text-xs text-ink-soft">
                {d}
              </span>
            ))}
          </div>
        </FactGroup>
      )}

      <div className="flex items-center justify-between">
        <Button variant="subtle" onClick={onBack}>
          ← Back
        </Button>
        <Button onClick={onNext} loading={loading}>
          Looks right → check it
        </Button>
      </div>
    </div>
  );
}

const inputCls =
  "rounded-md border border-line bg-card px-2.5 py-1.5 text-sm text-ink focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand";

function FactGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
        {title}
      </h2>
      <div className="divide-y divide-line-soft">{children}</div>
    </Card>
  );
}

function Row({
  label,
  confidence,
  sourceSpan,
  children,
}: {
  label: string;
  confidence: number;
  sourceSpan: string | null;
  children: ReactNode;
}) {
  return (
    <div className="grid grid-cols-1 gap-2 px-4 py-3 sm:grid-cols-[10rem_1fr_auto] sm:items-center">
      <div className="text-sm font-medium text-ink">{label}</div>
      <div>
        {children}
        {sourceSpan && (
          <p className="mt-1 text-xs text-ink-faint">
            from your documents: <span className="tabular italic">“{sourceSpan}”</span>
          </p>
        )}
      </div>
      <div className="sm:justify-self-end">
        <ConfidenceChip confidence={confidence} />
      </div>
    </div>
  );
}

function FactRow({
  label,
  field,
  onChange,
  type = "text",
  mono,
  prefix,
}: {
  label: string;
  field: { value: string | null; confidence: number; source_span: string | null };
  onChange: (v: string) => void;
  type?: "text" | "date";
  mono?: boolean;
  prefix?: string;
}) {
  return (
    <Row label={label} confidence={field.confidence} sourceSpan={field.source_span}>
      <div className="flex items-center gap-2">
        {prefix && <span className="text-sm text-ink-faint">{prefix}</span>}
        <input
          type={type}
          value={field.value ?? ""}
          onChange={(e) => onChange(e.target.value)}
          className={cx(inputCls, mono && "tabular", "min-w-0 flex-1")}
        />
      </div>
    </Row>
  );
}

function boolToStr(v: boolean | null): string {
  return v === true ? "true" : v === false ? "false" : "";
}
function strToBool(v: string): boolean | null {
  return v === "true" ? true : v === "false" ? false : null;
}
