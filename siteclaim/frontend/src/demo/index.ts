// Pre-recorded pipeline results bundled into the app, so a demo never hard-crashes
// even if the backend is unreachable. Regenerate with:
//   cd backend && python fixtures/build_demo_snapshots.py
import type { Snapshot } from "../types";
import clean from "./clean.json";
import gotcha from "./gotcha.json";
import messy from "./messy.json";

export const SNAPSHOTS: Record<string, Snapshot> = {
  clean: clean as unknown as Snapshot,
  messy: messy as unknown as Snapshot,
  gotcha: gotcha as unknown as Snapshot,
};
