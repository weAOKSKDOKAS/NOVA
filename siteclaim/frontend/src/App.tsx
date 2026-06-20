import { useEffect, useState } from "react";
import { api } from "./api";
import { Header, Stepper, type StepIndex, type View } from "./components";
import { SNAPSHOTS } from "./demo";
import { SavingsDashboard } from "./SavingsDashboard";
import type {
  AuditReport,
  ClaimDraft,
  DemoCase,
  ExtractedFacts,
  ReviewFlag,
  Snapshot,
  UploadedFile,
  ValidityReport,
} from "./types";
import { ErrorBanner, InfoNotice } from "./ui";
import { StepInput } from "./steps/StepInput";
import { StepFacts } from "./steps/StepFacts";
import { StepValidity } from "./steps/StepValidity";
import { StepDraft } from "./steps/StepDraft";
import { StepAudit } from "./steps/StepAudit";

const FALLBACK_NOTICE =
  "Decision support, not legal advice. Statutory values are unverified — a quantity surveyor or lawyer must confirm before filing.";

export default function App() {
  // Meta
  const [demoMode, setDemoMode] = useState(true);
  const [notice, setNotice] = useState(FALLBACK_NOTICE);
  const [demoCases, setDemoCases] = useState<DemoCase[]>([]);
  const [view, setView] = useState<View>("wizard");

  // Navigation
  const [step, setStep] = useState<StepIndex>(1);
  const [maxReached, setMaxReached] = useState<StepIndex>(1);

  // Pipeline state
  const [caseId, setCaseId] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [facts, setFacts] = useState<ExtractedFacts | null>(null);
  const [validity, setValidity] = useState<ValidityReport | null>(null);
  const [reviewFlags, setReviewFlags] = useState<ReviewFlag[]>([]);
  const [judgeSummary, setJudgeSummary] = useState("");
  const [draft, setDraft] = useState<ClaimDraft | null>(null);
  const [audit, setAudit] = useState<AuditReport | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState<string | null>(null);

  useEffect(() => {
    api.health().then((h) => setDemoMode(h.demo_mode)).catch(() => {});
    api.legalNotice().then((n) => setNotice(n.warning)).catch(() => {});
    api.demoCases().then(setDemoCases).catch(() => {});
  }, []);

  async function run(fn: () => Promise<void>) {
    setLoading(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  // Graceful degradation: if a live stage call fails mid-demo, fall back to the
  // pre-recorded snapshot for this case so the demo never hard-crashes.
  async function withFallback<T>(call: () => Promise<T>, fromSnapshot: (s: Snapshot) => T): Promise<T> {
    try {
      return await call();
    } catch (e) {
      const snap = caseId ? SNAPSHOTS[caseId] : undefined;
      if (snap) {
        setDegraded(`Couldn't reach the live pipeline — showing the recorded result for the “${caseId}” case.`);
        return fromSnapshot(snap);
      }
      throw e;
    }
  }

  function advance(to: StepIndex) {
    setStep(to);
    setMaxReached((m) => (to > m ? to : m));
  }

  // Editing a gate invalidates every later gate (the ICM review-gate rule).
  function invalidateAfter(keep: StepIndex) {
    if (keep < 3) {
      setValidity(null);
      setReviewFlags([]);
      setJudgeSummary("");
    }
    if (keep < 4) setDraft(null);
    if (keep < 5) setAudit(null);
    setMaxReached((m) => (m > keep ? keep : m));
  }

  async function pickDemo(id: string) {
    setDegraded(null);
    await run(async () => {
      setCaseId(id);
      try {
        const source = await api.demoCase(id);
        setDescription(source.description);
        setFiles(source.docs?.files ?? []);
      } catch {
        // Even the source fetch failed — start from the bundled snapshot.
        setDescription(`Demo case: ${id}`);
        setFiles([]);
        if (SNAPSHOTS[id]) setDegraded(`Couldn't reach the server — loading the “${id}” case from bundled fixtures.`);
      }
      setFacts(null);
      invalidateAfter(1);
    });
  }

  const goExtract = () =>
    run(async () => {
      const source = { docs: { files }, description, case_id: caseId };
      const f = await withFallback(() => api.extract(source), (s) => s.facts);
      setFacts(f);
      invalidateAfter(2);
      advance(2);
    });

  const goVerify = () =>
    run(async () => {
      if (!facts) return;
      const res = await withFallback(
        () => api.verify({ facts, case_id: caseId, source_description: description }),
        (s) => ({ facts: s.facts, validity: s.validity, review_flags: s.review_flags, judge_summary: s.judge_summary }),
      );
      setFacts(res.facts);
      setValidity(res.validity);
      setReviewFlags(res.review_flags);
      setJudgeSummary(res.judge_summary);
      advance(3);
    });

  const goDraft = () =>
    run(async () => {
      if (!facts || !validity) return;
      const d = await withFallback(() => api.draft({ facts, validity }), (s) => s.draft);
      setDraft(d);
      setAudit(null);
      advance(4);
    });

  const goAudit = () =>
    run(async () => {
      if (!facts || !validity || !draft) return;
      const a = await withFallback(() => api.audit({ facts, validity, draft }), (s) => s.audit);
      setAudit(a);
      advance(5);
    });

  function reset() {
    setStep(1);
    setMaxReached(1);
    setCaseId(null);
    setDescription("");
    setFiles([]);
    setFacts(null);
    setValidity(null);
    setReviewFlags([]);
    setJudgeSummary("");
    setDraft(null);
    setAudit(null);
    setError(null);
    setDegraded(null);
    setView("wizard");
  }

  return (
    <div className="min-h-screen">
      <Header demoMode={demoMode} notice={notice} view={view} onNavigate={setView} />
      <main className="mx-auto max-w-6xl px-5 py-8">
        {view === "savings" ? (
          <SavingsDashboard onBack={() => setView("wizard")} />
        ) : (
          <div className="grid gap-8 lg:grid-cols-[16rem_1fr]">
            <Stepper current={step} maxReached={maxReached} onNavigate={setStep} />
            <div className="min-w-0 space-y-4">
              {error && <ErrorBanner message={error} />}
              {degraded && <InfoNotice>{degraded}</InfoNotice>}

              {step === 1 && (
                <StepInput
                  demoMode={demoMode}
                  demoCases={demoCases}
                  caseId={caseId}
                  description={description}
                  files={files}
                  onPickDemo={pickDemo}
                  onChangeDescription={setDescription}
                  onAddFiles={(f) => setFiles((cur) => [...cur, ...f])}
                  onRemoveFile={(i) => setFiles((cur) => cur.filter((_, idx) => idx !== i))}
                  onNext={goExtract}
                  loading={loading}
                />
              )}

              {step === 2 && facts && (
                <StepFacts
                  facts={facts}
                  onChange={(f) => {
                    setFacts(f);
                    invalidateAfter(2);
                  }}
                  onBack={() => setStep(1)}
                  onNext={goVerify}
                  loading={loading}
                />
              )}

              {step === 3 && validity && (
                <StepValidity
                  validity={validity}
                  reviewFlags={reviewFlags}
                  judgeSummary={judgeSummary}
                  onBack={() => setStep(2)}
                  onNext={goDraft}
                  loading={loading}
                />
              )}

              {step === 4 && draft && (
                <StepDraft
                  draft={draft}
                  onChangeMarkdown={(v) => {
                    setDraft({ ...draft, rendered_markdown: v });
                    invalidateAfter(4);
                  }}
                  onBack={() => setStep(3)}
                  onNext={goAudit}
                  loading={loading}
                />
              )}

              {step === 5 && audit && facts && (
                <StepAudit
                  audit={audit}
                  facts={facts}
                  onBack={() => setStep(4)}
                  onReset={reset}
                  onShowSavings={() => setView("savings")}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
