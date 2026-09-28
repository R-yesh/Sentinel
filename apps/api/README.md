# Sentinel demonstration API

Run from the **repository root** using the API virtual environment:

```powershell
apps/api/.venv/Scripts/python.exe -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

The root working directory is required by the existing ML model loader. Provision
`ml/drift/random_forest_model.joblib` (ignored by Git) and configure
`GEMINI_API_KEY` server-side; `GEMINI_MODEL` is optional. Dataset browsing does
not call Gemini or load the ML model. API documentation is at `/docs`.

## Dataset browsing

The supported dataset ID is `synthetic-burnin`, mapped server-side to
`data/synthetic/burnin_dataset.csv`. Requests cannot select filesystem paths.

- `GET /api/v1/datasets/synthetic-burnin/components?search=LOT-001&page=1&page_size=25`
- `GET /api/v1/datasets/synthetic-burnin/components/C0001`

Search is a case-insensitive literal substring match against component and lot
IDs. Results are sorted by component ID. Pages start at 1; page size is 1–100.
The list response contains `dataset_id`, `items`, `total`, `page`, and `page_size`.
Each component contains only `component_id`, `lot_id`, `leakage_0h`, and
`leakage_24h`. Measurements are observed leakage in µA. Synthetic labels and
later observations are deliberately excluded from this early investigation API.

## Investigation

`POST /api/v1/investigations` with:

```json
{"dataset_id": "synthetic-burnin", "component_id": "C0001"}
```

The server reads one dataset snapshot, constructs peer context with the existing
`build_lot_context`, creates a fresh `WorkflowState`, and executes the unchanged
orchestrator. The request waits for the whole pipeline, including LLM explanation.
Execution uses FastAPI's synchronous-route thread pool. There is no persistence
or subsequent lookup endpoint. A browser/proxy timeout does not imply cancellation.

HTTP 200 returns `{"dataset_id": "synthetic-burnin", "workflow": {...}}`.
`workflow` preserves the existing state fields, findings, and agent output shapes.
A validation stop is also a returned workflow: `needs_review` can have a null
decision and explanation. A judge `REVIEW` is distinct from that early stop.

At the JSON boundary only, non-finite numbers are encoded as the strings
`"Infinity"`, `"-Infinity"`, or `"NaN"`, recursively, including finding metadata.
This retains their meaning without emitting invalid JSON or silently turning
an unbounded statistic into zero or null. Finite numbers stay numeric.

Observed inputs remain in `raw_data`; forecasts and uncertainty remain in drift
outputs; anomaly measures remain in lot outputs; provisional assessments remain
in latent outputs; final decisions come from the judge. No failure probability
or confidence interval is inferred by the API.

Errors: 404 for unknown selections; 422 for malformed requests or unavailable
peer context; 503 for an unavailable/invalid dataset; 502 for pipeline execution
failure. Execution errors return no fabricated workflow result; details are logged
server-side.

## Focused tests

```powershell
apps/api/.venv/Scripts/python.exe -m pytest tests/test_api_integration.py -q -p no:cacheprovider
```

The tests execute the existing orchestrator and analytical agents with controlled
forecast/LLM responses, without external Gemini calls. The existing predictor
test can separately verify the local model artifact.
