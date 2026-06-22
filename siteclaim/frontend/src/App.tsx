import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { Header, type Page } from "./components";
import { CiteProvider } from "./cite";
import { registerFor } from "./theme";
import type { Coverage, DemoCaseSummary, Firm } from "./types";
import { PageDatabase } from "./PageDatabase";
import { PageSourcing } from "./PageSourcing";

export default function App() {
  const [page, setPage] = useState<Page>("database");

  // Shared meta, fetched once and passed down (offline in DEMO_MODE).
  const [demoMode, setDemoMode] = useState(true);
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [firms, setFirms] = useState<Firm[]>([]);
  const [demoCases, setDemoCases] = useState<DemoCaseSummary[]>([]);

  useEffect(() => {
    api.health().then((h) => setDemoMode(h.demo_mode)).catch(() => {});
    api.coverage().then(setCoverage).catch(() => {});
    api.firms().then(setFirms).catch(() => {});
    api.demoCases().then(setDemoCases).catch(() => {});
  }, []);

  // Distinct issuing registers across the live firm data (header + hero figure).
  const registers = useMemo(() => {
    const set = new Set<string>();
    for (const f of firms) for (const fl of f.public_flags) set.add(registerFor(fl.source).short);
    return set.size || 4;
  }, [firms]);

  return (
    <CiteProvider>
      <div style={{ minHeight: "100vh", background: "radial-gradient(1100px 520px at 88% -8%, rgba(110,86,207,0.10), transparent 60%), radial-gradient(900px 480px at -5% 8%, rgba(15,181,166,0.09), transparent 55%), #EEF2F7" }}>
        <Header page={page} onNavigate={setPage} registers={registers} />
        <div style={{ display: page === "database" ? "block" : "none" }}>
          <PageDatabase active={page === "database"} firms={firms} coverage={coverage} registers={registers} />
        </div>
        <div style={{ display: page === "sourcing" ? "block" : "none" }}>
          <PageSourcing demoMode={demoMode} demoCases={demoCases} coverage={coverage} />
        </div>
      </div>
    </CiteProvider>
  );
}
