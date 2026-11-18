# SEES Nexus

The digital platform of the Society of Electrical, Electronics and Computer
Engineering Students (SEES), University of Lagos: projects, hardware lending,
events and news in one place.

| | |
|---|---|
| `backend/` | FastAPI + async SQLAlchemy + PostgreSQL, Alembic migrations, pytest suite. [backend/README.md](backend/README.md) |
| `frontend/` | React + Vite + Tailwind single-page app. [frontend/README.md](frontend/README.md) |

## Run it locally

```bash
# backend (SQLite, no setup)
cd backend && pip install -r requirements.txt
python seed.py                    # admin@seesnexus.dev / student@seesnexus.dev, password ChangeMe123
uvicorn app.main:app --reload     # http://localhost:8000/docs

# frontend, in another terminal
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## Deploy

- **Backend (Render):** `DATABASE_URL` (Render's `postgres://` URL works as is),
  a private `SECRET_KEY` (the app refuses to start against Postgres without one),
  `ADMIN_REGISTRATION_KEY` (shared only with people who should become admins),
  `CORS_ORIGINS` set to the frontend's origin, `BREVO_API_KEY` and a verified
  `BREVO_SENDER_EMAIL`, `OTP_DEBUG_RETURN_CODE=false`, and the `CLOUDINARY_*`
  keys. Run `alembic upgrade head` on each deploy.
- **Frontend (Vercel):** `VITE_API_URL` set to the backend's origin.

## CI

- `backend-ci.yml`: ruff, Alembic round-trip on Postgres, tests.
- `frontend-ci.yml`: type check, lint, build.
- `repo-guard.yml`: blocks committed `.env` files, code hidden far to the right
  of a line, and build configuration that downloads or evaluates code — the
  techniques used in the November 2026 compromise of the old `master` branch.

The default branch is `main`.
