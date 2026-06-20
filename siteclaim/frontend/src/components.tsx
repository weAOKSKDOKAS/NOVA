import { cx } from "./ui";

export const STEPS = ["Input", "Facts", "Validity", "Draft", "Audit"] as const;
export type StepIndex = 1 | 2 | 3 | 4 | 5;
export type View = "wizard" | "savings";

const GATE_HINT: Record<number, string> = {
  1: "Describe the work",
  2: "Review what we read",
  3: "Check it against the law",
  4: "Read the draft",
  5: "Final verdict",
};

export function Header({
  demoMode,
  notice,
  view,
  onNavigate,
}: {
  demoMode: boolean;
  notice: string;
  view: View;
  onNavigate: (v: View) => void;
}) {
  return (
    <header className="border-b border-line bg-card">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3">
        <div className="flex items-center gap-2.5">
          <span className="text-lg font-bold tracking-tight text-ink">
            Site<span className="text-brand">Claim</span>
          </span>
          {demoMode && (
            <span
              className="inline-flex items-center gap-1.5 rounded-full bg-ink px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-white"
              title="Running offline against pre-recorded fixtures — zero network calls."
            >
              <span className="h-1.5 w-1.5 rounded-full bg-ok" />
              Demo mode
            </span>
          )}
        </div>

        <nav className="flex gap-1 sm:ml-2">
          <NavTab active={view === "wizard"} onClick={() => onNavigate("wizard")}>
            Wizard
          </NavTab>
          <NavTab active={view === "savings"} onClick={() => onNavigate("savings")}>
            Savings
          </NavTab>
        </nav>

        <p className="w-full text-xs text-ink-faint sm:ml-auto sm:w-auto sm:max-w-sm sm:text-right">
          {notice}
        </p>
      </div>
    </header>
  );
}

function NavTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={cx(
        "rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors",
        active ? "bg-brand-bg text-brand" : "text-ink-soft hover:bg-line-soft hover:text-ink",
      )}
    >
      {children}
    </button>
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
