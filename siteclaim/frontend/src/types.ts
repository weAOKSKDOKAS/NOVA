// TypeScript mirror of the backend Pydantic contracts (schemas/models.py).
// Note: Decimal and date both serialise to JSON *strings*.

export interface FF<T> {
  value: T | null;
  confidence: number;
  source_span: string | null;
}

export interface Party {
  name: string;
  role?: string | null;
  address?: string | null;
  contact?: string | null;
}

export interface Parties {
  claimant: FF<Party>;
  respondent: FF<Party>;
}

export interface WorkPeriod {
  start: string | null;
  end: string | null;
}

export interface LineItem {
  description: string;
  quantity?: string | null;
  unit?: string | null;
  rate?: string | null;
  amount: string | null;
  confidence: number;
  source_span?: string | null;
}

export interface ServiceDetails {
  method: FF<string>;
  served_on: FF<string>;
  date_served: FF<string>;
  proof_retained: FF<boolean>;
}

export interface PaymentResponseFacts {
  served: FF<boolean>;
  date_served: FF<string>;
  admitted_amount: FF<string>;
  disputes_claim: FF<boolean>;
}

export interface ExtractedFacts {
  contract_sum: FF<string>;
  contract_type: FF<string>;
  sector: FF<string>;
  parties: Parties;
  reference_date: FF<string>;
  claimed_amount: FF<string>;
  work_period: FF<WorkPeriod>;
  line_items: LineItem[];
  certified_amounts: unknown[];
  supporting_doc_refs: string[];
  contract_date: FF<string>;
  claim_served_date: FF<string>;
  claim_in_writing: FF<boolean>;
  service: ServiceDetails;
  payment_response: PaymentResponseFacts;
  extraction_notes?: string | null;
}

export type Severity = "fatal" | "warning" | "info";

export interface Check {
  name: string;
  passed: boolean;
  severity: Severity;
  sopo_reference: string;
  explanation: string;
}

export interface Deadline {
  name: string;
  due_date: string;
  business_days_remaining: number;
  sopo_reference: string;
}

export interface DeadlineSet {
  deadlines: Deadline[];
  computed_from: string | null;
  computed_at: string;
}

export interface ValidityReport {
  checks: Check[];
  deadlines: DeadlineSet | null;
  generated_at: string;
}

export interface ReviewFlag {
  field: string;
  confidence: number;
  value_repr: string | null;
  reason: string;
}

export interface ClaimDraft {
  claimant_name: string | null;
  respondent_name: string | null;
  contract_reference: string | null;
  reference_date: string | null;
  claimed_amount: string | null;
  currency: string;
  line_items: LineItem[];
  basis_of_calculation: string | null;
  statutory_statement: string | null;
  supporting_doc_refs: string[];
  rendered_markdown: string;
  generated_at: string;
}

export type AuditVerdict = "fileable" | "fileable_with_fixes" | "not_fileable";

export interface Finding {
  issue: string;
  location: string;
  severity: Severity;
  suggested_fix: string;
  sopo_reference?: string | null;
}

export interface AuditReport {
  findings: Finding[];
  verdict: AuditVerdict;
  generated_at: string;
}

export interface UploadedFile {
  filename: string;
  content_type: string;
  size_bytes?: number | null;
  storage_ref?: string | null;
  sha256?: string | null;
}

export interface SourceMaterial {
  docs: { files: UploadedFile[] };
  description: string;
  case_id: string | null;
  submitted_by?: string | null;
  submitted_at?: string | null;
}

export interface VerifyResponse {
  facts: ExtractedFacts;
  validity: ValidityReport;
  review_flags: ReviewFlag[];
  judge_summary: string;
}

export interface DemoCase {
  case_id: string;
  label: string;
  description: string;
}

export interface Health {
  status: string;
  config_version: string;
  demo_mode: boolean;
}

// A pre-recorded full-pipeline result for a demo case (the frontend's offline
// fallback). Mirrors what the wizard accumulates across the four stage calls.
export interface Snapshot {
  case_id: string;
  facts: ExtractedFacts;
  validity: ValidityReport;
  review_flags: ReviewFlag[];
  judge_summary: string;
  draft: ClaimDraft;
  audit: AuditReport;
}
