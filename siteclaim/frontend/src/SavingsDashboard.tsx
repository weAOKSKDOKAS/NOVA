import type { ReactNode } from "react";
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  ASSUMPTIONS,
  hkd,
  pct,
  rejectionImpact,
  savingsFor,
  SCENARIO_LABEL,
  SCENARIOS,
} from "./assumptions";
import { Button, Card, InfoDot } from "./ui";

const INK = "#15212e";
const BRAND = "#1f4e8c";
const OK = "#1a7f55";
const OK_SOFT = "#7fb89a";
const BAD = "#b42318";
const FAINT = "#8595a3";

const base = savingsFor("base");
const bear = savingsFor("bear");
const bull = savingsFor("bull");
const rej = rejectionImpact();

const hours = (n: number) => `${n.toLocaleString("en-HK", { maximumFractionDigits: 2 })} h`;
const count = (n: number) => `${n}`;

const timeBasis = `${ASSUMPTIONS.manualHoursPerClaim.basis}\n\n${ASSUMPTIONS.siteclaimMinutesPerClaim.basis}`;
const costBasis = `${timeBasis}\n\n${ASSUMPTIONS.qsHourlyRateHkd.basis}`;

export function SavingsDashboard({ onBack }: { onBack: () => void }) {
  const timeData = [
    { name: "Manual QS", value: base.manualHours, fill: FAINT, note: ASSUMPTIONS.manualHoursPerClaim.basis },
    { name: "With SiteClaim", value: base.siteclaimHours, fill: BRAND, note: ASSUMPTIONS.siteclaimMinutesPerClaim.basis },
  ];
  const costData = SCENARIOS.map((s) => {
    const sv = savingsFor(s);
    return {
      name: `${SCENARIO_LABEL[s]} · ${pct(sv.timeSavedPct)} saved`,
      value: sv.costSavedPer100,
      fill: s === "base" ? OK : OK_SOFT,
      note: costBasis,
    };
  });
  const rejData = [
    { name: "Without SiteClaim", value: rej.beforePer100, fill: BAD, note: ASSUMPTIONS.rejectionRateBefore.basis },
    { name: "With SiteClaim", value: rej.afterPer100, fill: OK, note: ASSUMPTIONS.rejectionRateAfter.basis },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">The savings story</h1>
          <p className="mt-1.5 max-w-2xl text-sm text-ink-soft">
            What SiteClaim is worth per claim and per 100 claims. Every figure is driven by the stated assumptions
            below — adjustable, not measured — so the economics are auditable, not invented.
          </p>
        </div>
        <Button variant="ghost" onClick={onBack} className="shrink-0">
          ← Back to wizard
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat
          headline={pct(base.timeSavedPct)}
          label="QS time saved per claim"
          range={`${pct(bear.timeSavedPct)}–${pct(bull.timeSavedPct)} (bear–bull)`}
          basis={timeBasis}
        />
        <Stat
          headline={hkd(base.costSavedPerClaim)}
          label="Cost saved per claim"
          range={`${hkd(bear.costSavedPerClaim)}–${hkd(bull.costSavedPerClaim)} (bear–bull)`}
          basis={costBasis}
        />
        <Stat
          headline={`−${pct(rej.relativeReductionPct)}`}
          label="Technicality rejections"
          range={`${pct(ASSUMPTIONS.rejectionRateBefore.value)} → ${pct(ASSUMPTIONS.rejectionRateAfter.value)} of claims`}
          basis={`${ASSUMPTIONS.rejectionRateBefore.basis}\n\n${ASSUMPTIONS.rejectionRateAfter.basis}`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="QS time per claim (hours)" hint="Lower is better. Hover a bar for its assumption.">
          <HBars data={timeData} format={hours} height={120} />
        </ChartCard>
        <ChartCard title="Technicality rejections (per 100 claims)" hint="Claims lost to wrong party / bad service / missing particulars.">
          <HBars data={rejData} format={count} height={120} />
        </ChartCard>
        <ChartCard
          title="Cost saved per 100 claims (HK$)"
          hint="Bear / base / bull, from the time-saved range."
          className="lg:col-span-2"
        >
          <HBars data={costData} format={hkd} height={150} />
        </ChartCard>
      </div>

      <Card className="overflow-hidden">
        <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
          Base case — per claim vs per 100 claims
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line-soft text-left text-xs uppercase tracking-wide text-ink-faint">
              <th className="px-4 py-2 font-semibold">Metric</th>
              <th className="px-4 py-2 text-right font-semibold">Per claim</th>
              <th className="px-4 py-2 text-right font-semibold">Per 100 claims</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line-soft">
            <TableRow
              label="QS time saved"
              perClaim={hours(base.timeSavedHours)}
              per100={hours(base.timeSavedHours * 100)}
              basis={timeBasis}
            />
            <TableRow
              label="Cost saved"
              perClaim={hkd(base.costSavedPerClaim)}
              per100={hkd(base.costSavedPer100)}
              basis={costBasis}
            />
            <TableRow
              label="Technicality rejections avoided"
              perClaim={(rej.avoidedPer100 / 100).toFixed(2)}
              per100={count(rej.avoidedPer100)}
              basis={`${ASSUMPTIONS.rejectionRateBefore.basis}\n\n${ASSUMPTIONS.rejectionRateAfter.basis}`}
            />
          </tbody>
        </table>
      </Card>

      <Card className="overflow-hidden">
        <h2 className="border-b border-line-soft px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-soft">
          Assumptions — adjustable, not measured
        </h2>
        <ul className="divide-y divide-line-soft">
          <AssumptionRow name="QS hourly rate" value={hkd(ASSUMPTIONS.qsHourlyRateHkd.value)} basis={ASSUMPTIONS.qsHourlyRateHkd.basis} />
          <AssumptionRow name="Manual hours / claim" value={`${ASSUMPTIONS.manualHoursPerClaim.value} h`} basis={ASSUMPTIONS.manualHoursPerClaim.basis} />
          <AssumptionRow
            name="SiteClaim minutes / claim"
            value={`${ASSUMPTIONS.siteclaimMinutesPerClaim.value.bear} / ${ASSUMPTIONS.siteclaimMinutesPerClaim.value.base} / ${ASSUMPTIONS.siteclaimMinutesPerClaim.value.bull} min`}
            basis={ASSUMPTIONS.siteclaimMinutesPerClaim.basis}
          />
          <AssumptionRow name="Rejection rate — before" value={pct(ASSUMPTIONS.rejectionRateBefore.value)} basis={ASSUMPTIONS.rejectionRateBefore.basis} />
          <AssumptionRow name="Rejection rate — after" value={pct(ASSUMPTIONS.rejectionRateAfter.value)} basis={ASSUMPTIONS.rejectionRateAfter.basis} />
        </ul>
      </Card>

      <p className="text-xs text-ink-faint">
        Illustrative economics for decision-making, not a measured result. Time saved is shown as a bear / base / bull
        range precisely because it is an estimate.
      </p>
    </div>
  );
}

interface Row {
  name: string;
  value: number;
  fill: string;
  note: string;
}

function HBars({ data, format, height }: { data: Row[]; format: (n: number) => string; height: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 96, bottom: 4, left: 8 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 12, fill: INK }}
        />
        <Tooltip cursor={{ fill: "rgba(21,33,46,0.05)" }} content={<AssumptionTooltip format={format} />} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false} barSize={22}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.fill} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            formatter={(v: unknown) => format(Number(v))}
            style={{ fill: INK, fontSize: 12, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// recharts injects { active, payload }; `format` comes from the JSX above.
function AssumptionTooltip({ active, payload, format }: any) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as Row;
  return (
    <div className="max-w-xs rounded-lg border border-line bg-card p-3 text-xs shadow-lg">
      <div className="tabular font-semibold text-ink">
        {row.name}: {format(Number(payload[0].value))}
      </div>
      <div className="mt-1 whitespace-pre-line text-ink-soft">{row.note}</div>
    </div>
  );
}

function ChartCard({
  title,
  hint,
  className,
  children,
}: {
  title: string;
  hint: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Card className={className}>
      <div className="border-b border-line-soft px-4 py-2.5">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <p className="text-xs text-ink-faint">{hint}</p>
      </div>
      <div className="p-3">{children}</div>
    </Card>
  );
}

function Stat({ headline, label, range, basis }: { headline: string; label: string; range: string; basis: string }) {
  return (
    <Card className="p-4">
      <div className="tabular text-3xl font-bold text-ink">{headline}</div>
      <div className="mt-0.5 text-sm font-medium text-ink">
        {label}
        <InfoDot title={basis} />
      </div>
      <div className="tabular mt-1 text-xs text-ink-faint">{range}</div>
    </Card>
  );
}

function TableRow({ label, perClaim, per100, basis }: { label: string; perClaim: string; per100: string; basis: string }) {
  return (
    <tr>
      <td className="px-4 py-2.5 text-ink">
        {label}
        <InfoDot title={basis} />
      </td>
      <td className="tabular px-4 py-2.5 text-right text-ink" title={basis}>
        {perClaim}
      </td>
      <td className="tabular px-4 py-2.5 text-right font-semibold text-ink" title={basis}>
        {per100}
      </td>
    </tr>
  );
}

function AssumptionRow({ name, value, basis }: { name: string; value: string; basis: string }) {
  return (
    <li className="flex items-start justify-between gap-4 px-4 py-2.5">
      <div>
        <div className="text-sm font-medium text-ink">{name}</div>
        <div className="text-xs text-ink-faint">{basis}</div>
      </div>
      <div className="tabular shrink-0 text-sm font-semibold text-ink">{value}</div>
    </li>
  );
}
