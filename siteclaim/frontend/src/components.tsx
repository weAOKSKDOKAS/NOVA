import { cx } from "./ui";

export const STEPS = ["Input", "Facts", "Validity", "Draft", "Audit"] as const;
export type StepIndex = 1 | 2 | 3 | 4 | 5;

const GATE_HINT: Record<number, string> = {
  1: "Describe the work",
  2: "Review what we read",
  3: "Check it against the law",
  4: "Read the draft",
  5: "Final verdict",
};

export function Header({ demoMode, notice }: { demoMode: boolean; notice: string }) {
  return (
    <header className="border-b border-line bg-card">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3">
        <div className="flex items-baseline gap-2.5">
          <span className="text-lg font-bold tracking-tight text-ink">
            Site<span className="text-brand">Claim</span>
          </span>
          <span className="hidden text-sm text-ink-soft sm:inline">
            SOPO payment-claim copilot · Cap. 652
          </span>
        </div>
        {demoMode && (
          <span className="tabular rounded-full bg-brand-bg px-2.5 py-0.5 text-xs font-medium text-brand">
            demo mode · offline
          </span>
        )}
        <p className="w-full text-xs text-ink-faint sm:ml-auto sm:w-auto sm:max-w-md sm:text-right">
          {notice}
        </p>
      </div>
    </header>
  );
}

export function Stepper({
  current,
  maxReached,
  onNavigate,
}: {
  current: StepIndex;
  maxReached: StepIndex;
  onNavigate: (s: StepIndex) => void;
}) {
  return (
    <nav aria-label="Progress" className="lg:sticky lg:top-6">
      <ol className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:gap-0 lg:overflow-visible lg:pb-0">
        {STEPS.map((label, i) => {
          const step = (i + 1) as StepIndex;
          const state = step === current ? "active" : step < current ? "done" : "upcoming";
          const reachable = step <= maxReached;
          const isLast = i === STEPS.length - 1;
          return (
            <li key={label} className="relative flex shrink-0 lg:block">
              {!isLast && (
                <span
                  aria-hidden
                  className={cx(
                    "absolute hidden lg:block",
                    "left-[15px] top-8 h-[calc(100%-1.5rem)] w-px",
                    step < current ? "bg-brand" : "bg-line",
                  )}
                />
              )}
              <button
                type="button"
                disabled={!reachable}
                onClick={() => reachable && onNavigate(step)}
                className={cx(
                  "group flex items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors lg:w-full",
                  reachable ? "cursor-pointer hover:bg-line-soft" : "cursor-not-allowed",
                  state === "active" && "bg-brand-bg/60",
                )}
              >
                <span
                  className={cx(
                    "tabular flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold",
                    state === "active" && "border-brand bg-brand text-white",
                    state === "done" && "border-brand bg-card text-brand",
                    state === "upcoming" && "border-line bg-card text-ink-faint",
                  )}
                >
                  {state === "done" ? "✓" : step}
                </span>
                <span className="pr-2">
                  <span
                    className={cx(
                      "block text-sm font-semibold",
                      state === "upcoming" ? "text-ink-faint" : "text-ink",
                    )}
                  >
                    {label}
                  </span>
                  <span className="hidden text-xs text-ink-faint lg:block">{GATE_HINT[step]}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
