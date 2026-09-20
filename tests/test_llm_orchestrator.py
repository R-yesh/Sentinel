import pytest

from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.schemas.workflow import WorkflowState

@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "component_id",
        "leakage_0h",
        "leakage_24h",
        "lot_leakage_24h",
        "expected_decision",
    ),
    [
        # Clearly healthy:
        # almost no early drift and normal relative to lot.
        (
            "HEALTHY-001",
            10.0,
            10.1,
            [
                9.8,
                10.0,
                10.1,
                10.2,
                10.3,
                9.9,
                10.0,
            ],
            "PASS",
        ),

        # Borderline:
        # noticeable early drift, but not an extreme
        # lot-relative anomaly.
        (
            "BORDERLINE-001",
            10.0,
            10.7,
            [
                10.0,
                10.2,
                10.4,
                10.5,
                10.6,
                10.8,
                11.0,
            ],
            "REVIEW",
        ),

        # Severe:
        # huge observed early drift and extremely
        # unusual relative to the rest of the lot.
        (
            "SEVERE-001",
            10.0,
            16.0,
            [
                9.8,
                10.0,
                10.1,
                10.2,
                10.3,
                9.9,
                10.1,
            ],
            "REJECT",
        ),
    ],
)
async def test_judge_decision_scenarios(
    component_id,
    leakage_0h,
    leakage_24h,
    lot_leakage_24h,
    expected_decision,
):
    state = WorkflowState(
        workflow_id=f"wf-{component_id}",
        component_id=component_id,
        raw_data={
            "leakage_0h": leakage_0h,
            "leakage_24h": leakage_24h,
            "lot_leakage_24h": lot_leakage_24h,
        },
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    print(
        f"\n{component_id}"
    )

    print(
        f"Expected: {expected_decision}"
    )

    print(
        f"Actual:   {result.final_decision}"
    )

    judge_output = result.agent_outputs.get(
        "reliability_judge",
        {},
    )

    print(
        "Reasoning:"
    )

    print(
        judge_output.get("reasoning")
    )

    assert result.final_decision == expected_decision

    explanation_output = result.agent_outputs.get(
        "explanation",
        {},
    )

    assert result.explanation is not None

    assert explanation_output.get("headline")
    assert explanation_output.get("summary")
    assert explanation_output.get("key_evidence")
    assert explanation_output.get("decision_reasoning")
    assert explanation_output.get("recommended_action")