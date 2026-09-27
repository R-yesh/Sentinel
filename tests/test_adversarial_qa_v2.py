import pytest

from agents.adversarial_qa.agent import AdversarialQAAgent
from shared.schemas.workflow import WorkflowState


@pytest.mark.asyncio
async def test_adversarial_qa_with_v2_lot_evidence():
    state = WorkflowState(
        workflow_id="wf-adversarial-v2",
        component_id="C0030",
        raw_data={},
    )

    # Simulate Latent Defect V2 output.
    state.agent_outputs["latent_defect"] = {
        "assessment": "ELEVATED_CONCERN",
        "signals": [
            "elevated_lot_deviation",
            "unusual_early_lot_behavior",
            "significant_early_drift",
        ],

        "robust_z_score": 1.912,
        "robust_anomaly_score": 0.3824,
        "deviation_direction": "HIGH",
        "lot_evidence_level": "ELEVATED",

        "isolation_score": 0.0795,
        "isolation_anomaly": True,

        "percentage_change": 8.5,
        "early_slope": 0.035,
        "predicted_168h": 15.4,
        "prediction_uncertainty": 1.8,
    }

    agent = AdversarialQAAgent()

    result = await agent.run(state)

    output = result.agent_outputs[
        "adversarial_qa"
    ]

    print("\nAdversarial QA V2:")
    print(output)

    # A structured review should have been produced.
    assert output["review"] is not None

    review = output["review"]

    # Review must challenge the same provisional assessment.
    assert (
        review["challenged_assessment"]
        == "ELEVATED_CONCERN"
    )

    # The LLM should produce at least one challenge.
    assert len(review["challenges"]) > 0

    # Every challenge should contain the structured
    # fields required by the schema.
    for challenge in review["challenges"]:
        assert "challenge_type" in challenge
        assert "direction" in challenge
        assert "summary" in challenge

    # Agent should also produce a Finding.
    adversarial_findings = [
        finding
        for finding in result.findings
        if finding.agent == "adversarial_qa"
    ]

    assert len(adversarial_findings) == 1

    finding = adversarial_findings[0]

    assert (
        finding.finding_type
        == "adversarial_review"
    )


@pytest.mark.asyncio
async def test_adversarial_qa_stops_on_insufficient_evidence():
    state = WorkflowState(
        workflow_id="wf-adversarial-missing",
        component_id="BROKEN-001",
        raw_data={},
    )

    state.agent_outputs["latent_defect"] = {
        "assessment": "INSUFFICIENT_EVIDENCE",
        "signals": [],
    }

    agent = AdversarialQAAgent()

    result = await agent.run(state)

    output = result.agent_outputs[
        "adversarial_qa"
    ]

    print("\nInsufficient evidence:")
    print(output)

    assert output["review"] is None

    assert (
        output["reason"]
        == "insufficient_evidence"
    )

    findings = [
        finding
        for finding in result.findings
        if finding.agent == "adversarial_qa"
    ]

    assert len(findings) == 1

    assert (
        findings[0].finding_type
        == "unable_to_challenge"
    )