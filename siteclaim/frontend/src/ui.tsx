import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { AuditVerdict, Severity } from "./types";

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

// --- Confidence ------------------------------------------------------------
type Tier = { label: string; chip: string; ring: string };

export function confidenceTier(confidence: number): Tier {
  if (confidence >= 0.8) {
    return { label: "High confidence", chip: "bg-ok-bg text-ok", ring: "border-ok/40" };
  }
  if (confidence >= 0.6) {
    return { label: "Worth a check", chip: "bg-warn-bg text-warn", ring: "border-warn/50" };
  }
  return { label: "Low — please confirm", chip: "bg-bad-bg text-bad", ring: "border-bad/50" };
}

export function ConfidenceChip({ confidence }: { confidence: number }) {
  const tier = confidenceTier(confidence);
  return (
    <span
      className={cx(
        "tabular inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        tier.chip,
      )}
      title={tier.label}
    >
      {confidence.toFixed(2)}
      <span className="font-sans">· {tier.label}</span>
    </span>
  );
}

// --- Severity --------------------------------------------------------------
const SEVERITY: Record<Severity, { label: string; classes: string; dot: string }> = {
  fatal: { label: "Fatal", classes: "bg-bad-bg text-bad", dot: "bg-bad" },
  warning: { label: "Warning", classes: "bg-warn-bg text-warn", dot: "bg-warn" },
  info: { label: "Info", classes: "bg-brand-bg text-brand", dot: "bg-brand" },
};

export function SeverityTag({ severity }: { severity: Severity }) {
  const s = SEVERITY[severity];
  return (
    <span className={cx("inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-semibold uppercase tracking-wide", s.classes)}>
      <span className={cx("h-1.5 w-1.5 rounded-full", s.dot)} />
      {s.label}
    </span>
  );
}

// --- Verdict ---------------------------------------------------------------
export const VERDICT: Record<AuditVerdict, { label: string; classes: string; blurb: string }> = {
  fileable: {
    label: "Fileable",
    classes: "bg-ok-bg text-ok border-ok/30",
    blurb: "No blocking defects found. Ready for a person to approve.",
  },
  fileable_with_fixes: {
    label: "Fileable with fixes",
    classes: "bg-warn-bg text-warn border-warn/40",
    blurb: "No fatal defects, but some particulars need confirming first.",
  },
  not_fileable: {
    label: "Not fileable",
    classes: "bg-bad-bg text-bad border-bad/40",
    blurb: "A fatal defect would void this claim. Do not serve it as-is.",
  },
};

// --- Button ----------------------------------------------------------------
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "subtle";
  loading?: boolean;
};

export function Button({ variant = "primary", loading, children, className, disabled, ...rest }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-bright focus-visible:ring-offset-2 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-brand text-white hover:bg-brand-bright disabled:bg-ink-faint",
    ghost: "border border-line bg-card text-ink hover:bg-line-soft disabled:text-ink-faint",
    subtle: "text-ink-soft hover:text-ink disabled:text-ink-faint",
  };
  return (
    <button className={cx(base, variants[variant], className)} disabled={disabled || loading} {...rest}>
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function Spinner() {
  return (
    <span
      className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
      aria-hidden
    />
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cx("rounded-xl border border-line bg-card", className)}>{children}</div>;
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-bad/30 bg-bad-bg px-4 py-3 text-sm text-bad">
      <span className="font-semibold">Something went wrong.</span> {message}
    </div>
  );
}

export function InfoNotice({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-warn/30 bg-warn-bg px-4 py-2.5 text-sm text-ink">{children}</div>
  );
}

// A hover/focus "ⓘ" carrying an assumption basis as its tooltip. Keyboard-focusable.
export function InfoDot({ title }: { title: string }) {
  return (
    <span
      tabIndex={0}
      role="note"
      aria-label={title}
      title={title}
      className="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-line text-[10px] font-bold text-ink-faint align-middle focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-bright"
    >
      i
    </span>
  );
}
