import pandas as pd
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.datasets import DatasetRepository, get_dataset_repository
from apps.api.app.services.population import LIMIT_ENV, _screen, population
from ml.anomaly.detector import detect_lot_anomaly
from shared.context.lot_context import build_lot_context

URL = '/api/v1/datasets/synthetic-burnin/population'


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.delenv(LIMIT_ENV, raising=False)
    _screen.cache_clear()
    path = tmp_path / 'observations.csv'
    pd.DataFrame([
        dict(component_id='A', lot_id='L1', leakage_0h=10, leakage_24h=10, defect_type='hidden', leakage_168h=900),
        dict(component_id='B', lot_id='L1', leakage_0h=10, leakage_24h=10),
        dict(component_id='C', lot_id='L1', leakage_0h=10, leakage_24h=12),
        dict(component_id='D', lot_id='L2', leakage_0h=5, leakage_24h=5),
    ]).to_csv(path, index=False)
    repo = DatasetRepository(path)
    app.dependency_overrides[get_dataset_repository] = lambda: repo
    yield repo
    app.dependency_overrides.clear()


def test_screening_uses_existing_peer_detector_and_excludes_future_labels(source):
    with TestClient(app) as client:
        response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body['summary'] == dict(total=4, lots=2, screened=3, unassessed=1, candidates=1,
                                    no_screening_signal=2, significant_drift=1, high_side_lot=1)
    c = next(row for row in body['components'] if row['component_id'] == 'C')
    context = build_lot_context(source.load('synthetic-burnin'), 'C')
    expected = detect_lot_anomaly(12, context.leakage_24h_population)
    assert c['lot_evidence'] == expected.evidence_level.value
    assert c['robust_z_score'] == 'Infinity'
    assert c['reasons'] == ['significant_early_drift', 'high_side_lot_deviation']
    assert c['percentage_change'] == 20
    assert body['comparison']['both'] is None
    assert body['comparison']['status'] == 'unconfigured'
    assert sum(b['count'] for b in body['drift_histogram']) == 3
    assert 'defect_type' not in response.text and 'leakage_168h' not in response.text
    assert 'final_decision' not in response.text


def test_configured_comparison_is_explicit_strict_and_excludes_unassessed(source, monkeypatch):
    monkeypatch.setenv(LIMIT_ENV, '12')
    result = population(source, 'synthetic-burnin')['comparison']
    assert result['limit_ua'] == 12
    assert (result['sentinel_only'], result['both'], result['neither'], result['conventional_only']) == (1, 0, 2, 0)
    assert result['excluded'] == 1
    monkeypatch.setenv(LIMIT_ENV, '11')
    assert population(source, 'synthetic-burnin')['comparison']['both'] == 1


def test_invalid_peer_population_remains_unassessed_and_cache_invalidates(source):
    before = population(source, 'synthetic-burnin')
    population(source, 'synthetic-burnin')
    assert _screen.cache_info().hits == 1
    frame = pd.read_csv(source.path)
    frame.loc[frame.component_id == 'B', 'leakage_0h'] = -1
    frame.to_csv(source.path, index=False)
    after = population(source, 'synthetic-burnin')
    assert after['snapshot_id'] != before['snapshot_id']
    assert after['summary']['unassessed'] == 4
    assert after['summary']['no_screening_signal'] == 0


def test_population_route_errors_and_invalid_reference(source, monkeypatch):
    with TestClient(app) as client:
        assert client.get(URL.replace('synthetic-burnin', 'unknown')).status_code == 404
        monkeypatch.setenv(LIMIT_ENV, 'NaN')
        assert client.get(URL).status_code == 503
        monkeypatch.delenv(LIMIT_ENV)
        source.path.write_text('invalid\nvalue\n')
        assert client.get(URL).status_code == 503


def test_zero_baseline_preserves_existing_feature_convention(source):
    frame = pd.read_csv(source.path)
    frame.loc[frame.component_id == 'A', ['leakage_0h', 'leakage_24h']] = [0, 1]
    frame.to_csv(source.path, index=False)
    row = next(r for r in population(source, 'synthetic-burnin')['components'] if r['component_id'] == 'A')
    assert row['percentage_change'] == 0
    assert row['early_slope'] == pytest.approx(1 / 24)
    assert 'significant_early_drift' not in row['reasons']
