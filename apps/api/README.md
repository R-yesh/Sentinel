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

## Population screening (Phase 4)

`GET /api/v1/datasets/synthetic-burnin/population` returns the full observed
population with derived screening evidence, summary counts, lot counts, ten
equal-width percentage-change histogram bins, and conventional comparison groups.
This is a read-only screen, not 1,000 investigations. No LLM, Isolation Forest
fits, or RF predictions run on this route. The existing agents are unchanged.

A **screening candidate** has either early percentage change at or above the
existing `EARLY_DRIFT_THRESHOLD` (currently 6%), OR HIGH-direction non-TYPICAL
evidence from `detect_lot_anomaly` (ELEVATED, STRONG_DEVIATION, OUTLIER). This
reuses the originating concern gates of Latent Defect, not its assessment or
Reliability Judge decisions. The detector's existing levels start at positive
robust z-scores of 1.5, 2.5, and 3.5. No threshold was modified.

Percentage change/slope use `build_early_feature_vector`, including its 0%
percentage-change convention for a zero baseline. Paired peer context comes
from `build_lot_context`, excluding the component itself. Missing, non-finite,
negative observations, missing peers, or invalid peer populations leave the
component unassessed. Unassessed rows are not counted as having no signal.
Histogram and signal totals use fully screened rows. Signal totals overlap;
the candidate count is their union. Rows are sorted by reason count descending,
then component ID, not by a calibrated reliability-risk score.

No authoritative conventional threshold exists in the repository. By default,
comparison counts are null and the UI requests a domain-approved reference.
An optional server environment variable `SENTINEL_CONVENTIONAL_24H_LIMIT_UA`
enables the explicit rule **observed leakage_24h > configured limit (µA)**.
Set a finite non-negative domain-approved value before starting the API; restart
after changing it. There is no threshold editor and no default numerical limit.
Configuration itself does not establish scientific approval. Invalid values
return 503 rather than silently changing the rule.

Comparison uses only fully screened rows and partitions them into conventional
only, Sentinel only, both, and neither. The excluded count is explicit. A
Sentinel-only candidate is not called a missed defect. `defect_type`, 96h and
168h future observations are never used or returned. IF, RF forecasts, tree
disagreement, and final adjudication remain in individual investigations.

The dataset is reread on each request; a bounded two-snapshot in-memory cache
keys analysis by observed content and the conventional setting. A lock coalesces
concurrent cold computations. No persistence or background infrastructure is
introduced. `snapshot_id` fingerprints observations; `method` identifies the
screening definition. Non-finite robust z-scores retain explicit Infinity strings.

Focused validation:

```powershell
apps/api/.venv/Scripts/python.exe -m pytest tests/test_population.py -q -p no:cacheprovider
```

## Investigation execution

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
