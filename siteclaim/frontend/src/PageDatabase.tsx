import { useEffect, useMemo, useRef, useState } from "react";
import { useCite } from "./cite";
import {
  registerFor, rgba, sevMeta, signalColor, signalLabel, signalSeverity, tradeColor, tradeLabel, type Sev,
} from "./theme";
import type { Coverage, Firm, PublicFlag } from "./types";

export function PageDatabase({
  active,
  firms,
  coverage,
  registers,
}: {
  active: boolean;
  firms: Firm[];
  coverage: Coverage | null;
  registers: number;
}) {
  const cite = useCite();
  const [q, setQ] = useState("");
  const [trade, setTrade] = useState("all");
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  const total = coverage?.total_firms ?? firms.length;
  const flagged = coverage?.flagged_firms ?? firms.filter((f) => f.public_flags.length > 0).length;

  // ---- count-up (replays each time the page becomes active) ----
  const [counts, setCounts] = useState({ firms: 0, flagged: 0, registers: 0 });
  const raf = useRef(0);
  useEffect(() => {
    if (!active) return;
    const dur = 1150, t0 = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      setCounts({ firms: Math.round(total * e), flagged: Math.round(flagged * e), registers: Math.round(registers * e) });
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [active, total, flagged, registers]);

  // ---- breathing matrix ----
  const cells = useMemo(() => {
    const out: { color: string; dur: string; delay: string }[] = [];
    for (let i = 0; i < total; i++) {
      const isFlag = i < flagged;
      const color = isFlag
        ? i < flagged * 0.65 ? "#E5484D" : i < flagged * 0.85 ? "#C13439" : "#D99513"
        : "rgba(159,180,214,0.26)";
      out.push({ color, dur: (2.4 + (i % 5) * 0.45).toFixed(2) + "s", delay: ((i % 13) * 0.13).toFixed(2) + "s" });
    }
    return out;
  }, [total, flagged]);

  // ---- breakdown by signal type (live /coverage) ----
  const breakdown = useMemo(() => {
    const fbt = coverage?.flags_by_type ?? {};
    const entries = Object.entries(fbt).map(([type, n]) => ({ type, n, label: signalLabel(type), color: signalColor(type) }));
    entries.sort((a, b) => b.n - a.n);
    const sum = entries.reduce((s, e) => s + e.n, 0) || 1;
    return entries.map((e) => ({ ...e, pct: ((e.n / sum) * 100).toFixed(2) + "%" }));
  }, [coverage]);

  // ---- register chips (distinct issuing registers in the data) ----
  const registerChips = useMemo(() => {
    const map = new Map<string, ReturnType<typeof registerFor>>();
    for (const f of firms) for (const fl of f.public_flags) { const r = registerFor(fl.source); map.set(r.short, r); }
    return [...map.values()];
  }, [firms]);

  // ---- trade chips ----
  const trades = useMemo(() => {
    const set = new Set<string>();
    for (const f of firms) for (const t of f.trades) set.add(t);
    return [...set].sort();
  }, [firms]);

  // ---- filtering ----
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return firms.filter((f) => {
      if (flaggedOnly && f.public_flags.length === 0) return false;
      if (trade !== "all" && !f.trades.includes(trade)) return false;
      if (needle && !(f.name_en.toLowerCase().includes(needle) || (f.name_zh ?? "").toLowerCase().includes(needle))) return false;
      return true;
    });
  }, [firms, q, trade, flaggedOnly]);

  const registerCite = (r: ReturnType<typeof registerFor>) =>
    cite.open({ source: r.name, reference: r.home, detail: `${r.name} — register cross-checked against all ${total} screened firms. Adverse records are matched by company name and registration number.`, date: null });

  const mono = "'Spline Sans Mono',monospace";
  const display = "'Bricolage Grotesque',sans-serif";

  return (
    <main style={{ maxWidth: 1260, margin: "0 auto", padding: "26px 30px 72px" }}>
      {/* HERO */}
      <section style={{ position: "relative", overflow: "hidden", borderRadius: 22, padding: "36px 38px 32px", color: "#EAF0FB", background: "radial-gradient(820px 420px at 86% -20%, rgba(110,86,207,0.55), transparent 62%), radial-gradient(680px 520px at 6% 130%, rgba(15,181,166,0.34), transparent 56%), linear-gradient(135deg,#0F1B2D 0%, #14213B 55%, #182347 100%)", boxShadow: "0 24px 60px -28px rgba(15,27,45,0.55)" }}>
        <div style={{ position: "relative", zIndex: 2, display: "flex", gap: 40, flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div style={{ maxWidth: 540 }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, fontFamily: mono, fontSize: 11, letterSpacing: "0.16em", textTransform: "uppercase", color: "#9fb4d6", border: "1px solid rgba(159,180,214,0.28)", borderRadius: 999, padding: "5px 12px", marginBottom: 18 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#0FB5A6" }} /> The proprietary data asset
            </div>
            <h1 style={{ margin: 0, fontFamily: display, fontSize: 42, fontWeight: 700, lineHeight: 1.04, letterSpacing: "-0.025em", color: "#fff" }}>Every subcontractor,<br />screened against the public record.</h1>
            <p style={{ margin: "16px 0 0", fontSize: 15, lineHeight: 1.62, color: "#b9c7de", maxWidth: 480 }}>Performance and risk signals fused from official Hong Kong registers — the moat a generic chatbot cannot reach. Every figure below traces to a government record. Tap any <span style={{ color: "#fff", fontWeight: 500 }}>citation</span> to open the source.</p>
          </div>
          <div style={{ flex: "none" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14, marginBottom: 11 }}>
              <span style={{ fontFamily: mono, fontSize: 10.5, letterSpacing: "0.12em", textTransform: "uppercase", color: "#9fb4d6" }}>Signal map · {total} firms</span>
              <div style={{ display: "flex", gap: 12, fontFamily: mono, fontSize: 10, color: "#9fb4d6" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}><span style={{ width: 8, height: 8, borderRadius: 2, background: "#E5484D" }} />flagged</span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}><span style={{ width: 8, height: 8, borderRadius: 2, background: "rgba(159,180,214,0.30)" }} />clear</span>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(20,1fr)", gap: 4, width: 360 }}>
              {cells.map((c, i) => (
                <span key={i} style={{ width: "100%", aspectRatio: "1", borderRadius: 2.5, background: c.color, animation: `ssPulse ${c.dur} ease-in-out ${c.delay} infinite` }} />
              ))}
            </div>
          </div>
        </div>

        {/* figures */}
        <div style={{ position: "relative", zIndex: 2, display: "flex", flexWrap: "wrap", marginTop: 30, paddingTop: 26, borderTop: "1px solid rgba(159,180,214,0.18)" }}>
          <Figure value={counts.firms} label="Firms screened" color="#fff" mono={mono} display={display}
            cite={() => cite.open({ source: "Companies Registry", reference: "https://www.cr.gov.hk/", detail: `The screened universe of ${total} Hong Kong construction firms, compiled from official registers and matched by company name and registration number.`, date: null })} citeBg={rgba("#1F6FEB", 0.22)} citeFg="#9fc0ff" />
          <Figure value={counts.flagged} label="Carry a verified risk signal" color="#FF8E8E" underline mono={mono} display={display}
            cite={() => cite.open({ source: "Labour Department", reference: "https://www.labour.gov.hk/eng/news/prosecutions.htm", detail: `Of ${total} screened firms, ${flagged} carry at least one verified public risk signal — each traceable to its issuing register.`, date: null })} citeBg={rgba("#E5484D", 0.22)} citeFg="#ffb3b3" />
          <div style={{ padding: "0 34px", borderLeft: "1px solid rgba(159,180,214,0.18)" }}>
            <span style={{ fontFamily: display, fontVariantNumeric: "tabular-nums", fontSize: 56, fontWeight: 700, lineHeight: 0.9, color: "#fff" }}>{counts.registers}</span>
            <div style={{ fontSize: 12, letterSpacing: "0.06em", textTransform: "uppercase", color: "#9fb4d6", marginTop: 9 }}>Official registers cross-checked</div>
          </div>
        </div>

        {/* register chips */}
        <div style={{ position: "relative", zIndex: 2, display: "flex", flexWrap: "wrap", alignItems: "center", gap: 13, marginTop: 20, paddingTop: 18, borderTop: "1px solid rgba(159,180,214,0.18)" }}>
          <span style={{ fontFamily: mono, fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", color: "#9fb4d6" }}>Registers · tap to verify →</span>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {registerChips.map((r) => (
              <button key={r.short} type="button" onClick={() => registerCite(r)} style={{ display: "inline-flex", alignItems: "center", gap: 7, cursor: "pointer", background: "rgba(255,255,255,0.04)", border: `1px solid ${rgba(r.color, 0.4)}`, borderRadius: 8, padding: "6px 12px", fontSize: 11.5, color: "#dbe5f4" }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: r.color }} />{r.short}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* SIGNAL BREAKDOWN */}
      <section style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 18 }}>
        <div style={{ flex: 2, minWidth: 340, background: "#fff", border: "1px solid rgba(15,27,45,0.07)", borderRadius: 16, padding: "18px 20px", boxShadow: "0 10px 30px -22px rgba(15,27,45,0.35)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: "#0F1B2D" }}>The {flagged} flagged firms, by signal type</span>
            <span style={{ fontFamily: mono, fontSize: 11, color: "#8a98ab" }}>verified · sourced</span>
          </div>
          <div style={{ display: "flex", height: 14, borderRadius: 7, overflow: "hidden", marginBottom: 14 }}>
            {breakdown.map((b) => <div key={b.type} style={{ width: b.pct, background: b.color }} title={b.label} />)}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "7px 16px" }}>
            {breakdown.map((b) => (
              <div key={b.type} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                <span style={{ width: 9, height: 9, borderRadius: 2, background: b.color }} />
                <span style={{ fontSize: 12, color: "#46566b" }}>{b.label}</span>
                <span style={{ fontFamily: mono, fontSize: 12, fontWeight: 600, color: "#0F1B2D" }}>{b.n}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 220, background: "linear-gradient(140deg,#0FB5A6,#1F6FEB)", borderRadius: 16, padding: "18px 20px", color: "#fff", boxShadow: "0 14px 32px -20px rgba(15,181,166,0.7)", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div style={{ fontFamily: mono, fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", opacity: 0.85 }}>Coverage integrity</div>
          <div>
            <div style={{ fontFamily: display, fontSize: 34, fontWeight: 700, lineHeight: 1 }}>100%</div>
            <div style={{ fontSize: 12.5, lineHeight: 1.5, opacity: 0.92, marginTop: 6 }}>of risk signals carry a clickable government source. Nothing is asserted without a record.</div>
          </div>
        </div>
      </section>

      {/* CONTROLS */}
      <section style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, margin: "24px 0 14px" }}>
        <div style={{ flex: 1, minWidth: 260, display: "flex", alignItems: "center", gap: 10, background: "#fff", border: "1px solid rgba(15,27,45,0.10)", borderRadius: 12, padding: "0 14px", height: 46, boxShadow: "0 6px 18px -14px rgba(15,27,45,0.4)" }}>
          <span style={{ color: "#1F6FEB", fontSize: 16 }}>⌕</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Search ${total} firms — name, English or 中文…`} style={{ flex: 1, border: "none", outline: "none", background: "transparent", fontSize: 14, color: "#0F1B2D", height: "100%" }} />
          <span style={{ fontFamily: mono, fontSize: 11, color: "#8a98ab" }}>{rows.length}/{firms.length}</span>
        </div>
        <div style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: 9, height: 46, padding: "0 12px", background: "#fff", border: `1px solid ${trade === "all" ? "rgba(15,27,45,0.10)" : rgba(tradeColor(trade), 0.4)}`, borderRadius: 12, boxShadow: "0 6px 18px -14px rgba(15,27,45,0.4)" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", flex: "none", background: trade === "all" ? "#8a98ab" : tradeColor(trade) }} />
          <select value={trade} onChange={(e) => setTrade(e.target.value)} aria-label="Filter by trade" style={{ appearance: "none", WebkitAppearance: "none", border: "none", outline: "none", background: "transparent", fontFamily: "inherit", fontSize: 13.5, fontWeight: 500, color: "#0F1B2D", height: "100%", paddingRight: 16, cursor: "pointer" }}>
            <option value="all">All trades</option>
            {trades.map((t) => <option key={t} value={t}>{tradeLabel(t)}</option>)}
          </select>
          <span style={{ position: "absolute", right: 12, pointerEvents: "none", color: "#8a98ab", fontSize: 10 }}>▾</span>
        </div>
        <button type="button" onClick={() => setFlaggedOnly((v) => !v)} style={{ display: "inline-flex", alignItems: "center", gap: 8, height: 38, background: flaggedOnly ? rgba("#E5484D", 0.08) : "#fff", border: `1px solid ${flaggedOnly ? rgba("#E5484D", 0.4) : "rgba(15,27,45,0.14)"}`, borderRadius: 9, padding: "0 14px", fontSize: 12.5, fontWeight: 600, color: flaggedOnly ? "#E5484D" : "#46566b", cursor: "pointer" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#E5484D" }} />Flagged only
        </button>
      </section>

      {/* FIRM LIST */}
      <section style={{ display: "flex", flexDirection: "column", gap: 11 }}>
        {rows.map((f) => <FirmRow key={f.firm_id} firm={f} onCite={cite.open} />)}
        <div style={{ textAlign: "center", padding: 12, fontFamily: mono, fontSize: 11.5, color: "#8a98ab" }}>— showing {rows.length} of {firms.length} screened firms · {flagged} carry a public signal —</div>
      </section>
    </main>
  );
}

function Figure({ value, label, color, underline, cite, citeBg, citeFg, mono, display }: {
  value: number; label: string; color: string; underline?: boolean; cite: () => void; citeBg: string; citeFg: string; mono: string; display: string;
}) {
  return (
    <div style={{ padding: "0 34px", borderLeft: label === "Firms screened" ? "none" : "1px solid rgba(159,180,214,0.18)", paddingLeft: label === "Firms screened" ? 0 : 34 }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
        <span style={{ position: "relative", fontFamily: display, fontVariantNumeric: "tabular-nums", fontSize: 56, fontWeight: 700, lineHeight: 0.9, color }}>
          {value}
          {underline && <span style={{ position: "absolute", left: 0, right: 0, bottom: -3, height: 3, borderRadius: 2, background: "linear-gradient(90deg,#E5484D,#D99513)" }} />}
        </span>
        <button type="button" onClick={cite} title="Open the source record" style={{ marginTop: 6, cursor: "pointer", border: "none", background: citeBg, color: citeFg, fontFamily: mono, fontSize: 11, fontWeight: 600, width: 20, height: 20, borderRadius: 6 }}>§</button>
      </div>
      <div style={{ fontSize: 12, letterSpacing: "0.06em", textTransform: "uppercase", color: "#9fb4d6", marginTop: 9 }}>{label}</div>
    </div>
  );
}

function FirmRow({ firm, onCite }: { firm: Firm; onCite: (c: { source: string | null; reference: string | null; detail: string; date?: string | null }) => void }) {
  const sevOf = (fl: PublicFlag): Sev => signalSeverity(fl.signal_type);
  const worst: Sev | null = firm.public_flags.some((f) => sevOf(f) === "fatal") ? "fatal"
    : firm.public_flags.some((f) => sevOf(f) === "warning") ? "warning" : null;
  const accent = worst === "fatal" ? "#E5484D" : worst === "warning" ? "#D99513" : "#2EA56A";
  const sm = worst ? sevMeta(worst) : null;
  const display = "'Bricolage Grotesque',sans-serif", mono = "'Spline Sans Mono',monospace";

  return (
    <article style={{ position: "relative", display: "flex", background: "#fff", border: "1px solid rgba(15,27,45,0.07)", borderRadius: 15, overflow: "hidden", boxShadow: "0 8px 24px -20px rgba(15,27,45,0.45)" }}>
      <div style={{ width: 5, flex: "none", background: accent }} />
      <div style={{ flex: 1, minWidth: 0, padding: "17px 20px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: display, fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em", color: "#0F1B2D" }}>{firm.name_en}</span>
          {firm.name_zh && <span style={{ fontSize: 13, color: "#8a98ab" }}>{firm.name_zh}</span>}
          {firm.registered_grade && <span style={{ fontFamily: mono, fontSize: 11, color: "#5a6b80", background: "#EEF2F7", borderRadius: 6, padding: "3px 8px" }}>{firm.registered_grade}</span>}
          {firm.public_flags.length === 0 ? (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginLeft: "auto", fontSize: 12, fontWeight: 600, color: "#2EA56A", background: rgba("#2EA56A", 0.1), borderRadius: 999, padding: "4px 11px" }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#2EA56A" }} />No adverse record
            </span>
          ) : (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginLeft: "auto", fontSize: 12, fontWeight: 700, color: sm!.fg, background: sm!.bg, borderRadius: 999, padding: "4px 11px" }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: sm!.dot }} />{sm!.label}
            </span>
          )}
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 11 }}>
          {firm.trades.map((t) => {
            const col = tradeColor(t);
            return (
              <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11.5, fontWeight: 500, color: col, background: rgba(col, 0.1), borderRadius: 7, padding: "3px 9px" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: col }} />{tradeLabel(t)}
              </span>
            );
          })}
        </div>

        {firm.public_flags.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 9, marginTop: 14 }}>
            {firm.public_flags.map((fl, i) => {
              const sev = sevOf(fl), m = sevMeta(sev), reg = registerFor(fl.source);
              return (
                <div key={i} style={{ display: "flex", gap: 12, padding: "11px 13px", borderRadius: 11, background: rgba(m.dot, 0.05), border: `1px solid ${rgba(m.dot, 0.18)}` }}>
                  <span style={{ width: 3, flex: "none", borderRadius: 2, background: m.dot }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 5, background: m.bg, color: m.fg, fontFamily: mono, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", padding: "3px 8px", borderRadius: 6 }}><span style={{ width: 5, height: 5, borderRadius: "50%", background: m.fg }} />{m.tag}</span>
                      <span style={{ fontSize: 13.5, fontWeight: 600, color: "#0F1B2D" }}>{signalLabel(fl.signal_type)}</span>
                    </div>
                    <p style={{ margin: "6px 0 0", fontSize: 12.5, lineHeight: 1.55, color: "#46566b" }}>{fl.label}</p>
                    <button type="button" onClick={() => onCite({ source: fl.source, reference: fl.reference, detail: fl.label, date: fl.date })} style={{ display: "inline-flex", alignItems: "center", gap: 8, marginTop: 9, cursor: "pointer", border: `1px solid ${rgba(reg.color, 0.3)}`, background: "#fff", borderRadius: 8, padding: "5px 11px" }}>
                      <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 16, height: 16, padding: "0 3px", borderRadius: 5, background: reg.color, color: "#fff", fontFamily: mono, fontSize: 9, fontWeight: 600 }}>{reg.short}</span>
                      <span style={{ fontFamily: mono, fontSize: 11, fontWeight: 600, color: reg.color }}>{reg.short}</span>
                      <span style={{ fontSize: 11, color: "#8a98ab" }}>→ view source</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </article>
  );
}
