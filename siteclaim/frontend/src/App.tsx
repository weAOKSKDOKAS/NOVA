import { useEffect, useState } from "react";
import { api } from "./api";
import { Header, Stepper, type StepIndex } from "./components";
import type {
  AuditReport,
  ClaimDraft,
  DemoCase,
  ExtractedFacts,
  ReviewFlag,
  UploadedFile,
  ValidityReport,
} from "./types";
import { ErrorBanner } from "./ui";
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
    await run(async () => {
      const source = await api.demoCase(id);
      setCaseId(id);
      setDescription(source.description);
      setFiles(source.docs?.files ?? []);
      setFacts(null);
      invalidateAfter(1);
    });
  }

  const goExtract = () =>
    run(async () => {
      const source = { docs: { files }, description, case_id: caseId };
      const f = await api.extract(source);
      setFacts(f);
      invalidateAfter(2);
      advance(2);
    });

  const goVerify = () =>
    run(async () => {
      if (!facts) return;
      const res = await api.verify({ facts, case_id: caseId, source_description: description });
      setFacts(res.facts);
      setValidity(res.validity);
      setReviewFlags(res.review_flags);
      setJudgeSummary(res.judge_summary);
      advance(3);
    });

  const goDraft = () =>
    run(async () => {
      if (!facts || !validity) return;
      const d = await api.draft({ facts, validity });
      setDraft(d);
      setAudit(null);
      advance(4);
    });

  const goAudit = () =>
    run(async () => {
      if (!facts || !validity || !draft) return;
      const a = await api.audit({ facts, validity, draft });
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
  }

  return (
    <div className="min-h-screen">
      <Header demoMode={demoMode} notice={notice} />
      <main className="mx-auto max-w-6xl px-5 py-8">
        <div className="grid gap-8 lg:grid-cols-[16rem_1fr]">
          <Stepper current={step} maxReached={maxReached} onNavigate={setStep} />
          <div className="min-w-0 space-y-4">
            {error && <ErrorBanner message={error} />}

            {step === 1 && (
              <StepInput
                demoMode={demoMode}
                demoCases={demoCases}
                caseId={caseId}
                description={description}
                files={files}
                onPickDemo={pickDemo}
                onChangeDescription={(v) => {
                  setDescription(v);
                }}
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

            {step === 5 && audit && (
              <StepAudit audit={audit} onBack={() => setStep(4)} onReset={reset} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
