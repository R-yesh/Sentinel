"""Retrospective synthetic evaluation; never an input to operational screening."""
import hashlib
import json
import math
from functools import lru_cache

from .datasets import DatasetRepository, DatasetUnavailable, OBSERVATION_COLUMNS
from .population import population

# The synthetic generator explicitly defines these classes. Unknown labels are
# excluded, not silently recoded as defects. No future leakage cutoff defines truth.
DEFECTIVE_LABELS = ('mild_drift', 'strong_drift', 'latent_defect')


class _EarlySnapshot(DatasetRepository):
    def __init__(self, frame):
        self.frame = frame[OBSERVATION_COLUMNS].copy()

    def load(self, dataset_id):
        return self.frame.copy()


def _rate(numerator, denominator):
    return numerator / denominator * 100 if denominator else None


def _coverage(rows):
    assessed = [r for r in rows if r['evaluated']]
    flagged = sum(r['early']['candidate'] is True for r in assessed)
    return dict(total=len(rows), evaluated=len(assessed), excluded=len(rows) - len(assessed),
                flagged=flagged, not_flagged=len(assessed) - flagged, flag_rate=_rate(flagged, len(assessed)))


@lru_cache(maxsize=2)
def _summarize(snapshot: str, early_json: str):
    source = json.loads(snapshot)
    screening = json.loads(early_json)
    early_by_id = {row['component_id']: row for row in screening['components']}
    configured = screening['comparison']['status'] == 'configured'
    components = []
    for record in source:
        early = early_by_id[record['component_id']]
        label = record['defect_type']
        classification = 'healthy' if label == 'healthy' else 'defective' if label in DEFECTIVE_LABELS else 'unknown'
        evaluated = classification != 'unknown' and early['candidate'] is not None
        bucket = None
        if evaluated and configured:
            candidate, conventional = early['candidate'], early['conventional_flag']
            bucket = 'both' if candidate and conventional else 'sentinel_only' if candidate else 'conventional_only' if conventional else 'neither'
        components.append(dict(early=early, evaluated=evaluated, comparison_bucket=bucket,
                               hindsight=dict(defect_type=label, synthetic_class=classification,
                                              leakage_96h=record['leakage_96h'], leakage_168h=record['leakage_168h'])))
    evaluated = [r for r in components if r['evaluated']]
    healthy = [r for r in components if r['hindsight']['synthetic_class'] == 'healthy']
    defective = [r for r in components if r['hindsight']['synthetic_class'] == 'defective']
    defective_assessed = [r for r in defective if r['evaluated']]
    overlap = dict(drift_only=0, lot_only=0, both=0, neither=0)
    for row in evaluated:
        reasons = row['early']['reasons']
        drift = 'significant_early_drift' in reasons
        lot = 'high_side_lot_deviation' in reasons
        overlap['both' if drift and lot else 'drift_only' if drift else 'lot_only' if lot else 'neither'] += 1
    comparison = dict(status=screening['comparison']['status'], limit_ua=screening['comparison']['limit_ua'],
                      rule=screening['comparison']['rule'], comparable_defective=len(defective_assessed),
                      excluded_defective=len(defective) - len(defective_assessed),
                      conventional_flagged=None, sentinel_flagged=None,
                      conventional_only=None, sentinel_only=None, both=None, neither=None)
    if configured:
        for key in ('conventional_only', 'sentinel_only', 'both', 'neither'):
            comparison[key] = sum(r['comparison_bucket'] == key for r in defective_assessed)
        comparison['conventional_flagged'] = comparison['conventional_only'] + comparison['both']
        comparison['sentinel_flagged'] = comparison['sentinel_only'] + comparison['both']
    total_coverage = _coverage(components)
    return dict(dataset_id=screening['dataset_id'], evaluation_only=True,
                snapshot_id=hashlib.sha256((snapshot + early_json).encode()).hexdigest()[:12],
                screening_method=screening['method'], healthy_label='healthy', defective_labels=list(DEFECTIVE_LABELS),
                summary=dict(total=len(components), evaluated=len(evaluated), excluded=len(components) - len(evaluated),
                             unknown_labels=len(components) - len(healthy) - len(defective),
                             candidates=total_coverage['flagged'], screening_rate=total_coverage['flag_rate'],
                             healthy=_coverage(healthy), defective=_coverage(defective)),
                by_defect_type=[dict(defect_type=label, **_coverage([r for r in components if (r['hindsight']['defect_type'] or '(missing)') == label]))
                                for label in sorted({r['hindsight']['defect_type'] or '(missing)' for r in components})],
                signal_overlap=overlap, comparison=comparison, components=components)


def evaluation(repository: DatasetRepository, dataset_id: str):
    frame = repository.load(dataset_id)
    if 'defect_type' not in frame.columns:
        raise DatasetUnavailable('Synthetic evaluation requires the defect_type column.')
    # One source snapshot for both views. Phase 4 sees only the early allowlist;
    # labels/future observations cannot influence its flags, peers, or cache key.
    early = population(_EarlySnapshot(frame), dataset_id)
    records = []
    for row in frame.sort_values('component_id').to_dict('records'):
        label = row.get('defect_type')
        record = dict(component_id=row['component_id'], defect_type=label.strip() if isinstance(label, str) and label.strip() else None)
        for key in ('leakage_96h', 'leakage_168h'):
            try:
                value = float(row.get(key))
                record[key] = value if math.isfinite(value) and value >= 0 else None
            except (ValueError, TypeError):
                record[key] = None
        records.append(record)
    return _summarize(json.dumps(records, sort_keys=True, allow_nan=False), json.dumps(early, sort_keys=True, allow_nan=False))
