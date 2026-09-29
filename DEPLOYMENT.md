# Sentinel demonstration deployment

## Architecture

- Vercel: static React/Vite build, project root `apps/web`, Node 22.x.
- Render: native Python web service, repository root, Python 3.12.10.
- Browser calls the Render HTTPS origin directly. No Vercel API rewrite/proxy,
  serverless conversion, Docker, database or background queue is needed.
- One Uvicorn worker for the initial demonstration. Use an always-on paid service
  with approximately 2 GB RAM as a starting allocation, then observe actual usage.
  This is a sizing recommendation, not a load-tested memory guarantee. Free Render
  services sleep when idle and may exceed the frontend's 20-second browsing timeout
  during cold start. Select/approve the compute cost in your account before creating it.

Render documents HTTP responses up to 100 minutes. The existing browser timeout
for an investigation remains 600 seconds; Gemini's client timeout remains 120
seconds per call. Browsing requests remain 20 seconds. No execution timeouts or
analytical behavior were changed. Retries may run another paid investigation;
closing a browser request does not cancel server execution.

References: https://render.com/docs/web-services,
https://render.com/docs/render-vs-vercel-comparison,
https://render.com/docs/python-version, https://render.com/docs/free,
https://vercel.com/docs/frameworks/frontend/vite.

## Audit findings / required assets

- API entry point: `apps.api.app.main:app`; start from the repository root so the
  existing relative predictor path resolves. Dataset paths already resolve from
  the repository location. No Windows absolute paths are required by runtime code.
- `data/synthetic/burnin_dataset.csv` is tracked and contains 1,000 components.
- `ml/drift/random_forest_model.joblib` exists locally but was ignored/untracked.
  The narrowly scoped ignore exception now allows packaging that exact artifact.
  It is 14,633,233 bytes, a 200-tree RandomForestRegressor, SHA-256:
  `3364e86ea62626856530fd6bd48e3c5c5ec372144f978425c2e1433b60dd84de`.
  It has NOT been retrained or modified. Include it in the deployment source after
  reviewing/approving the commit. Do not regenerate models as a build step.
- Pinned backend requirements match the local Python 3.12.10 environment;
  scikit-learn is 1.9.1. The preflight rejects a changed artifact or model-version
  mismatch and runs one local prediction without Gemini. Cloud/Linux dependency
  installation and memory usage still require verification on the chosen host.
- No persistent filesystem writes are required for normal requests. Ephemeral
  hosting is sufficient when model/data files are included in every deployment.
- `/health` is reachability only, not Gemini quota/readiness verification. The
  asset preflight prevents a missing model from masquerading as a deployable build.
- Exact-origin CORS and SPA fallback configuration have been added. The API has
  no authentication or application rate limiting; CORS is not access control.
  Public investigation requests can consume Gemini quota. Use account quota/budget
  controls and keep this deployment scoped to the demonstration.

## Environment variables

Backend only (set in Render, never in Vercel's `VITE_*` variables):

| Name | Value / purpose |
| --- | --- |
| `GEMINI_API_KEY` | Required secret from your Google account; enter privately in Render. |
| `GEMINI_MODEL` | Explicit model ID available to that key and compatible with the existing Interactions API. Existing code default: `gemini-3.5-flash-lite`. Do not set an empty value. Preserve the working local model choice. |
| `SENTINEL_CORS_ORIGINS` | JSON array, e.g. `["https://YOUR-ASSIGNED-FRONTEND.vercel.app"]`. Exact origin, no path or wildcard. Add localhost:5173 / 127.0.0.1:5173 only when needed for direct cross-origin development. |
| `ENVIRONMENT` | `production` (informational API metadata). |
| `SENTINEL_CONVENTIONAL_24H_LIMIT_UA` | Optional; leave absent unless deliberately configured. No authoritative or generator-defined acceptance threshold exists. An operator-chosen demo value must be documented as synthetic demonstration configuration, not an ISRO/industry standard. |
| `PORT` | Supplied by Render; start command binds it on `0.0.0.0`. |
| `PYTHON_VERSION` | Optional override; omit to use committed `.python-version` = 3.12.10. |

`APP_NAME` and `APP_VERSION` optionally override informational metadata; their
existing defaults need no changes. The local `.env` currently has Gemini/model and
conventional-limit settings, but it is ignored and is NOT a deployment source.
Do not upload or commit it. Explicitly decide whether to carry over the optional
demo limit; no deployment default has been introduced.

Frontend:

- `VITE_API_BASE_URL=https://YOUR-ASSIGNED-BACKEND.onrender.com` — required on
  Vercel, public build-time value. No `/api/v1` suffix. Redeploy after changing it.
- `API_PROXY_TARGET` — local Vite dev/preview only; defaults to
  `http://127.0.0.1:8000`. It is not the production connection mechanism.
- Vercel supplies `VERCEL`; builds there reject a missing/non-HTTPS API origin.
- No Gemini credentials belong in the frontend project or bundle.

## Deploy in this order

1. Sign in to Vercel and Render. No authenticated deployment credentials were
   available locally during preparation. Never paste API keys into chat.
2. Review this deployment diff and the existing model artifact. This task does
   not commit or push. Git-based deployment cannot use these local changes until
   you commit/push them yourself or explicitly authorize that separate action.
3. In Vercel, import `R-yesh/Sentinel`, branch `main`, root `apps/web`, framework
   Vite, install `npm ci`, build `npm run build`, output `dist`, Node 22.x.
   Note the assigned stable frontend domain; do not guess it. Configure production
   and any intended preview environment separately. Preview domains must each be
   explicitly allowed by CORS if they call the backend.
4. In Render create a native Python Web Service from the same repository/branch.
   Leave Root Directory empty (repository root).
   - Build: `pip install -r apps/api/requirements.txt && python -m deployment.preflight`
   - Start: `python -m deployment.preflight && python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port $PORT --workers 1`
   - Health check: `/health`
   - Add the backend environment variables above, including exact Vercel origin.
   - Choose/approve an always-on compute plan and region with Gemini availability.
5. Set Vercel `VITE_API_BASE_URL` to the actual Render HTTPS URL and deploy/redeploy.
   `vercel.json` serves the SPA for deep links; API calls bypass Vercel entirely.
6. Verify the public application before presenting it. Do not declare success
   based only on a successful static build or `/health`.

## Public acceptance checks (pending deployment)

- Open/refresh `/overview`, `/dataset`, `/evaluation`, `/analysis` directly.
- Verify Overview/Evaluation use real data and the expected conventional setting.
- Search `C0030`; inspect its early observations and lot.
- Submit ONE real investigation explicitly. Confirm Gemini-backed outputs,
  authoritative disposition/explanation, node inspection, telemetry and replay.
- Check network/console for CORS, mixed-content, API errors and timeouts.
- A 502 investigation needs server/Gemini diagnosis. Missing assets or dependency
  failures must fail deployment, never trigger mock responses or model retraining.

## Local validation

From repository root:

```powershell
apps/api/.venv/Scripts/python.exe -m deployment.preflight
apps/api/.venv/Scripts/python.exe -m pytest tests/test_deployment.py tests/test_api_integration.py -q -p no:cacheprovider
```

From `apps/web`: `npm.cmd run test` and `npm.cmd run build`.
