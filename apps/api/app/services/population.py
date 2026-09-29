"""Read-only population triage. No agents, LLM calls, or model fitting.

Candidate gates match the existing latent-defect *originating* evidence:
significant early drift OR high-side non-typical lot evidence. Corroborating
IF/RF context and all adjudication are deliberately left to investigations.
"""
import hashlib
import json
import math
import os
from functools import lru_cache
from threading import Lock

import numpy as np
import pandas as pd

from ml.anomaly.detector import detect_lot_anomaly
from ml.anomaly.isolation_forest import build_early_feature_vector
from shared.config.signal_thresholds import EARLY_DRIFT_THRESHOLD
from shared.context.lot_context import build_lot_context

from .datasets import DatasetRepository, DatasetUnavailable, OBSERVATION_COLUMNS

_cache_lock = Lock()
LIMIT_ENV = 'SENTINEL_CONVENTIONAL_24H_LIMIT_UA'


def conventional_limit() -> float | None:
    value = os.environ.get(LIMIT_ENV)
    if value is None or not value.strip():
        return None
    try:
        limit = float(value)
        if not math.isfinite(limit) or limit < 0:
            raise ValueError()
        return limit
    except ValueError as exc:
        raise DatasetUnavailable(f'{LIMIT_ENV} must be a finite non-negative number.') from exc


def valid(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


@lru_cache(maxsize=2)
def _screen(snapshot: str, limit: float | None) -> dict:
    frame = pd.DataFrame(json.loads(snapshot), columns=OBSERVATION_COLUMNS)
    rows = []
    for observed in json.loads(snapshot):
        row = {**observed, 'percentage_change': None, 'early_slope': None,
               'lot_evidence': None, 'robust_z_score': None, 'candidate': None,
               'reasons': [], 'issue': None, 'conventional_flag': None}
        if not all(valid(observed[key]) for key in ('leakage_0h', 'leakage_24h')):
            row['issue'] = 'Missing, non-finite, or negative observed measurement.'
        else:
            features = build_early_feature_vector(observed['leakage_0h'], observed['leakage_24h'])
            row.update(percentage_change=features[3], early_slope=features[4])
            row['conventional_flag'] = observed['leakage_24h'] > limit if limit is not None else None
            try:
                context = build_lot_context(frame, observed['component_id'])
                if not all(valid(v) for v in context.leakage_0h_population + context.leakage_24h_population):
                    raise ValueError('Invalid peer observations')
                evidence = detect_lot_anomaly(observed['leakage_24h'], context.leakage_24h_population)
                row['lot_evidence'] = evidence.evidence_level.value
                z = evidence.robust_z_score
                row['robust_z_score'] = z if math.isfinite(z) else ('Infinity' if z > 0 else '-Infinity')
                if features[3] >= EARLY_DRIFT_THRESHOLD:
                    row['reasons'].append('significant_early_drift')
                if evidence.deviation_direction.value == 'HIGH' and evidence.evidence_level.value != 'TYPICAL':
                    row['reasons'].append('high_side_lot_deviation')
                row['candidate'] = bool(row['reasons'])
            except ValueError:
                row['issue'] = 'Paired valid lot peers unavailable; screening is incomplete.'
        rows.append(row)

    assessed = [r for r in rows if r['candidate'] is not None]
    candidates = sum(r['candidate'] for r in assessed)
    lots = []
    for lot_id in sorted({r['lot_id'] for r in rows}):
        group = [r for r in rows if r['lot_id'] == lot_id]
        count = sum(r['candidate'] is not None for r in group)
        lots.append(dict(lot_id=lot_id, total=len(group), screened=count,
                         candidates=sum(r['candidate'] is True for r in group), unassessed=len(group) - count))
    changes = [r['percentage_change'] for r in assessed]
    histogram = []
    if changes:
        counts, edges = np.histogram(changes, bins=10)
        histogram = [dict(lower=float(edges[i]), upper=float(edges[i + 1]), count=int(count)) for i, count in enumerate(counts)]
    comparison = dict(status='configured' if limit is not None else 'unconfigured', limit_ua=limit,
                      rule='Observed leakage_24h > configured limit (µA). Domain approval required.',
                      comparable=len(assessed), excluded=len(rows) - len(assessed),
                      conventional_only=None, sentinel_only=None, both=None, neither=None)
    if limit is not None:
        comparison.update(
            conventional_only=sum(r['conventional_flag'] and not r['candidate'] for r in assessed),
            sentinel_only=sum(r['candidate'] and not r['conventional_flag'] for r in assessed),
            both=sum(r['candidate'] and r['conventional_flag'] for r in assessed),
            neither=sum(not r['candidate'] and not r['conventional_flag'] for r in assessed),
        )
    return dict(dataset_id='synthetic-burnin', snapshot_id=hashlib.sha256(snapshot.encode()).hexdigest()[:12],
                method='early-drift-and-leave-one-out-lot-v1', early_drift_threshold_percent=EARLY_DRIFT_THRESHOLD,
                summary=dict(total=len(rows), lots=len(lots), screened=len(assessed), unassessed=len(rows) - len(assessed),
                             candidates=candidates, no_screening_signal=len(assessed) - candidates,
                             significant_drift=sum('significant_early_drift' in r['reasons'] for r in assessed),
                             high_side_lot=sum('high_side_lot_deviation' in r['reasons'] for r in assessed)),
                comparison=comparison, lots=lots, drift_histogram=histogram,
                components=sorted(rows, key=lambda r: (-len(r['reasons']), r['component_id'])))


def population(repository: DatasetRepository, dataset_id: str) -> dict:
    frame = repository.load(dataset_id)[OBSERVATION_COLUMNS].sort_values('component_id')
    records = frame.to_dict('records')
    # Normalize non-finite observations as unavailable; never feed them to statistics.
    for row in records:
        for key in ('leakage_0h', 'leakage_24h'):
            if row[key] is not None and not math.isfinite(row[key]):
                row[key] = None
    snapshot = json.dumps(records, allow_nan=False, sort_keys=True)
    # Content-keyed bounded cache; a changed source invalidates the analysis. The
    # lock coalesces concurrent cold requests without adding background jobs.
    with _cache_lock:
        return _screen(snapshot, conventional_limit())
