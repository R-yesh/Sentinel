# Sentinel web workspace

Phase 2 is a React + TypeScript frontend built with Vite. It provides a dataset
workspace, component previews, overview/navigation, and an analysis placeholder.
It does **not** execute investigations or generate analytical results.

## Run locally

Use Node.js 22.12+ (verified with 22.20.0). In a PowerShell terminal, start the
existing FastAPI service **from the repository root**:

```powershell
cd C:\Users\aarye\Desktop\Sentinel
apps/api/.venv/Scripts/python.exe -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd C:\Users\aarye\Desktop\Sentinel\apps\web
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. The default route is `/dataset`. Browsing does not
make Gemini calls or run the ML model. The Python environment still needs the
existing API dependencies installed to import the backend.

## Configuration

Defaults work without an environment file. Copy `.env.example` to `.env.local`
only if overriding them:

- `API_PROXY_TARGET`: FastAPI origin for Vite's development/preview proxy;
  defaults to `http://127.0.0.1:8000`.
- `VITE_API_BASE_URL`: browser-visible API origin; defaults to empty (same-origin).
  An absolute cross-origin URL requires that deployment's CORS configuration.
  Prefer the default local proxy; no backend CORS change is needed.

The proxy forwards `/api` and `/health`. These settings do not contain secrets.
Never put Gemini credentials in a `VITE_` variable. Vite variables are public
and become part of the browser bundle. Restart Vite after configuration changes.

## API contract

- `GET /api/v1/datasets/synthetic-burnin/components?search=...&page=...&page_size=...`
- `GET /api/v1/datasets/synthetic-burnin/components/{component_id}`
- `GET /health`

The single dataset ID is the one supported by Phase 1, not a fabricated display
dataset. Search is submitted using Enter or the Search button and is executed by
the backend. Both component and lot IDs are searchable. Pagination is server-side.
An additional unfiltered one-item request provides the dataset's total count;
filtered totals are shown separately. Health indicates API reachability only,
not model readiness or LLM availability.

Search, page size, page, and selected component are encoded in URL parameters.
Selecting a row fetches its current observations from the detail endpoint.
`Analyze with Sentinel` navigates to `/analysis?dataset=...&component=...` without
calling the investigation API. The placeholder explicitly says execution has not
started. Browser back/forward and direct selection links are supported.

Only identity, lot ID, observed 0h/24h leakage, and API counts are presented.
Leakage is formatted to four decimal places in µA; the backend retains source
precision. Missing/non-finite display values appear as unavailable, not zero.
No training labels, future observations, predictions, classifications, anomaly
measures, or fabricated results are computed or bundled in the frontend.

## Structure

- `src/api/client.ts`: API types, request/error/timeout handling, endpoint methods.
- `src/hooks/useResource.ts`: abortable resource loading, retry, stale-response protection.
- `src/components/`: application shell, API health, shared loading/error states.
- `src/features/dataset/`: Dataset Workspace and component preview.
- `src/pages/`: Overview and Analysis placeholder.
- `src/styles.css`: design tokens, semantic colors, responsive layout, reduced-motion support.
- `src/test/`: focused interaction tests using API fixtures; no external services required.

React Router provides route/state foundations for later investigation screens.
Fonts are bundled locally. The design uses native tables, accessible controls,
keyboard selection, and a collapsible narrow-screen navigation. On narrower
screens the detail panel moves below the table; the table scrolls horizontally.

## Validation and build

```powershell
npm.cmd run test
npm.cmd run typecheck
npm.cmd run build
npm.cmd run preview
```

The production bundle is written to `dist/`. Preview uses port 4173 and the same
local API proxy. For future static hosting, configure SPA fallback to `index.html`
and same-origin proxy routes for `/api` and `/health`; Vite configuration itself
does not install a production reverse proxy.
