import pytest

from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.schemas.workflow import WorkflowState


@pytest.mark.asyncio
async def test_full_investigation_pipeline():
    state = WorkflowState(
        workflow_id="wf-test-001",
        component_id="A173",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 14.0,
            "lot_leakage_24h": [
                9.8,
                10.2,
                10.1,
                9.9,
                10.4,
                9.7,
                10.0,
            ],
        },
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    agent_names = {
        finding.agent
        for finding in result.findings
    }

    assert "data_forensics" in agent_names
    assert "lot_intelligence" in agent_names
    assert "drift_intelligence" in agent_names
    assert "latent_defect" in agent_names
    assert "adversarial_qa" in agent_names
    assert "reliability_judge" in agent_names
    assert "explanation" in agent_names

    assert result.final_decision in {
        "PASS",
        "REVIEW",
        "REJECT",
    }

    assert result.explanation is not None


@pytest.mark.asyncio
async def test_bad_data_stops_downstream_analysis():
    state = WorkflowState(
        workflow_id="wf-test-002",
        component_id="BROKEN-001",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": None,
            "lot_leakage_24h": [
                9.8,
                10.2,
                10.1,
            ],
        },
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    agent_names = {
        finding.agent
        for finding in result.findings
    }

    assert "data_forensics" in agent_names

    assert "lot_intelligence" not in agent_names
    assert "drift_intelligence" not in agent_names
    assert "latent_defect" not in agent_names