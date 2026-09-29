import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.datasets import (
    DATASET_PATH, DatasetRepository, get_dataset_repository,
)
from shared.schemas.adversarial import AdversarialReview
from shared.schemas.explaination import ExplanationResult
from shared.schemas.judge import JudgeDecision


BASE = "/api/v1/datasets/synthetic-burnin/components"
SELECTION = {"dataset_id": "synthetic-burnin", "component_id": "C0001"}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def local_inference(monkeypatch):
    calls = []

    def generate(*, prompt, response_schema):
        calls.append(response_schema.__name__)
        if response_schema is AdversarialReview:
            return AdversarialReview(
                challenged_assessment="LOW_CONCERN", challenges=[], unresolved_conflict=False,
            )
        if response_schema is JudgeDecision:
            return JudgeDecision(
                decision="PASS", reason_code="EVIDENCE_SUPPORTS_PASS",
                reasoning="Fixture decision based on supplied evidence.",
                supporting_evidence=["Fixture evidence."], unresolved_concerns=[],
            )
        assert response_schema is ExplanationResult
        return ExplanationResult(
            headline="Fixture explanation", summary="Fixture summary",
            key_evidence=["Fixture evidence."], adversarial_context=[],
            decision_reasoning="Fixture decision reasoning.", recommended_action="Accept.",
        )

    for name in ("adversarial_qa", "reliability_judge", "explanation"):
        monkeypatch.setattr(f"agents.{name}.agent.generate_structured", generate)
    monkeypatch.setattr(
        "agents.drift_intelligence.agent.predict_168h",
        lambda frame: (np.array([12.25]), np.array([0.75])),
    )
    return calls


def use_dataset(tmp_path, rows):
    path = tmp_path / "burnin.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    repository = DatasetRepository(path)
    app.dependency_overrides[get_dataset_repository] = lambda: repository


def test_component_pagination_search_and_observation_contract(client):
    first = client.get(BASE, params={"page_size": 2}).json()
    second = client.get(BASE, params={"page_size": 2, "page": 2}).json()
    assert first["total"] == 1000
    assert [item["component_id"] for item in first["items"]] == ["C0001", "C0002"]
    assert [item["component_id"] for item in second["items"]] == ["C0003", "C0004"]
    assert client.get(BASE, params={"search": "lot-001"}).json()["total"] == 50
    assert client.get(BASE, params={"search": "c0001"}).json()["total"] == 1
    assert client.get(BASE, params={"search": ".*"}).json()["items"] == []
    assert client.get(BASE, params={"page": 999}).json()["items"] == []
    observation = client.get(f"{BASE}/C0001").json()
    assert set(observation) == {"component_id", "lot_id", "leakage_0h", "leakage_24h"}
    row = pd.read_csv(DATASET_PATH).iloc[0]
    assert observation["lot_id"] == row["lot_id"]
    assert observation["leakage_0h"] == row["leakage_0h"]
    assert observation["leakage_24h"] == row["leakage_24h"]


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_invalid_pagination(client, params):
    assert client.get(BASE, params=params).status_code == 422


@pytest.mark.parametrize("selection", [
    {"dataset_id": "unknown", "component_id": "C0001"},
    {"dataset_id": "synthetic-burnin", "component_id": "unknown"},
])
def test_unknown_selection(client, selection):
    assert client.post("/api/v1/investigations", json=selection).status_code == 404
    url = f"/api/v1/datasets/{selection['dataset_id']}/components/{selection['component_id']}"
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("payload", [
    {}, {"dataset_id": "synthetic-burnin", "component_id": " "},
    {**SELECTION, "raw_data": {"leakage_24h": 999}},
    {**SELECTION, "final_decision": "PASS"},
])
def test_selection_only_request(client, payload):
    assert client.post("/api/v1/investigations", json=payload).status_code == 422


def test_investigation_runs_existing_pipeline(client, local_inference):
    response = client.post("/api/v1/investigations", json=SELECTION)
    assert response.status_code == 200, response.text
    result = response.json()
    state = result["workflow"]
    assert result["dataset_id"] == "synthetic-burnin"
    assert state["component_id"] == "C0001"
    assert state["lot_id"] == "LOT-001"
    assert state["workflow_id"]
    assert state["status"] == "completed"
    assert state["final_decision"] == "PASS"
    context = state["lot_context"]
    assert context["lot_id"] == "LOT-001"
    peers = pd.read_csv(DATASET_PATH).query("lot_id == 'LOT-001' and component_id != 'C0001'")
    assert context["component_ids"] == peers["component_id"].tolist()
    assert context["leakage_0h_population"] == peers["leakage_0h"].tolist()
    assert context["leakage_24h_population"] == peers["leakage_24h"].tolist()
    assert set(state["raw_data"]) == {"leakage_0h", "leakage_24h"}
    names = {
        "data_forensics", "lot_intelligence", "drift_intelligence", "latent_defect",
        "adversarial_qa", "reliability_judge", "explanation",
    }
    assert set(state["agent_outputs"]) == names
    assert {finding["agent"] for finding in state["findings"]} == names
    assert len(state["findings"]) == 7
    assert state["agent_outputs"]["drift_intelligence"]["predicted_168h"] == 12.25
    assert state["agent_outputs"]["drift_intelligence"]["prediction_uncertainty"] == 0.75
    assert "isolation_score" in state["agent_outputs"]["lot_intelligence"]
    assert "assessment" in state["agent_outputs"]["latent_defect"]
    assert "risk_score" not in state["agent_outputs"]["latent_defect"]
    assert state["explanation"] == "Fixture decision reasoning."
    assert local_inference == ["AdversarialReview", "JudgeDecision", "ExplanationResult"]


def test_validation_stop_is_not_a_fabricated_decision(client, tmp_path, local_inference):
    use_dataset(tmp_path, [
        {"component_id": "C0001", "lot_id": "L", "leakage_0h": None, "leakage_24h": 10},
        {"component_id": "C0002", "lot_id": "L", "leakage_0h": 10, "leakage_24h": 10},
    ])
    response = client.post("/api/v1/investigations", json=SELECTION)
    assert response.status_code == 200
    state = response.json()["workflow"]
    assert state["status"] == "needs_review"
    assert state["final_decision"] is None
    assert state["explanation"] is None
    assert list(state["agent_outputs"]) == ["data_forensics"]
    assert local_inference == []


def test_nonfinite_statistics_are_explicit_valid_json(client, tmp_path, local_inference):
    use_dataset(tmp_path, [
        {"component_id": "C0001", "lot_id": "L", "leakage_0h": 10, "leakage_24h": 20},
        *[
            {"component_id": f"P{i}", "lot_id": "L", "leakage_0h": 10, "leakage_24h": 10}
            for i in range(5)
        ],
    ])
    response = client.post("/api/v1/investigations", json=SELECTION)
    assert response.status_code == 200, response.text

    def reject_constant(value):
        pytest.fail(f"Non-JSON number: {value}")

    state = json.loads(response.text, parse_constant=reject_constant)["workflow"]
    assert state["agent_outputs"]["lot_intelligence"]["robust_z_score"] == "Infinity"
    finding = next(item for item in state["findings"] if item["agent"] == "lot_intelligence")
    assert finding["metadata"]["robust_z_score"] == "Infinity"


def test_no_peers_is_an_input_error(client, tmp_path):
    use_dataset(tmp_path, [
        {"component_id": "C0001", "lot_id": "L", "leakage_0h": 10, "leakage_24h": 10},
    ])
    response = client.post("/api/v1/investigations", json=SELECTION)
    assert response.status_code == 422
    assert "No peer" in response.json()["detail"]


def test_dataset_unavailable(client, tmp_path):
    app.dependency_overrides[get_dataset_repository] = lambda: DatasetRepository(tmp_path / "missing.csv")
    assert client.get(BASE).status_code == 503
    assert client.post("/api/v1/investigations", json=SELECTION).status_code == 503


def test_execution_failure_has_no_fabricated_result(client, monkeypatch):
    async def fail(self, state):
        raise RuntimeError("Private dependency error")

    monkeypatch.setattr("apps.api.app.services.investigations.SentinelOrchestrator.run", fail)
    response = client.post("/api/v1/investigations", json=SELECTION)
    assert response.status_code == 502
    assert "workflow" not in response.json()
    assert "Private dependency error" not in response.text


def test_dataset_path_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(DatasetRepository().load("synthetic-burnin")) == 1000


def test_existing_routes_and_openapi(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/investigations" in paths
