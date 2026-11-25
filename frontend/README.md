# StockFlow frontend

React 19 + TypeScript + Vite single-page app for the StockFlow API. See the
[main README](../README.md) for the whole project.

```bash
npm ci
npm run dev            # http://localhost:5173, /api is proxied to http://127.0.0.1:8000
npm run lint           # ESLint
npm run format:check   # Prettier (npm run format to fix)
npm run build          # type-check and build into dist/
```

The app calls the API at `/api` on its own origin. In production the build is
served by Django (see the root `Dockerfile`). For a separate deployment set
`VITE_API_URL` at build time (see `.env.example`).
