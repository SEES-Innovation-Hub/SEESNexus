# SEES Nexus

FastAPI + React rebuild of the SEES departmental platform.

## Layout

- `backend/` — FastAPI service, Alembic migrations, test suite. See
  [backend/README.md](backend/README.md) for setup and local dev.
- `frontend/` — not in this repo yet.

CI for the backend runs from `.github/workflows/backend-ci.yml` and is scoped to
changes under `backend/`.
