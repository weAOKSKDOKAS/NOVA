import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ClaimDraft } from "../types";
import { Button, Card } from "../ui";
import { StepHeading } from "./StepInput";

export function StepDraft({
  draft,
  onChangeMarkdown,
  onBack,
  onNext,
  loading,
}: {
  draft: ClaimDraft;
  onChangeMarkdown: (v: string) => void;
  onBack: () => void;
  onNext: () => void;
  loading: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const md = draft.rendered_markdown;
  const banner = bannerFor(md);

  return (
    <div className="space-y-6">
      <StepHeading
        title="Read the draft"
        lead="SiteClaim drafted this from your facts, following the CIC template. Nothing is invented — gaps show as marked placeholders. Edit anything before the final audit."
      />

      {banner && (
        <div
          className={
            banner.tone === "bad"
              ? "rounded-xl border-2 border-bad/40 bg-bad-bg p-4 text-sm text-ink"
              : "rounded-xl border border-warn/40 bg-warn-bg p-4 text-sm text-ink"
          }
        >
          <span className={banner.tone === "bad" ? "font-bold text-bad" : "font-bold text-warn"}>
            {banner.title}
          </span>{" "}
          {banner.body}
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line-soft px-4 py-2.5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-soft">Payment claim — draft</h2>
          <div className="flex gap-1">
            <ToggleButton active={!editing} onClick={() => setEditing(false)}>
              Preview
            </ToggleButton>
            <ToggleButton active={editing} onClick={() => setEditing(true)}>
              Edit text
            </ToggleButton>
          </div>
        </div>
        {editing ? (
          <textarea
            value={md}
            onChange={(e) => onChangeMarkdown(e.target.value)}
            spellCheck={false}
            className="tabular block h-[28rem] w-full resize-y border-0 bg-card p-5 text-xs leading-relaxed text-ink focus:outline-none"
          />
        ) : (
          <div className="doc max-h-[32rem] overflow-y-auto p-6">
            <Markdown remarkPlugins={[remarkGfm]}>{md}</Markdown>
          </div>
        )}
      </Card>

      <div className="flex items-center justify-between">
        <Button variant="subtle" onClick={onBack}>
          ← Back
        </Button>
        <Button onClick={onNext} loading={loading}>
          Run final audit →
        </Button>
      </div>
    </div>
  );
}

function ToggleButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-md bg-brand-bg px-2.5 py-1 text-xs font-semibold text-brand"
          : "rounded-md px-2.5 py-1 text-xs font-medium text-ink-faint hover:text-ink"
      }
    >
      {children}
    </button>
  );
}

function bannerFor(md: string): { tone: "bad" | "warn"; title: string; body: string } | null {
  if (md.includes("NOT FILEABLE")) {
    return {
      tone: "bad",
      title: "Not fileable yet.",
      body: "The draft carries a fatal defect (shown at the top of the document). Fix it before serving.",
    };
  }
  if (md.includes("DRAFT — not ready")) {
    return {
      tone: "warn",
      title: "Draft — not ready to file.",
      body: "Some mandatory particulars are missing or low-confidence and appear as placeholders. Confirm them first.",
    };
  }
  return null;
}
