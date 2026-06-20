import type { ChangeEvent } from "react";
import type { DemoCase } from "../types";
import { Button, Card, cx } from "../ui";

export function StepInput({
  demoMode,
  demoCases,
  caseId,
  description,
  files,
  onPickDemo,
  onChangeDescription,
  onAddFiles,
  onRemoveFile,
  onNext,
  loading,
}: {
  demoMode: boolean;
  demoCases: DemoCase[];
  caseId: string | null;
  description: string;
  files: File[];
  onPickDemo: (caseId: string) => void;
  onChangeDescription: (v: string) => void;
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (i: number) => void;
  onNext: () => void;
  loading: boolean;
}) {
  function onFileInput(e: ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(e.target.files ?? []);
    if (picked.length) onAddFiles(picked);
    e.target.value = "";
  }

  const liveUpload = !demoMode && files.length > 0;

  const blockedInDemo = demoMode && !caseId;
  const canAdvance = !blockedInDemo && (!!caseId || description.trim().length > 0 || files.length > 0);

  return (
    <div className="space-y-6">
      <StepHeading
        title="Tell us about the claim"
        lead="Describe the work you did and attach what you have — the contract, invoices, site records. SiteClaim reads it into the facts a SOPO payment claim depends on."
      />

      <Card className="p-5">
        <label className="mb-2 block text-sm font-semibold text-ink">Load a demo case</label>
        <p className="mb-3 text-xs text-ink-faint">
          {demoMode
            ? "Demo mode is offline. Pick a prepared case to run the whole pipeline without the live AI."
            : "Prepared examples — handy to see the flow end to end."}
        </p>
        <div className="flex flex-wrap gap-2">
          {demoCases.map((c) => (
            <button
              key={c.case_id}
              type="button"
              onClick={() => onPickDemo(c.case_id)}
              className={cx(
                "rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                caseId === c.case_id
                  ? "border-brand bg-brand-bg text-brand"
                  : "border-line bg-card text-ink hover:bg-line-soft",
              )}
            >
              <span className="block font-semibold">{c.label}</span>
              <span className="block text-xs text-ink-faint">{c.case_id}</span>
            </button>
          ))}
        </div>
      </Card>

      <Card className="p-5">
        <label htmlFor="desc" className="mb-2 block text-sm font-semibold text-ink">
          Describe the work you did
        </label>
        <textarea
          id="desc"
          value={description}
          onChange={(e) => onChangeDescription(e.target.value)}
          rows={6}
          placeholder="e.g. Rebar fixing to grid C–F in February 2026 under our subcontract with…"
          className="w-full resize-y rounded-lg border border-line bg-card px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />

        <div className="mt-4">
          <span className="mb-2 block text-sm font-semibold text-ink">
            Attach documents <span className="font-normal text-ink-faint">(optional)</span>
          </span>
          <label className="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-line bg-paper/50 px-4 py-5 text-sm text-ink-soft hover:border-brand hover:text-brand">
            <input type="file" multiple accept="application/pdf,image/*" className="sr-only" onChange={onFileInput} />
            Choose files — invoice or contract (PDF, JPEG, PNG)
          </label>
          {files.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {files.map((f, i) => (
                <li
                  key={`${f.name}-${i}`}
                  className="flex items-center justify-between rounded-md border border-line-soft bg-paper/50 px-3 py-1.5 text-sm"
                >
                  <span className="truncate text-ink">{f.name}</span>
                  <button
                    type="button"
                    onClick={() => onRemoveFile(i)}
                    className="ml-3 shrink-0 text-xs font-medium text-ink-faint hover:text-bad"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
          {liveUpload && (
            <p className="mt-2 text-xs text-brand">
              These will be read directly by the live AI (DeepSeek vision) — the facts come from the document itself.
            </p>
          )}
        </div>
      </Card>

      {blockedInDemo && (
        <p className="text-sm text-warn">
          Pick a demo case above to continue — free-text extraction needs the live AI, which is off in demo mode.
        </p>
      )}

      <div className="flex justify-end">
        <Button onClick={onNext} loading={loading} disabled={!canAdvance}>
          Read my documents →
        </Button>
      </div>
    </div>
  );
}

export function StepHeading({ title, lead }: { title: string; lead: string }) {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-ink">{title}</h1>
      <p className="mt-1.5 max-w-2xl text-sm text-ink-soft">{lead}</p>
    </div>
  );
}
