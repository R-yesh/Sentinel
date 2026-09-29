# Sentinel web workspace

React + TypeScript with Vite. Phase 4 adds a population command center alongside
the dataset workspace and Phase 3's synchronous investigations, inspectable
seven-agent workflow, and engineering reliability disposition. All analytical
results come from Sentinel.

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

Open http://127.0.0.1:5173. The default route is `/overview`. Browsing does not
make Gemini calls or run the ML model. The Python environment still needs the
existing API dependencies installed to import the backend.

## Population command center (Phase 4)

Overview now consumes `GET /api/v1/datasets/synthetic-burnin/population` through
the existing API client. It displays population/lot counts, screening candidates,
significant early drift, high-side lot evidence, no-signal and unassessed counts.
No final PASS/REVIEW/REJECT counts are manufactured.

The server defines a candidate as significant early drift OR high-side
non-TYPICAL lot evidence, using existing Sentinel utilities and thresholds.
The UI only formats values and filters the complete returned population. Its
15-row table pagination is over that complete response, not a partial dataset
page. Sorting by number of reasons is evidence triage, not a risk score.

Charts show the backend's percentage-change histogram and each lot's
candidate/total count. Hover or keyboard-focus histogram bars for exact ranges;
select a lot bar to filter the component table. Conventional overlap is shown
only when the optional server reference is configured (see `../api/README.md`).
No numerical conventional default or threshold-editing UI is included.

`Investigate` calls the existing Phase 3 session action and navigates directly
to the existing Analysis workspace. Dashboard loading does not execute agents,
fit models, or call Gemini. IF/RF context remains available in investigations.
Synthetic training labels and future measurements never enter the dashboard.

Added modules: `src/api/population.ts` and `src/features/population/` (charts,
comparison, component table, styling). Overview reuses the existing shell,
resource/error handling, request layer, and investigation session.

## Evaluation / Why Sentinel? (Phase 4.5)

`/evaluation` is a separate navigation destination. It consumes only the
dedicated `/api/v1/datasets/synthetic-burnin/evaluation` endpoint. An evaluation
banner and tinted hindsight columns distinguish synthetic `defect_type` and
future 96h/168h observations from the early operational inputs. Overview remains
unchanged and stays the default route.

The page includes coverage counts/rates, class-level flag-rate bars, four signal
overlap buckets, optional configured conventional comparison, and a searchable,
paginated retrospective table defaulting to unflagged synthetic defects.
Comparison-group and class filters reveal misses as well as successes. Unknown
labels/incomplete screening remain explicitly excluded; missing future values
are unavailable. No generic accuracy or real-world performance claim is made.

Investigate invokes the existing Phase 3 session with an explicit early-input
allowlist and sends only dataset/component IDs to the investigation API. No
hindsight is passed into investigation state. No Gemini calls occur on evaluation
page loading. Conventional configuration remains server-side and unset by default.

Modules: `api/evaluation.ts`, `pages/EvaluationPage.tsx`, and
`features/evaluation/` (coverage, comparison, table, styles). Focused frontend
tests verify the boundary and Overview/Analysis navigation.

## API connection configuration

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
- `POST /api/v1/investigations` with `{ "dataset_id": "synthetic-burnin", "component_id": "C0001" }`

The single dataset ID is the one supported by Phase 1, not a fabricated display
dataset. Search is submitted using Enter or the Search button and is executed by
the backend. Both component and lot IDs are searchable. Pagination is server-side.
An additional unfiltered one-item request provides the dataset's total count;
filtered totals are shown separately. Health indicates API reachability only,
not model readiness or LLM availability.

Search, page size, page, and selected component are encoded in URL parameters.
Selecting a row fetches its current observations from the detail endpoint.
`Analyze with Sentinel` starts one POST and navigates to
`/analysis?dataset=...&component=...`. The API constructs context and executes the
unchanged orchestrator. Gemini credentials and the model artifact must already
be configured on the server (see `../api/README.md`). No credentials reach the UI.

Execution starts in an event handler, not a mount effect, preventing duplicate
requests under React StrictMode. Direct analysis links and reloads require an
explicit Run action. The current request/result remains in tab memory across
route navigation, but is lost on reload. A new selection replaces that client
session; late results from an older request cannot overwrite the new component.
Leaving the page does not cancel backend execution. The client waits up to ten
minutes; retry explicitly starts a new investigation, not a persisted job lookup.

The loading screen shows one request state: the API has no per-agent progress.
After a response, a labeled 1.8-second presentation replay highlights the workflow
and findings accumulated in the shared state. Drift and Lot branch together and
converge into Latent Defect. Results and inspection are immediately available;
Skip/Replay controls and reduced-motion support avoid mandatory animation.

Select any agent with returned evidence to inspect structured metrics, findings,
severity, evidence, and metadata. Raw agent output and the full response remain
collapsible for audit. The final decision comes only from `final_decision`;
`needs_review` without a decision is an early stop, not a fabricated REVIEW.
Invalid response identities/envelopes fail visibly; partial evidence produces
completeness notes and unavailable values rather than inferred analysis.

The dataset browser presents only identity, lot ID, observed 0h/24h leakage, and API counts.
Leakage is formatted to four decimal places in µA; the backend retains source
precision. Missing/non-finite display values appear as unavailable, not zero.
The investigation separates those observed inputs from returned forecasts,
uncertainty, anomaly measures, provisional assessments, and final decisions.
API non-finite statistics retain their meaning (∞/−∞/undefined), never zero.
No training labels, future observations, or analytical calculations are bundled
or reproduced in the frontend. Percentile fractions are formatted as percentages.

## Structure

- `src/api/client.ts`: API types, request/error/timeout handling, endpoint methods.
- `src/api/investigation.ts`: workflow types and response-boundary validation.
- `src/hooks/useResource.ts`: abortable resource loading, retry, stale-response protection.
- `src/components/`: application shell, API health, shared loading/error states.
- `src/features/dataset/`: Dataset Workspace and component preview.
- `src/features/investigation/`: session, workspace, observed context, workflow graph,
  agent inspector, disposition, readable evidence primitives, and workspace styles.
- `src/pages/`: Overview and route selection for Analysis.
- `src/styles.css`: design tokens, semantic colors, responsive layout, reduced-motion support.
- `src/test/`: focused interaction tests using API fixtures; no external services required.

React Router preserves the existing shell and dataset navigation.
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
