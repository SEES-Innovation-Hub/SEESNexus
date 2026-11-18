# SEES Nexus — frontend

React 19 + TypeScript + Vite + Tailwind CSS v4, with TanStack Query and React Router.

```bash
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend on :8000
```

Before sharing work, all three must pass (CI runs them too):

```bash
npx tsc -b && npx oxlint && npm run build
```

**Deploying (Vercel):** set `VITE_API_URL` to the backend's origin, e.g.
`https://seesnexus.onrender.com` (see `.env.example`). `vercel.json` sends every
path to `index.html` so deep links like `/events/123` load on refresh.

How the code is organised, and why: [docs/CODE_GUIDE.md](docs/CODE_GUIDE.md).
