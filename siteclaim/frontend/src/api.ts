import type {
  AuditReport,
  ClaimDraft,
  DemoCase,
  ExtractedFacts,
  Health,
  SourceMaterial,
  ValidityReport,
  VerifyResponse,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep the status line */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

function get<T>(path: string): Promise<T> {
  return fetch(BASE + path).then((r) => handle<T>(r));
}

function post<T>(path: string, body: unknown): Promise<T> {
  return fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => handle<T>(r));
}

export interface VerifyRequest {
  facts: ExtractedFacts;
  case_id: string | null;
  source_description?: string;
}

export const api = {
  base: BASE,
  health: () => get<Health>("/health"),
  legalNotice: () => get<{ warning: string; source: string }>("/legal-notice"),
  demoCases: () => get<DemoCase[]>("/demo/cases"),
  demoCase: (id: string) => get<SourceMaterial>(`/demo/${id}`),
  extract: (source: SourceMaterial) => post<ExtractedFacts>("/extract", source),
  // Live multimodal extraction: POST the raw files as multipart/form-data.
  extractUpload: (files: File[], description: string, caseId: string | null) => {
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    fd.append("description", description);
    if (caseId) fd.append("case_id", caseId);
    return fetch(BASE + "/extract-upload", { method: "POST", body: fd }).then((r) => handle<ExtractedFacts>(r));
  },
  verify: (req: VerifyRequest) => post<VerifyResponse>("/verify", req),
  draft: (req: { facts: ExtractedFacts; validity: ValidityReport }) => post<ClaimDraft>("/draft", req),
  audit: (req: { facts: ExtractedFacts; validity: ValidityReport; draft: ClaimDraft }) =>
    post<AuditReport>("/audit", req),
};
