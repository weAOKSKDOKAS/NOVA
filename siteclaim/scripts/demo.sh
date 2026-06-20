#!/usr/bin/env bash
# One-command offline demo: FastAPI backend (DEMO_MODE) + Vite frontend, both
# local, zero network. Ctrl-C stops both.
set -euo pipefail

cd "$(dirname "$0")/.."   # -> siteclaim/
ROOT="$(pwd)"
export DEMO_MODE=true

echo "→ SiteClaim demo (DEMO_MODE=true, offline)"
echo "→ starting backend on http://localhost:8000 …"
( cd "$ROOT/backend" && exec uvicorn api:app --port 8000 ) &
BACKEND_PID=$!
trap 'echo; echo "→ stopping…"; kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  echo "→ installing frontend deps (first run)…"
  npm install
fi

echo "→ starting frontend on http://localhost:5173 …"
echo "→ open http://localhost:5173 and load a demo case (clean / messy / gotcha)"
npm run dev
