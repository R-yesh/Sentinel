import pytest

from agents.reliability_judge.agent import (
    ReliabilityJudgeAgent,
)
from shared.schemas.workflow import (
    WorkflowState,
    WorkflowStatus,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "component_id",
        "latent_output",
        "adversarial_review",
        "expected_decision",
    ),
    [
        # -------------------------------------------------
        # 1. HEALTHY / REASSURING
        # -------------------------------------------------
        (
            "HEALTHY-V2",
            {
                "assessment": "LOW_CONCERN",
                "signals": [],
                "robust_z_score": 0.25,
                "robust_anomaly_score": 0.05,
                "deviation_direction": "HIGH",
                "lot_evidence_level": "TYPICAL",
                "isolation_score": -0.08,
                "isolation_anomaly": False,
                "percentage_change": 1.0,
                "early_slope": 0.004,
                "predicted_168h": 10.3,
                "prediction_uncertainty": 0.5,
            },
            {
                "challenged_assessment": "LOW_CONCERN",
                "challenges": [
                    {
                        "challenge_type": "MODEL_UNCERTAINTY",
                        "direction": "HIGHER_CONCERN",
                        "summary": (
                            "The 168h value remains a model "
                            "forecast rather than an observed "
                            "measurement."
                        ),
                    }
                ],
                "unresolved_conflict": False,
            },
            "PASS",
        ),

        # -------------------------------------------------
        # 2. STRONG CORROBORATED CONCERN
        # -------------------------------------------------
        (
            "SEVERE-V2",
            {
                "assessment": "HIGH_CONCERN",
                "signals": [
                    "significant_early_drift",
                    "strong_lot_deviation",
                    "isolation_forest_anomaly",
                ],
                "robust_z_score": 4.2,
                "robust_anomaly_score": 0.84,
                "deviation_direction": "HIGH",
                "lot_evidence_level": "OUTLIER",
                "isolation_score": 0.21,
                "isolation_anomaly": True,
                "percentage_change": 55.0,
                "early_slope": 0.23,
                "predicted_168h": 22.0,
                "prediction_uncertainty": 1.4,
            },
            {
                "challenged_assessment": "HIGH_CONCERN",
                "challenges": [
                    {
                        "challenge_type": "ASSUMPTION_CHALLENGE",
                        "direction": "LOWER_CONCERN",
                        "summary": (
                            "The exact 168h forecast depends "
                            "on model assumptions and should "
                            "not be treated as an observed "
                            "measurement."
                        ),
                    },
                    {
                        "challenge_type": (
                            "CORROBORATING_EVIDENCE"
                        ),
                        "direction": "HIGHER_CONCERN",
                        "summary": (
                            "Observed early degradation and "
                            "both lot-relative analytical "
                            "views indicate unusual behaviour."
                        ),
                    },
                ],
                "unresolved_conflict": False,
            },
            "REJECT",
        ),

        # -------------------------------------------------
        # 3. GENUINELY CONFLICTING EVIDENCE
        # -------------------------------------------------
        (
            "CONFLICT-V2",
            {
                "assessment": "ELEVATED_CONCERN",
                "signals": [
                    "significant_early_drift",
                    "isolation_forest_anomaly",
                ],
                "robust_z_score": 0.4,
                "robust_anomaly_score": 0.08,
                "deviation_direction": "HIGH",
                "lot_evidence_level": "TYPICAL",
                "isolation_score": 0.08,
                "isolation_anomaly": True,
                "percentage_change": 7.0,
                "early_slope": 0.029,
                "predicted_168h": 16.2,
                "prediction_uncertainty": 2.7,
            },
            {
                "challenged_assessment": (
                    "ELEVATED_CONCERN"
                ),
                "challenges": [
                    {
                        "challenge_type": (
                            "CONFLICTING_EVIDENCE"
                        ),
                        "direction": "LOWER_CONCERN",
                        "summary": (
                            "Robust lot statistics classify "
                            "the component as typical relative "
                            "to its lot."
                        ),
                    },
                    {
                        "challenge_type": (
                            "CORROBORATING_EVIDENCE"
                        ),
                        "direction": "HIGHER_CONCERN",
                        "summary": (
                            "Observed early drift and the "
                            "Isolation Forest anomaly indicate "
                            "potentially abnormal behaviour."
                        ),
                    },
                ],
                "unresolved_conflict": True,
            },
            "REVIEW",
        ),
    ],
)
async def test_judge_v2_decision_scenarios(
    component_id,
    latent_output,
    adversarial_review,
    expected_decision,
):
    state = WorkflowState(
        workflow_id=f"wf-{component_id}",
        component_id=component_id,
        raw_data={},
    )

    state.agent_outputs["latent_defect"] = (
        latent_output
    )

    state.agent_outputs["adversarial_qa"] = {
        "review": adversarial_review,
    }

    agent = ReliabilityJudgeAgent()

    result = await agent.run(state)

    judge_output = result.agent_outputs[
        "reliability_judge"
    ]

    actual_decision = judge_output["decision"]

    print()
    print(component_id)
    print(f"Expected: {expected_decision}")
    print(f"Actual:   {actual_decision}")
    print("Reasoning:")
    print(judge_output["reasoning"])

    assert actual_decision == expected_decision

    assert judge_output["reason_code"] is not None

    assert judge_output["reasoning"]

    assert "supporting_evidence" in judge_output

    assert "unresolved_concerns" in judge_output

    assert result.final_decision == expected_decision

    if expected_decision == "REVIEW":
        assert (
            result.status
            == WorkflowStatus.NEEDS_REVIEW
        )
    else:
        assert (
            result.status
            == WorkflowStatus.COMPLETED
        )


@pytest.mark.asyncio
async def test_judge_v2_missing_evidence_guardrail():
    state = WorkflowState(
        workflow_id="wf-missing-v2",
        component_id="MISSING-V2",
        raw_data={},
    )

    state.agent_outputs["latent_defect"] = {
        "assessment": "INSUFFICIENT_EVIDENCE",
        "signals": [],
    }

    state.agent_outputs["adversarial_qa"] = {
        "review": None,
        "reason": "insufficient_evidence",
    }

    agent = ReliabilityJudgeAgent()

    result = await agent.run(state)

    judge_output = result.agent_outputs[
        "reliability_judge"
    ]

    print()
    print("MISSING-V2")
    print(judge_output)

    assert result.final_decision == "REVIEW"

    assert (
        result.status
        == WorkflowStatus.NEEDS_REVIEW
    )

    assert (
        judge_output["decision"]
        == "REVIEW"
    )

    assert (
        judge_output["reason_code"]
        == "INSUFFICIENT_EVIDENCE"
    )