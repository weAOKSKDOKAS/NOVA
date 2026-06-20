// Savings model — every figure in the dashboard derives from these assumptions.
// NONE are measured; each carries its basis so a judge can see (and argue) the
// economics rather than be handed an unlabelled round number.

export type Scenario = "bear" | "base" | "bull";
export const SCENARIOS: Scenario[] = ["bear", "base", "bull"];
export const SCENARIO_LABEL: Record<Scenario, string> = { bear: "Bear", base: "Base", bull: "Bull" };

export interface Assumption<T> {
  value: T;
  basis: string; // always begins "ASSUMPTION — adjustable, not measured."
}

const A = "ASSUMPTION — adjustable, not measured.";

export const ASSUMPTIONS = {
  qsHourlyRateHkd: {
    value: 800,
    basis: `${A} Blended Hong Kong QS / commercial charge-out rate, HK$ per hour.`,
  } as Assumption<number>,
  manualHoursPerClaim: {
    value: 5,
    basis: `${A} QS time to draft and check one SOPO payment claim by hand, in hours.`,
  } as Assumption<number>,
  siteclaimMinutesPerClaim: {
    value: { bear: 180, base: 120, bull: 75 },
    basis: `${A} Hands-on time in SiteClaim including human review at every gate, in minutes (bear / base / bull).`,
  } as Assumption<Record<Scenario, number>>,
  rejectionRateBefore: {
    value: 0.2,
    basis: `${A} Share of claims rejected on technicalities (wrong party, defective service, missing particulars) without SiteClaim.`,
  } as Assumption<number>,
  rejectionRateAfter: {
    value: 0.05,
    basis: `${A} Residual technicality-rejection rate after SiteClaim's deterministic gates.`,
  } as Assumption<number>,
};

export interface Savings {
  scenario: Scenario;
  manualHours: number;
  siteclaimHours: number;
  timeSavedHours: number;
  timeSavedPct: number; // 0..1, derived
  costSavedPerClaim: number; // HK$
  costSavedPer100: number; // HK$
}

export function savingsFor(scenario: Scenario): Savings {
  const manualHours = ASSUMPTIONS.manualHoursPerClaim.value;
  const siteclaimHours = ASSUMPTIONS.siteclaimMinutesPerClaim.value[scenario] / 60;
  const timeSavedHours = manualHours - siteclaimHours;
  const costSavedPerClaim = timeSavedHours * ASSUMPTIONS.qsHourlyRateHkd.value;
  return {
    scenario,
    manualHours,
    siteclaimHours,
    timeSavedHours,
    timeSavedPct: timeSavedHours / manualHours,
    costSavedPerClaim,
    costSavedPer100: costSavedPerClaim * 100,
  };
}

export interface RejectionImpact {
  beforePer100: number;
  afterPer100: number;
  avoidedPer100: number;
  relativeReductionPct: number; // 0..1
}

export function rejectionImpact(): RejectionImpact {
  const beforePer100 = ASSUMPTIONS.rejectionRateBefore.value * 100;
  const afterPer100 = ASSUMPTIONS.rejectionRateAfter.value * 100;
  return {
    beforePer100,
    afterPer100,
    avoidedPer100: beforePer100 - afterPer100,
    relativeReductionPct: (beforePer100 - afterPer100) / beforePer100,
  };
}

export const hkd = (n: number) => `HK$${Math.round(n).toLocaleString("en-HK")}`;
export const pct = (n: number) => `${Math.round(n * 100)}%`;
