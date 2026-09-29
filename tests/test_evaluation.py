import pandas as pd
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.datasets import DatasetRepository, get_dataset_repository
from apps.api.app.services.evaluation import evaluation
from apps.api.app.services.population import LIMIT_ENV, population

BASE = '/api/v1/datasets/synthetic-burnin'


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.delenv(LIMIT_ENV, raising=False)
    rows = [('A', 'L1', 'healthy', 10, 10), ('B', 'L1', 'mild_drift', 10, 10),
            ('C', 'L1', 'strong_drift', 10, 12), ('E', 'L2', 'healthy', 10, 10),
            ('F', 'L2', 'mild_drift', 12, 12), ('G', 'L2', 'mild_drift', 8, 9),
            ('H', 'L2', 'latent_defect', 20, 20)]
    frame = pd.DataFrame(rows, columns=['component_id', 'lot_id', 'defect_type', 'leakage_0h', 'leakage_24h'])
    frame['leakage_96h'] = 30
    frame['leakage_168h'] = 40
    path = tmp_path / 'synthetic.csv'
    frame.to_csv(path, index=False)
    repository = DatasetRepository(path)
    app.dependency_overrides[get_dataset_repository] = lambda: repository
    yield repository
    app.dependency_overrides.clear()


def test_metrics_grouping_overlap_and_exact_phase4_screen(repo):
    result = evaluation(repo, 'synthetic-burnin')
    phase4 = population(repo, 'synthetic-burnin')
    assert {r['early']['component_id']: r['early'] for r in result['components']} == {r['component_id']: r for r in phase4['components']}
    summary = result['summary']
    assert (summary['total'], summary['evaluated'], summary['candidates']) == (7, 7, 3)
    assert summary['screening_rate'] == pytest.approx(300 / 7)
    assert summary['healthy'] == dict(total=2, evaluated=2, excluded=0, flagged=0, not_flagged=2, flag_rate=0)
    assert summary['defective'] == dict(total=5, evaluated=5, excluded=0, flagged=3, not_flagged=2, flag_rate=60)
    groups = {r['defect_type']: r for r in result['by_defect_type']}
    assert (groups['mild_drift']['total'], groups['mild_drift']['flagged'], groups['mild_drift']['not_flagged']) == (3, 1, 2)
    assert groups['mild_drift']['flag_rate'] == pytest.approx(100 / 3)
    assert groups['latent_defect']['flag_rate'] == groups['strong_drift']['flag_rate'] == 100
    assert result['signal_overlap'] == dict(drift_only=1, lot_only=1, both=1, neither=4)
    assert sum(result['signal_overlap'].values()) == summary['evaluated']
    assert result['comparison']['status'] == 'unconfigured'
    assert result['comparison']['sentinel_only'] is None
    assert all(r['comparison_bucket'] is None for r in result['components'])


def test_conventional_comparison_all_four_buckets_and_strict_limit(repo, monkeypatch):
    monkeypatch.setenv(LIMIT_ENV, '11')
    result = evaluation(repo, 'synthetic-burnin')
    c = result['comparison']
    assert (c['conventional_only'], c['sentinel_only'], c['both'], c['neither']) == (1, 1, 2, 1)
    assert c['conventional_flagged'] == c['sentinel_flagged'] == 3
    assert c['comparable_defective'] == 5
    assert {r['early']['component_id'] for r in result['components'] if r['comparison_bucket'] == 'conventional_only'} == {'F'}
    monkeypatch.setenv(LIMIT_ENV, '12')
    c = evaluation(repo, 'synthetic-burnin')['comparison']
    assert (c['conventional_only'], c['sentinel_only'], c['both'], c['neither']) == (0, 2, 1, 2)


def test_hindsight_changes_metrics_not_early_flags_and_never_leaks_operationally(repo):
    before = evaluation(repo, 'synthetic-burnin')
    frame = pd.read_csv(repo.path)
    frame.loc[frame.component_id == 'C', 'defect_type'] = 'healthy'
    frame['leakage_168h'] = 9999
    frame.to_csv(repo.path, index=False)
    after = evaluation(repo, 'synthetic-burnin')
    assert before['snapshot_id'] != after['snapshot_id']
    assert [r['early'] for r in before['components']] == [r['early'] for r in after['components']]
    assert after['summary']['healthy']['flagged'] == 1
    assert after['summary']['healthy']['flag_rate'] == pytest.approx(100 / 3)
    with TestClient(app) as client:
        response = client.get(BASE + '/evaluation')
        assert response.status_code == 200 and response.json()['evaluation_only'] is True
        assert response.json()['components'][0]['hindsight']['leakage_168h'] == 9999
        for path in ('/population', '/components', '/components/C'):
            operational = client.get(BASE + path)
            assert operational.status_code == 200
            assert not any(field in operational.text for field in ('defect_type', 'leakage_96h', 'leakage_168h', 'hindsight'))


def test_exclusions_and_missing_future_observations(repo):
    frame = pd.read_csv(repo.path)
    frame.loc[frame.component_id == 'A', 'defect_type'] = 'unknown-class'
    frame.loc[frame.component_id == 'B', 'leakage_0h'] = -1
    frame = frame.drop(columns=['leakage_96h', 'leakage_168h'])
    frame.to_csv(repo.path, index=False)
    result = evaluation(repo, 'synthetic-burnin')
    assert result['summary']['unknown_labels'] == 1
    assert result['summary']['excluded'] == 3  # Entire L1 has invalid input/peer context.
    assert result['summary']['evaluated'] == 4
    assert sum(result['signal_overlap'].values()) == 4
    assert all(r['hindsight']['leakage_168h'] is None for r in result['components'])
    frame['defect_type'] = 'unknown-class'
    frame.to_csv(repo.path, index=False)
    assert evaluation(repo, 'synthetic-burnin')['summary']['screening_rate'] is None


def test_missing_label_column_and_unknown_dataset_report_errors(repo):
    pd.read_csv(repo.path).drop(columns=['defect_type']).to_csv(repo.path, index=False)
    with TestClient(app) as client:
        assert client.get(BASE + '/evaluation').status_code == 503
        assert client.get(BASE.replace('synthetic-burnin', 'unknown') + '/evaluation').status_code == 404
