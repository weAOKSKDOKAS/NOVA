# SiteClaim — developer shortcuts.
.PHONY: demo install test snapshots build-frontend

# One-command offline demo: backend (DEMO_MODE) + frontend, both local.
demo:
	./scripts/demo.sh

# Install backend + frontend dependencies.
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Backend test suite (offline).
test:
	cd backend && python -m pytest -q

# Type-check + build the frontend.
build-frontend:
	cd frontend && npm run build

# Regenerate the frontend's offline demo snapshots from the pipeline.
snapshots:
	cd backend && python fixtures/build_demo_snapshots.py
